# Bash Performance & Optimization

## Overview
Bash performance and optimization covers techniques for writing efficient shell scripts that handle large datasets, execute commands quickly, optimize resource usage, and scale effectively. This includes profiling, benchmarking, parallel processing, and memory management strategies.

## Performance Profiling and Benchmarking

### 1. Script Profiling Framework
```bash
#!/bin/bash

# Performance profiling configuration
PROFILING_ENABLED="${PROFILING_ENABLED:-false}"
PROFILE_OUTPUT_DIR="${PROFILE_OUTPUT_DIR:-./profiles}"
PROFILE_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Initialize profiling
init_profiling() {
    if [[ "$PROFILING_ENABLED" != "true" ]]; then
        return 0
    fi
    
    mkdir -p "$PROFILE_OUTPUT_DIR"
    
    # Global profiling variables
    declare -g PROFILE_START_TIME=$(date +%s.%N)
    declare -g -A FUNCTION_TIMES=()
    declare -g -A FUNCTION_CALLS=()
    declare -g -A COMMAND_TIMES=()
    declare -g PROFILE_LOG="$PROFILE_OUTPUT_DIR/profile_${PROFILE_TIMESTAMP}.log"
    
    # Initialize profile log
    cat > "$PROFILE_LOG" << EOF
Performance Profile Report
==========================
Script: $0
Started: $(date)
PID: $$

EOF
    
    log_info "Performance profiling initialized: $PROFILE_LOG"
}

# Function execution timing
time_function() {
    local func_name="$1"
    shift
    local args=("$@")
    
    if [[ "$PROFILING_ENABLED" != "true" ]]; then
        "$func_name" "${args[@]}"
        return $?
    fi
    
    local start_time=$(date +%s.%N)
    local start_memory=$(get_memory_usage)
    
    # Execute function
    "$func_name" "${args[@]}"
    local exit_code=$?
    
    local end_time=$(date +%s.%N)
    local end_memory=$(get_memory_usage)
    local duration=$(echo "$end_time - $start_time" | bc -l)
    local memory_delta=$((end_memory - start_memory))
    
    # Record timing
    FUNCTION_TIMES["$func_name"]=$(echo "${FUNCTION_TIMES[$func_name]:-0} + $duration" | bc -l)
    FUNCTION_CALLS["$func_name"]=$((${FUNCTION_CALLS[$func_name]:-0} + 1))
    
    # Log to profile
    echo "FUNCTION: $func_name | Duration: ${duration}s | Memory: ${memory_delta}KB | Exit: $exit_code" >> "$PROFILE_LOG"
    
    return $exit_code
}

# Command execution timing
time_command() {
    local description="$1"
    shift
    local command=("$@")
    
    if [[ "$PROFILING_ENABLED" != "true" ]]; then
        "${command[@]}"
        return $?
    fi
    
    local start_time=$(date +%s.%N)
    local start_memory=$(get_memory_usage)
    
    # Execute command
    "${command[@]}"
    local exit_code=$?
    
    local end_time=$(date +%s.%N)
    local end_memory=$(get_memory_usage)
    local duration=$(echo "$end_time - $start_time" | bc -l)
    local memory_delta=$((end_memory - start_memory))
    
    # Record timing
    local cmd_key="${description// /_}"
    COMMAND_TIMES["$cmd_key"]=$(echo "${COMMAND_TIMES[$cmd_key]:-0} + $duration" | bc -l)
    
    # Log to profile
    echo "COMMAND: $description | Duration: ${duration}s | Memory: ${memory_delta}KB | Exit: $exit_code" >> "$PROFILE_LOG"
    
    return $exit_code
}

# Get current memory usage
get_memory_usage() {
    if command -v ps >/dev/null 2>&1; then
        ps -o rss= -p $$ 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Generate performance report
generate_performance_report() {
    if [[ "$PROFILING_ENABLED" != "true" ]]; then
        return 0
    fi
    
    local total_time=$(echo "$(date +%s.%N) - $PROFILE_START_TIME" | bc -l)
    local report_file="$PROFILE_OUTPUT_DIR/report_${PROFILE_TIMESTAMP}.txt"
    
    cat > "$report_file" << EOF
Performance Analysis Report
===========================
Generated: $(date)
Total Execution Time: ${total_time}s

Function Performance:
--------------------
EOF
    
    # Sort functions by total time
    for func in "${!FUNCTION_TIMES[@]}"; do
        local total_time="${FUNCTION_TIMES[$func]}"
        local call_count="${FUNCTION_CALLS[$func]}"
        local avg_time=$(echo "scale=6; $total_time / $call_count" | bc -l)
        echo "$func: ${total_time}s total, ${call_count} calls, ${avg_time}s avg"
    done | sort -k2 -nr >> "$report_file"
    
    echo "" >> "$report_file"
    echo "Command Performance:" >> "$report_file"
    echo "-------------------" >> "$report_file"
    
    # Sort commands by total time
    for cmd in "${!COMMAND_TIMES[@]}"; do
        local total_time="${COMMAND_TIMES[$cmd]}"
        echo "${cmd//_/ }: ${total_time}s"
    done | sort -k2 -nr >> "$report_file"
    
    log_info "Performance report generated: $report_file"
}

# Benchmark function execution
benchmark_function() {
    local func_name="$1"
    local iterations="${2:-10}"
    local warmup_iterations="${3:-3}"
    shift 3
    local args=("$@")
    
    log_info "Benchmarking function: $func_name ($iterations iterations)"
    
    # Warmup runs
    for ((i=1; i<=warmup_iterations; i++)); do
        "$func_name" "${args[@]}" >/dev/null 2>&1
    done
    
    local -a execution_times=()
    local total_time=0
    
    # Benchmark runs
    for ((i=1; i<=iterations; i++)); do
        local start_time=$(date +%s.%N)
        "$func_name" "${args[@]}" >/dev/null 2>&1
        local end_time=$(date +%s.%N)
        
        local duration=$(echo "$end_time - $start_time" | bc -l)
        execution_times+=("$duration")
        total_time=$(echo "$total_time + $duration" | bc -l)
    done
    
    # Calculate statistics
    local avg_time=$(echo "scale=6; $total_time / $iterations" | bc -l)
    
    # Find min and max
    local min_time="${execution_times[0]}"
    local max_time="${execution_times[0]}"
    
    for time in "${execution_times[@]}"; do
        if (( $(echo "$time < $min_time" | bc -l) )); then
            min_time="$time"
        fi
        if (( $(echo "$time > $max_time" | bc -l) )); then
            max_time="$time"
        fi
    done
    
    # Output results
    cat << EOF
Benchmark Results for: $func_name
=================================
Iterations: $iterations
Total Time: ${total_time}s
Average Time: ${avg_time}s
Min Time: ${min_time}s
Max Time: ${max_time}s
EOF
}

# Memory usage profiler
profile_memory_usage() {
    local interval="${1:-5}"
    local duration="${2:-60}"
    local output_file="$PROFILE_OUTPUT_DIR/memory_${PROFILE_TIMESTAMP}.csv"
    
    log_info "Starting memory profiling (${duration}s at ${interval}s intervals)"
    
    echo "timestamp,rss_kb,vms_kb,cpu_percent" > "$output_file"
    
    local end_time=$(($(date +%s) + duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local timestamp=$(date +%s)
        local memory_info
        
        if command -v ps >/dev/null 2>&1; then
            memory_info=$(ps -o rss=,vsz=,pcpu= -p $$ 2>/dev/null | tr -s ' ')
            echo "$timestamp,$memory_info" >> "$output_file"
        fi
        
        sleep "$interval"
    done &
    
    local profiler_pid=$!
    echo "$profiler_pid" > "$PROFILE_OUTPUT_DIR/memory_profiler.pid"
    
    log_info "Memory profiler running in background (PID: $profiler_pid)"
}

# Stop memory profiler
stop_memory_profiler() {
    local profiler_pid_file="$PROFILE_OUTPUT_DIR/memory_profiler.pid"
    
    if [[ -f "$profiler_pid_file" ]]; then
        local profiler_pid
        profiler_pid=$(cat "$profiler_pid_file")
        
        if kill "$profiler_pid" 2>/dev/null; then
            log_info "Memory profiler stopped (PID: $profiler_pid)"
        fi
        
        rm -f "$profiler_pid_file"
    fi
}
```

### 2. Performance Optimization Techniques
```bash
#!/bin/bash

# Efficient string operations
optimize_string_operations() {
    # Use parameter expansion instead of external commands
    
    # SLOW: using sed
    slow_trim() {
        local input="$1"
        echo "$input" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
    }
    
    # FAST: using parameter expansion
    fast_trim() {
        local input="$1"
        input="${input#"${input%%[![:space:]]*}"}"  # Remove leading whitespace
        input="${input%"${input##*[![:space:]]}"}"  # Remove trailing whitespace
        echo "$input"
    }
    
    # SLOW: using cut/awk for substring
    slow_substring() {
        local input="$1"
        local start="$2"
        local length="$3"
        echo "$input" | cut -c"$start"-$((start + length - 1))
    }
    
    # FAST: using parameter expansion
    fast_substring() {
        local input="$1"
        local start="$2"
        local length="$3"
        echo "${input:$((start-1)):$length}"
    }
    
    # SLOW: using grep for pattern matching
    slow_contains() {
        local haystack="$1"
        local needle="$2"
        echo "$haystack" | grep -q "$needle"
    }
    
    # FAST: using parameter expansion
    fast_contains() {
        local haystack="$1"
        local needle="$2"
        [[ "$haystack" == *"$needle"* ]]
    }
    
    # String concatenation optimization
    # SLOW: multiple assignments
    slow_concat() {
        local result=""
        for item in "$@"; do
            result="$result$item"
        done
        echo "$result"
    }
    
    # FAST: printf or array join
    fast_concat() {
        printf '%s' "$@"
    }
    
    # Case conversion optimization
    # SLOW: using tr
    slow_uppercase() {
        echo "$1" | tr '[:lower:]' '[:upper:]'
    }
    
    # FAST: using parameter expansion (Bash 4+)
    fast_uppercase() {
        echo "${1^^}"
    }
}

# Efficient file operations
optimize_file_operations() {
    # Read file line by line efficiently
    # SLOW: using cat and while loop
    slow_process_file() {
        local file="$1"
        cat "$file" | while IFS= read -r line; do
            echo "Processing: $line"
        done
    }
    
    # FAST: direct file descriptor reading
    fast_process_file() {
        local file="$1"
        while IFS= read -r line; do
            echo "Processing: $line"
        done < "$file"
    }
    
    # Count lines efficiently
    # SLOW: using wc -l with cat
    slow_count_lines() {
        local file="$1"
        cat "$file" | wc -l
    }
    
    # FAST: direct wc -l
    fast_count_lines() {
        local file="$1"
        wc -l < "$file"
    }
    
    # File existence check optimization
    # SLOW: using ls
    slow_file_exists() {
        local file="$1"
        ls "$file" >/dev/null 2>&1
    }
    
    # FAST: using test operator
    fast_file_exists() {
        local file="$1"
        [[ -f "$file" ]]
    }
    
    # Large file processing
    process_large_file_efficiently() {
        local file="$1"
        local chunk_size="${2:-1000}"
        
        # Process file in chunks to avoid memory issues
        local line_count=0
        local chunk_count=0
        local temp_chunk=$(mktemp)
        
        while IFS= read -r line; do
            echo "$line" >> "$temp_chunk"
            ((line_count++))
            
            if [[ $line_count -eq $chunk_size ]]; then
                ((chunk_count++))
                log_info "Processing chunk $chunk_count ($line_count lines)"
                
                # Process chunk
                process_chunk "$temp_chunk" "$chunk_count"
                
                # Reset for next chunk
                > "$temp_chunk"
                line_count=0
            fi
        done < "$file"
        
        # Process remaining lines
        if [[ $line_count -gt 0 ]]; then
            ((chunk_count++))
            log_info "Processing final chunk $chunk_count ($line_count lines)"
            process_chunk "$temp_chunk" "$chunk_count"
        fi
        
        rm -f "$temp_chunk"
    }
    
    # Chunk processing function
    process_chunk() {
        local chunk_file="$1"
        local chunk_number="$2"
        
        # Example processing - replace with actual logic
        local processed=0
        while IFS= read -r line; do
            # Process line here
            ((processed++))
        done < "$chunk_file"
        
        log_debug "Chunk $chunk_number: processed $processed lines"
    }
}

# Memory optimization techniques
optimize_memory_usage() {
    # Use local variables to prevent memory leaks
    memory_efficient_function() {
        local large_array=()
        local temp_var=""
        
        # Process data
        for i in {1..1000}; do
            large_array+=("data_$i")
        done
        
        # Process array
        for item in "${large_array[@]}"; do
            temp_var="processed_$item"
            echo "$temp_var"
        done
        
        # Variables are automatically cleaned up when function exits
    }
    
    # Avoid global variables for large data
    # BAD: Global array
    declare -g GLOBAL_LARGE_ARRAY=()
    
    # GOOD: Pass arrays as parameters
    process_array_efficiently() {
        local -n array_ref=$1  # Use nameref to avoid copying
        
        for item in "${array_ref[@]}"; do
            echo "Processing: $item"
        done
    }
    
    # Stream processing instead of loading entire files
    stream_process_log() {
        local log_file="$1"
        local pattern="$2"
        
        # Instead of: grep "$pattern" "$log_file" | while read line
        # Use direct streaming:
        while IFS= read -r line; do
            if [[ "$line" =~ $pattern ]]; then
                echo "$line"
            fi
        done < "$log_file"
    }
    
    # Efficient temporary file handling
    create_temp_file_efficiently() {
        local temp_file
        temp_file=$(mktemp) || return 1
        
        # Register for cleanup
        trap "rm -f '$temp_file'" EXIT
        
        echo "$temp_file"
    }
    
    # Clear arrays when done
    cleanup_arrays() {
        local -n array_ref=$1
        array_ref=()  # Clear array
        unset array_ref  # Remove array entirely
    }
}

# Command execution optimization
optimize_command_execution() {
    # Minimize external command calls
    # SLOW: Multiple external commands
    slow_process() {
        local file="$1"
        local count
        count=$(wc -l < "$file")
        local size
        size=$(wc -c < "$file")
        local words
        words=$(wc -w < "$file")
        
        echo "Lines: $count, Size: $size, Words: $words"
    }
    
    # FAST: Single command with multiple options
    fast_process() {
        local file="$1"
        local stats
        stats=$(wc -lwc < "$file")
        echo "Lines: $(echo $stats | cut -d' ' -f1), Words: $(echo $stats | cut -d' ' -f2), Size: $(echo $stats | cut -d' ' -f3)"
    }
    
    # Batch operations
    batch_file_operations() {
        local -a files=("$@")
        local temp_list=$(mktemp)
        
        # Create list of files for batch processing
        printf '%s\n' "${files[@]}" > "$temp_list"
        
        # Batch operations
        xargs -a "$temp_list" ls -la
        xargs -a "$temp_list" wc -l
        
        rm -f "$temp_list"
    }
    
    # Use command substitution efficiently
    # SLOW: Multiple command substitutions
    slow_get_system_info() {
        local hostname
        hostname=$(hostname)
        local uptime
        uptime=$(uptime | cut -d',' -f1)
        local users
        users=$(who | wc -l)
        
        echo "Host: $hostname, Uptime: $uptime, Users: $users"
    }
    
    # FAST: Combined command substitution
    fast_get_system_info() {
        local system_info
        system_info=$(
            hostname
            uptime | cut -d',' -f1
            who | wc -l
        )
        
        local -a info_array=($system_info)
        echo "Host: ${info_array[0]}, Uptime: ${info_array[1]}, Users: ${info_array[2]}"
    }
    
    # Avoid subshells in loops
    # SLOW: Creates subshell for each iteration
    slow_process_list() {
        local -a items=("$@")
        local total=0
        
        for item in "${items[@]}"; do
            total=$((total + $(echo "$item" | wc -c)))  # Creates subshell
        done
        
        echo "$total"
    }
    
    # FAST: Avoid subshells
    fast_process_list() {
        local -a items=("$@")
        local total=0
        
        for item in "${items[@]}"; do
            total=$((total + ${#item}))  # No subshell
        done
        
        echo "$total"
    }
}
```

## Parallel Processing and Concurrency

### 1. Parallel Execution Framework
```bash
#!/bin/bash

# Parallel job execution
execute_parallel_jobs() {
    local max_jobs="${1:-4}"
    shift
    local jobs=("$@")
    
    local active_jobs=0
    local job_index=0
    local total_jobs=${#jobs[@]}
    local -a job_pids=()
    local -a job_results=()
    
    log_info "Starting parallel execution: $total_jobs jobs, max concurrent: $max_jobs"
    
    while [[ $job_index -lt $total_jobs ]] || [[ $active_jobs -gt 0 ]]; do
        # Start new jobs if under limit and jobs available
        while [[ $active_jobs -lt $max_jobs && $job_index -lt $total_jobs ]]; do
            local job="${jobs[$job_index]}"
            
            log_debug "Starting job $((job_index + 1))/$total_jobs: $job"
            
            # Execute job in background
            (
                eval "$job"
                echo $? > "/tmp/job_${job_index}_$$"
            ) &
            
            local job_pid=$!
            job_pids[$job_index]=$job_pid
            
            ((active_jobs++))
            ((job_index++))
        done
        
        # Check for completed jobs
        for i in "${!job_pids[@]}"; do
            local pid="${job_pids[$i]}"
            
            if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
                # Job completed
                wait "$pid"
                local job_result=0
                
                # Get job result
                if [[ -f "/tmp/job_${i}_$$" ]]; then
                    job_result=$(cat "/tmp/job_${i}_$$")
                    rm -f "/tmp/job_${i}_$$"
                fi
                
                job_results[$i]=$job_result
                job_pids[$i]=""
                ((active_jobs--))
                
                if [[ $job_result -eq 0 ]]; then
                    log_debug "Job $((i + 1)) completed successfully"
                else
                    log_warn "Job $((i + 1)) failed with exit code: $job_result"
                fi
            fi
        done
        
        # Small delay to prevent busy waiting
        sleep 0.1
    done
    
    # Check overall results
    local failed_jobs=0
    for result in "${job_results[@]}"; do
        if [[ $result -ne 0 ]]; then
            ((failed_jobs++))
        fi
    done
    
    if [[ $failed_jobs -eq 0 ]]; then
        log_info "All $total_jobs parallel jobs completed successfully"
        return 0
    else
        log_error "$failed_jobs out of $total_jobs jobs failed"
        return 1
    fi
}

# Parallel file processing
process_files_parallel() {
    local max_workers="${1:-4}"
    local processor_function="$2"
    shift 2
    local files=("$@")
    
    local total_files=${#files[@]}
    log_info "Processing $total_files files with $max_workers workers"
    
    # Create job list
    local -a jobs=()
    for file in "${files[@]}"; do
        jobs+=("$processor_function '$file'")
    done
    
    # Execute in parallel
    execute_parallel_jobs "$max_workers" "${jobs[@]}"
}

# Producer-consumer pattern
producer_consumer_pipeline() {
    local producer_command="$1"
    local consumer_command="$2"
    local buffer_size="${3:-100}"
    
    local fifo
    fifo=$(mktemp -u)
    mkfifo "$fifo"
    
    # Register cleanup
    trap "rm -f '$fifo'" EXIT
    
    log_info "Starting producer-consumer pipeline"
    
    # Start consumer
    (
        while IFS= read -r item; do
            eval "$consumer_command '$item'"
        done < "$fifo"
    ) &
    local consumer_pid=$!
    
    # Start producer
    (
        eval "$producer_command" > "$fifo"
    ) &
    local producer_pid=$!
    
    # Wait for both processes
    wait "$producer_pid"
    local producer_exit=$?
    
    # Close FIFO to signal consumer
    exec {fifo_fd}>"$fifo"
    exec {fifo_fd}>&-
    
    wait "$consumer_pid"
    local consumer_exit=$?
    
    rm -f "$fifo"
    
    if [[ $producer_exit -eq 0 && $consumer_exit -eq 0 ]]; then
        log_info "Producer-consumer pipeline completed successfully"
        return 0
    else
        log_error "Pipeline failed: producer=$producer_exit, consumer=$consumer_exit"
        return 1
    fi
}

# Map-reduce pattern
map_reduce_process() {
    local mapper_function="$1"
    local reducer_function="$2"
    local max_mappers="${3:-4}"
    shift 3
    local input_data=("$@")
    
    log_info "Starting map-reduce: ${#input_data[@]} items, $max_mappers mappers"
    
    # Create temporary directory for intermediate results
    local temp_dir
    temp_dir=$(mktemp -d)
    trap "rm -rf '$temp_dir'" EXIT
    
    # Map phase: Process data in parallel
    local -a map_jobs=()
    local chunk_size=$(( (${#input_data[@]} + max_mappers - 1) / max_mappers ))
    
    for ((i=0; i<${#input_data[@]}; i+=chunk_size)); do
        local chunk=("${input_data[@]:i:chunk_size}")
        local chunk_id=$((i / chunk_size))
        local output_file="$temp_dir/map_output_$chunk_id"
        
        map_jobs+=("process_chunk '$mapper_function' '$output_file' '${chunk[*]}'")
    done
    
    # Execute map jobs
    if ! execute_parallel_jobs "$max_mappers" "${map_jobs[@]}"; then
        log_error "Map phase failed"
        return 1
    fi
    
    # Reduce phase: Combine results
    log_info "Starting reduce phase"
    local final_output="$temp_dir/final_output"
    
    # Collect all map outputs
    local -a map_outputs=()
    for output_file in "$temp_dir"/map_output_*; do
        if [[ -f "$output_file" ]]; then
            map_outputs+=("$output_file")
        fi
    done
    
    # Apply reducer
    eval "$reducer_function" "${map_outputs[@]}" > "$final_output"
    
    # Output final result
    cat "$final_output"
    
    log_info "Map-reduce completed successfully"
}

# Helper function for map-reduce
process_chunk() {
    local mapper_function="$1"
    local output_file="$2"
    shift 2
    local chunk_data=("$@")
    
    {
        for item in "${chunk_data[@]}"; do
            eval "$mapper_function '$item'"
        done
    } > "$output_file"
}

# Concurrent resource pool
manage_resource_pool() {
    local pool_name="$1"
    local max_resources="${2:-5}"
    local resource_command="$3"
    
    local pool_dir="/tmp/resource_pool_$pool_name"
    mkdir -p "$pool_dir"
    
    # Initialize resource semaphore
    local semaphore_file="$pool_dir/semaphore"
    echo "$max_resources" > "$semaphore_file"
    
    # Acquire resource
    acquire_resource() {
        local timeout="${1:-30}"
        local waited=0
        
        while [[ $waited -lt $timeout ]]; do
            (
                flock -x 200
                local available
                available=$(cat "$semaphore_file")
                
                if [[ $available -gt 0 ]]; then
                    echo $((available - 1)) > "$semaphore_file"
                    echo "acquired"
                    exit 0
                else
                    echo "busy"
                    exit 1
                fi
            ) 200>"$pool_dir/lock"
            
            local result=$?
            if [[ $result -eq 0 ]]; then
                return 0
            fi
            
            sleep 1
            ((waited++))
        done
        
        log_error "Timeout acquiring resource from pool: $pool_name"
        return 1
    }
    
    # Release resource
    release_resource() {
        (
            flock -x 200
            local available
            available=$(cat "$semaphore_file")
            echo $((available + 1)) > "$semaphore_file"
        ) 200>"$pool_dir/lock"
    }
    
    # Execute with resource management
    if acquire_resource; then
        log_debug "Acquired resource from pool: $pool_name"
        
        # Execute command
        eval "$resource_command"
        local exit_code=$?
        
        # Release resource
        release_resource
        log_debug "Released resource to pool: $pool_name"
        
        return $exit_code
    else
        return 1
    fi
}
```

### 2. Background Processing and Job Control
```bash
#!/bin/bash

# Background job manager
declare -g -A BACKGROUND_JOBS=()
declare -g JOB_COUNTER=0

# Start background job
start_background_job() {
    local job_name="$1"
    local job_command="$2"
    local log_file="${3:-/dev/null}"
    
    ((JOB_COUNTER++))
    local job_id="job_${JOB_COUNTER}"
    
    log_info "Starting background job: $job_name (ID: $job_id)"
    
    # Start job in background with logging
    (
        exec > "$log_file" 2>&1
        eval "$job_command"
        echo $? > "/tmp/${job_id}_exit_code"
    ) &
    
    local job_pid=$!
    
    # Store job information
    BACKGROUND_JOBS["$job_id"]="$job_pid|$job_name|$job_command|$log_file|$(date +%s)"
    
    echo "$job_id"
}

# Check job status
check_job_status() {
    local job_id="$1"
    
    if [[ -z "${BACKGROUND_JOBS[$job_id]:-}" ]]; then
        echo "unknown"
        return 1
    fi
    
    local job_info="${BACKGROUND_JOBS[$job_id]}"
    IFS='|' read -r job_pid job_name job_command log_file start_time <<< "$job_info"
    
    if kill -0 "$job_pid" 2>/dev/null; then
        echo "running"
        return 0
    else
        # Job completed - check exit code
        local exit_code_file="/tmp/${job_id}_exit_code"
        if [[ -f "$exit_code_file" ]]; then
            local exit_code
            exit_code=$(cat "$exit_code_file")
            rm -f "$exit_code_file"
            
            if [[ $exit_code -eq 0 ]]; then
                echo "completed"
            else
                echo "failed"
            fi
        else
            echo "terminated"
        fi
        
        # Remove from active jobs
        unset BACKGROUND_JOBS["$job_id"]
        return 0
    fi
}

# Wait for job completion
wait_for_job() {
    local job_id="$1"
    local timeout="${2:-0}"  # 0 = no timeout
    
    if [[ -z "${BACKGROUND_JOBS[$job_id]:-}" ]]; then
        log_error "Job not found: $job_id"
        return 1
    fi
    
    local job_info="${BACKGROUND_JOBS[$job_id]}"
    IFS='|' read -r job_pid job_name job_command log_file start_time <<< "$job_info"
    
    log_info "Waiting for job: $job_name (ID: $job_id)"
    
    if [[ $timeout -gt 0 ]]; then
        # Wait with timeout
        local waited=0
        while [[ $waited -lt $timeout ]]; do
            if ! kill -0 "$job_pid" 2>/dev/null; then
                break
            fi
            sleep 1
            ((waited++))
        done
        
        # Check if still running after timeout
        if kill -0 "$job_pid" 2>/dev/null; then
            log_warn "Job timeout reached: $job_name"
            return 124  # Timeout exit code
        fi
    else
        # Wait indefinitely
        wait "$job_pid"
    fi
    
    # Get final status
    local final_status
    final_status=$(check_job_status "$job_id")
    
    case "$final_status" in
        completed)
            log_info "Job completed successfully: $job_name"
            return 0
            ;;
        failed)
            log_error "Job failed: $job_name"
            return 1
            ;;
        *)
            log_error "Job terminated unexpectedly: $job_name"
            return 1
            ;;
    esac
}

# Kill background job
kill_background_job() {
    local job_id="$1"
    local signal="${2:-TERM}"
    
    if [[ -z "${BACKGROUND_JOBS[$job_id]:-}" ]]; then
        log_error "Job not found: $job_id"
        return 1
    fi
    
    local job_info="${BACKGROUND_JOBS[$job_id]}"
    IFS='|' read -r job_pid job_name job_command log_file start_time <<< "$job_info"
    
    if kill -0 "$job_pid" 2>/dev/null; then
        log_info "Killing job: $job_name (PID: $job_pid, Signal: $signal)"
        
        if kill -"$signal" "$job_pid" 2>/dev/null; then
            sleep 2
            
            # Check if process is still running
            if kill -0 "$job_pid" 2>/dev/null; then
                log_warn "Job didn't respond to $signal, sending KILL"
                kill -KILL "$job_pid" 2>/dev/null
            fi
            
            # Clean up
            unset BACKGROUND_JOBS["$job_id"]
            rm -f "/tmp/${job_id}_exit_code"
            
            log_info "Job killed successfully: $job_name"
            return 0
        else
            log_error "Failed to kill job: $job_name"
            return 1
        fi
    else
        log_warn "Job already terminated: $job_name"
        unset BACKGROUND_JOBS["$job_id"]
        return 0
    fi
}

# List all background jobs
list_background_jobs() {
    if [[ ${#BACKGROUND_JOBS[@]} -eq 0 ]]; then
        echo "No background jobs running"
        return 0
    fi
    
    printf "%-10s %-8s %-12s %-10s %-20s %s\n" "JOB_ID" "PID" "STATUS" "RUNTIME" "NAME" "COMMAND"
    printf "%s\n" "$(printf '=%.0s' {1..80})"
    
    for job_id in "${!BACKGROUND_JOBS[@]}"; do
        local job_info="${BACKGROUND_JOBS[$job_id]}"
        IFS='|' read -r job_pid job_name job_command log_file start_time <<< "$job_info"
        
        local status
        status=$(check_job_status "$job_id")
        
        local runtime=$(($(date +%s) - start_time))
        local runtime_formatted="${runtime}s"
        if [[ $runtime -gt 3600 ]]; then
            runtime_formatted="$((runtime / 3600))h$(((runtime % 3600) / 60))m"
        elif [[ $runtime -gt 60 ]]; then
            runtime_formatted="$((runtime / 60))m$((runtime % 60))s"
        fi
        
        printf "%-10s %-8s %-12s %-10s %-20s %s\n" \
            "$job_id" "$job_pid" "$status" "$runtime_formatted" \
            "${job_name:0:20}" "${job_command:0:40}"
    done
}

# Clean up completed jobs
cleanup_completed_jobs() {
    local cleaned=0
    
    for job_id in "${!BACKGROUND_JOBS[@]}"; do
        local status
        status=$(check_job_status "$job_id")
        
        if [[ "$status" != "running" ]]; then
            unset BACKGROUND_JOBS["$job_id"]
            rm -f "/tmp/${job_id}_exit_code"
            ((cleaned++))
        fi
    done
    
    log_info "Cleaned up $cleaned completed background jobs"
}

# Job scheduler
schedule_jobs() {
    local -a job_queue=("$@")
    local max_concurrent="${MAX_CONCURRENT_JOBS:-3}"
    
    log_info "Scheduling ${#job_queue[@]} jobs (max concurrent: $max_concurrent)"
    
    local job_index=0
    local -a active_job_ids=()
    
    while [[ $job_index -lt ${#job_queue[@]} ]] || [[ ${#active_job_ids[@]} -gt 0 ]]; do
        # Start new jobs if under limit
        while [[ ${#active_job_ids[@]} -lt $max_concurrent && $job_index -lt ${#job_queue[@]} ]]; do
            local job_spec="${job_queue[$job_index]}"
            IFS='|' read -r job_name job_command <<< "$job_spec"
            
            local job_id
            job_id=$(start_background_job "$job_name" "$job_command")
            active_job_ids+=("$job_id")
            
            ((job_index++))
        done
        
        # Check for completed jobs
        local -a remaining_jobs=()
        for job_id in "${active_job_ids[@]}"; do
            local status
            status=$(check_job_status "$job_id")
            
            if [[ "$status" == "running" ]]; then
                remaining_jobs+=("$job_id")
            else
                log_info "Job completed: $job_id ($status)"
            fi
        done
        
        active_job_ids=("${remaining_jobs[@]}")
        
        sleep 1
    done
    
    log_info "All scheduled jobs completed"
}
```

This comprehensive performance and optimization framework provides tools for profiling, benchmarking, parallel processing, and efficient resource utilization in Bash scripts for DevOps environments.