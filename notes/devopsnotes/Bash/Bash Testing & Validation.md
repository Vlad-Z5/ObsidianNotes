# Bash Testing & Validation

## Overview
Bash testing and validation covers comprehensive testing frameworks, unit testing approaches, integration testing strategies, test automation, and validation techniques for ensuring shell scripts are reliable, maintainable, and production-ready.

## Unit Testing Framework

### 1. Bash Unit Testing Framework (BATS-style)
```bash
#!/bin/bash

# Testing framework configuration
readonly TEST_DIR="${TEST_DIR:-./tests}"
readonly TEST_OUTPUT_DIR="${TEST_OUTPUT_DIR:-./test-results}"
readonly TEST_TIMEOUT="${TEST_TIMEOUT:-30}"

# Test framework globals
declare -g TEST_SUITE_NAME=""
declare -g TEST_CASE_NAME=""
declare -g TOTAL_TESTS=0
declare -g PASSED_TESTS=0
declare -g FAILED_TESTS=0
declare -g SKIPPED_TESTS=0
declare -g -a TEST_RESULTS=()

# Initialize test framework
init_test_framework() {
    local suite_name="$1"
    
    TEST_SUITE_NAME="$suite_name"
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    SKIPPED_TESTS=0
    TEST_RESULTS=()
    
    mkdir -p "$TEST_OUTPUT_DIR"
    
    log_info "Initializing test suite: $suite_name"
}

# Test assertion functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-Assertion failed}"
    
    if [[ "$actual" == "$expected" ]]; then
        return 0
    else
        log_error "$message: expected '$expected', got '$actual'"
        return 1
    fi
}

assert_not_equals() {
    local not_expected="$1"
    local actual="$2"
    local message="${3:-Assertion failed}"
    
    if [[ "$actual" != "$not_expected" ]]; then
        return 0
    else
        log_error "$message: expected not '$not_expected', but got '$actual'"
        return 1
    fi
}

assert_true() {
    local condition="$1"
    local message="${2:-Assertion failed}"
    
    if eval "$condition"; then
        return 0
    else
        log_error "$message: condition '$condition' is not true"
        return 1
    fi
}

assert_false() {
    local condition="$1"
    local message="${2:-Assertion failed}"
    
    if ! eval "$condition"; then
        return 0
    else
        log_error "$message: condition '$condition' is not false"
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-Assertion failed}"
    
    if [[ "$haystack" == *"$needle"* ]]; then
        return 0
    else
        log_error "$message: '$haystack' does not contain '$needle'"
        return 1
    fi
}

assert_file_exists() {
    local file_path="$1"
    local message="${2:-File does not exist}"
    
    if [[ -f "$file_path" ]]; then
        return 0
    else
        log_error "$message: $file_path"
        return 1
    fi
}

assert_directory_exists() {
    local dir_path="$1"
    local message="${2:-Directory does not exist}"
    
    if [[ -d "$dir_path" ]]; then
        return 0
    else
        log_error "$message: $dir_path"
        return 1
    fi
}

assert_command_succeeds() {
    local command="$1"
    local message="${2:-Command failed}"
    
    if eval "$command" >/dev/null 2>&1; then
        return 0
    else
        log_error "$message: $command"
        return 1
    fi
}

assert_command_fails() {
    local command="$1"
    local message="${2:-Command unexpectedly succeeded}"
    
    if ! eval "$command" >/dev/null 2>&1; then
        return 0
    else
        log_error "$message: $command"
        return 1
    fi
}

assert_exit_code() {
    local expected_code="$1"
    local command="$2"
    local message="${3:-Exit code mismatch}"
    
    eval "$command" >/dev/null 2>&1
    local actual_code=$?
    
    if [[ $actual_code -eq $expected_code ]]; then
        return 0
    else
        log_error "$message: expected exit code $expected_code, got $actual_code"
        return 1
    fi
}

# Test execution framework
run_test() {
    local test_name="$1"
    local test_function="$2"
    local setup_function="${3:-}"
    local teardown_function="${4:-}"
    
    TEST_CASE_NAME="$test_name"
    ((TOTAL_TESTS++))
    
    log_info "Running test: $test_name"
    
    # Create test isolation
    local test_start_time=$(date +%s.%N)
    local test_temp_dir
    test_temp_dir=$(mktemp -d -t "test_${test_name}_XXXXXX")
    local original_pwd="$PWD"
    
    # Setup test environment
    cd "$test_temp_dir" || {
        log_error "Failed to create test environment"
        ((FAILED_TESTS++))
        return 1
    }
    
    # Run setup if provided
    if [[ -n "$setup_function" ]] && command -v "$setup_function" >/dev/null 2>&1; then
        if ! "$setup_function"; then
            log_error "Test setup failed: $test_name"
            cd "$original_pwd"
            rm -rf "$test_temp_dir"
            ((FAILED_TESTS++))
            return 1
        fi
    fi
    
    # Run the actual test with timeout
    local test_result=0
    
    if timeout "$TEST_TIMEOUT" bash -c "$test_function"; then
        local test_end_time=$(date +%s.%N)
        local test_duration=$(echo "$test_end_time - $test_start_time" | bc -l)
        
        log_success "Test passed: $test_name (${test_duration}s)"
        ((PASSED_TESTS++))
        
        TEST_RESULTS+=("PASS|$test_name|$test_duration|")
    else
        test_result=$?
        local test_end_time=$(date +%s.%N)
        local test_duration=$(echo "$test_end_time - $test_start_time" | bc -l)
        
        if [[ $test_result -eq 124 ]]; then
            log_error "Test timed out: $test_name (${TEST_TIMEOUT}s)"
            TEST_RESULTS+=("TIMEOUT|$test_name|$test_duration|Test timed out")
        else
            log_error "Test failed: $test_name"
            TEST_RESULTS+=("FAIL|$test_name|$test_duration|Test failed with exit code $test_result")
        fi
        
        ((FAILED_TESTS++))
    fi
    
    # Run teardown if provided
    if [[ -n "$teardown_function" ]] && command -v "$teardown_function" >/dev/null 2>&1; then
        "$teardown_function" || log_warn "Test teardown failed: $test_name"
    fi
    
    # Cleanup
    cd "$original_pwd"
    rm -rf "$test_temp_dir"
    
    return $test_result
}

# Skip test function
skip_test() {
    local test_name="$1"
    local reason="${2:-Test skipped}"
    
    TEST_CASE_NAME="$test_name"
    ((TOTAL_TESTS++))
    ((SKIPPED_TESTS++))
    
    log_warn "Skipping test: $test_name - $reason"
    TEST_RESULTS+=("SKIP|$test_name|0|$reason")
}

# Test suite execution
run_test_suite() {
    local test_file="$1"
    
    if [[ ! -f "$test_file" ]]; then
        log_error "Test file not found: $test_file"
        return 1
    fi
    
    log_info "Running test suite from: $test_file"
    
    # Source the test file
    if ! source "$test_file"; then
        log_error "Failed to source test file: $test_file"
        return 1
    fi
    
    # Generate test report
    generate_test_report
    
    # Return appropriate exit code
    if [[ $FAILED_TESTS -gt 0 ]]; then
        return 1
    else
        return 0
    fi
}

# Generate test report
generate_test_report() {
    local report_file="$TEST_OUTPUT_DIR/test_report_$(date +%Y%m%d_%H%M%S).txt"
    local junit_file="$TEST_OUTPUT_DIR/junit_report_$(date +%Y%m%d_%H%M%S).xml"
    
    # Text report
    cat > "$report_file" << EOF
Test Suite Report: $TEST_SUITE_NAME
==================================
Generated: $(date)

Summary:
--------
Total Tests: $TOTAL_TESTS
Passed: $PASSED_TESTS
Failed: $FAILED_TESTS
Skipped: $SKIPPED_TESTS
Success Rate: $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l)%

Test Results:
-------------
EOF
    
    # Add individual test results
    for result in "${TEST_RESULTS[@]}"; do
        IFS='|' read -r status name duration message <<< "$result"
        printf "%-8s %-30s %8ss %s\n" "$status" "$name" "$duration" "$message" >> "$report_file"
    done
    
    # JUnit XML report
    generate_junit_report "$junit_file"
    
    log_info "Test reports generated:"
    log_info "  Text report: $report_file"
    log_info "  JUnit XML: $junit_file"
    
    # Display summary
    echo
    echo "Test Suite: $TEST_SUITE_NAME"
    echo "=========================================="
    echo "Total: $TOTAL_TESTS | Passed: $PASSED_TESTS | Failed: $FAILED_TESTS | Skipped: $SKIPPED_TESTS"
    
    if [[ $FAILED_TESTS -gt 0 ]]; then
        echo "❌ Test suite FAILED"
    else
        echo "✅ Test suite PASSED"
    fi
}

# Generate JUnit XML report
generate_junit_report() {
    local junit_file="$1"
    
    cat > "$junit_file" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="$TEST_SUITE_NAME" tests="$TOTAL_TESTS" failures="$FAILED_TESTS" skipped="$SKIPPED_TESTS" time="$(date +%s)">
EOF
    
    for result in "${TEST_RESULTS[@]}"; do
        IFS='|' read -r status name duration message <<< "$result"
        
        echo "  <testcase name=\"$name\" classname=\"$TEST_SUITE_NAME\" time=\"$duration\">" >> "$junit_file"
        
        case "$status" in
            FAIL|TIMEOUT)
                echo "    <failure message=\"$message\">$message</failure>" >> "$junit_file"
                ;;
            SKIP)
                echo "    <skipped message=\"$message\">$message</skipped>" >> "$junit_file"
                ;;
        esac
        
        echo "  </testcase>" >> "$junit_file"
    done
    
    echo "</testsuite>" >> "$junit_file"
}
```

### 2. Mock and Stub Framework
```bash
#!/bin/bash

# Mock framework for testing
declare -g -A MOCKED_COMMANDS=()
declare -g -A MOCK_CALL_COUNTS=()
declare -g -A MOCK_CALL_ARGS=()

# Mock a command
mock_command() {
    local command="$1"
    local mock_output="${2:-}"
    local mock_exit_code="${3:-0}"
    
    # Create mock function
    eval "
    $command() {
        local args=\"\$*\"
        
        # Track mock calls
        MOCK_CALL_COUNTS['$command']=\$((MOCK_CALL_COUNTS['$command'] + 1))
        MOCK_CALL_ARGS['$command']+=\"\$args|\"
        
        # Output mock response
        if [[ -n '$mock_output' ]]; then
            echo '$mock_output'
        fi
        
        return $mock_exit_code
    }
    "
    
    MOCKED_COMMANDS["$command"]="$mock_output|$mock_exit_code"
    MOCK_CALL_COUNTS["$command"]=0
    MOCK_CALL_ARGS["$command"]=""
    
    log_debug "Mocked command: $command"
}

# Verify mock was called
assert_mock_called() {
    local command="$1"
    local expected_times="${2:-1}"
    local message="${3:-Mock not called expected number of times}"
    
    local actual_calls="${MOCK_CALL_COUNTS[$command]:-0}"
    
    if [[ $actual_calls -eq $expected_times ]]; then
        return 0
    else
        log_error "$message: expected $expected_times calls, got $actual_calls"
        return 1
    fi
}

# Verify mock was called with specific arguments
assert_mock_called_with() {
    local command="$1"
    local expected_args="$2"
    local message="${3:-Mock not called with expected arguments}"
    
    local all_args="${MOCK_CALL_ARGS[$command]:-}"
    
    if [[ "$all_args" == *"$expected_args|"* ]]; then
        return 0
    else
        log_error "$message: expected '$expected_args' in '$all_args'"
        return 1
    fi
}

# Reset all mocks
reset_mocks() {
    for command in "${!MOCKED_COMMANDS[@]}"; do
        unset -f "$command"
        unset MOCKED_COMMANDS["$command"]
        unset MOCK_CALL_COUNTS["$command"]
        unset MOCK_CALL_ARGS["$command"]
    done
    
    log_debug "All mocks reset"
}

# Create test doubles (stubs)
create_stub_file() {
    local file_path="$1"
    local content="$2"
    local permissions="${3:-644}"
    
    mkdir -p "$(dirname "$file_path")"
    echo "$content" > "$file_path"
    chmod "$permissions" "$file_path"
    
    log_debug "Created stub file: $file_path"
}

# Create stub directory
create_stub_directory() {
    local dir_path="$1"
    local permissions="${2:-755}"
    
    mkdir -p "$dir_path"
    chmod "$permissions" "$dir_path"
    
    log_debug "Created stub directory: $dir_path"
}

# Environment variable stubbing
stub_env_var() {
    local var_name="$1"
    local var_value="$2"
    
    # Store original value if it exists
    if [[ -n "${!var_name:-}" ]]; then
        eval "ORIGINAL_$var_name=\"\${$var_name}\""
    fi
    
    export "$var_name"="$var_value"
    
    log_debug "Stubbed environment variable: $var_name=$var_value"
}

# Restore environment variable
restore_env_var() {
    local var_name="$1"
    
    local original_var="ORIGINAL_$var_name"
    
    if [[ -n "${!original_var:-}" ]]; then
        export "$var_name"="${!original_var}"
        unset "$original_var"
    else
        unset "$var_name"
    fi
    
    log_debug "Restored environment variable: $var_name"
}
```

## Integration Testing Framework

### 1. Service Integration Testing
```bash
#!/bin/bash

# Integration test framework
integration_test_setup() {
    local test_name="$1"
    
    log_info "Setting up integration test environment: $test_name"
    
    # Create isolated test environment
    export TEST_ENV_DIR
    TEST_ENV_DIR=$(mktemp -d -t "integration_test_${test_name}_XXXXXX")
    
    # Setup test database
    setup_test_database
    
    # Setup test services
    setup_test_services
    
    # Wait for services to be ready
    wait_for_test_services
    
    log_info "Integration test environment ready"
}

# Setup test database
setup_test_database() {
    local db_container="test_db_$$"
    
    log_info "Starting test database container"
    
    # Start PostgreSQL test container
    if docker run -d \
        --name "$db_container" \
        -e POSTGRES_PASSWORD=testpass \
        -e POSTGRES_DB=testdb \
        -p 0:5432 \
        postgres:13-alpine; then
        
        # Get mapped port
        local db_port
        db_port=$(docker port "$db_container" 5432/tcp | cut -d: -f2)
        
        export TEST_DB_HOST="localhost"
        export TEST_DB_PORT="$db_port"
        export TEST_DB_NAME="testdb"
        export TEST_DB_USER="postgres"
        export TEST_DB_PASSWORD="testpass"
        
        # Wait for database to be ready
        local max_wait=30
        local waited=0
        
        while [[ $waited -lt $max_wait ]]; do
            if pg_isready -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" >/dev/null 2>&1; then
                log_success "Test database is ready"
                break
            fi
            
            sleep 2
            waited=$((waited + 2))
        done
        
        if [[ $waited -ge $max_wait ]]; then
            log_error "Test database failed to start"
            return 1
        fi
        
        # Store container name for cleanup
        echo "$db_container" > "$TEST_ENV_DIR/db_container"
        
    else
        log_error "Failed to start test database"
        return 1
    fi
}

# Setup test services
setup_test_services() {
    log_info "Starting test services"
    
    # Start Redis cache
    local redis_container="test_redis_$$"
    
    if docker run -d \
        --name "$redis_container" \
        -p 0:6379 \
        redis:6-alpine; then
        
        local redis_port
        redis_port=$(docker port "$redis_container" 6379/tcp | cut -d: -f2)
        
        export TEST_REDIS_HOST="localhost"
        export TEST_REDIS_PORT="$redis_port"
        
        echo "$redis_container" > "$TEST_ENV_DIR/redis_container"
        
        log_success "Test Redis started on port $redis_port"
    else
        log_warn "Failed to start test Redis (non-critical)"
    fi
    
    # Start application service
    start_test_application
}

# Start test application
start_test_application() {
    local app_port="${TEST_APP_PORT:-8080}"
    
    log_info "Starting test application on port $app_port"
    
    # Build test application image
    if [[ -f "Dockerfile.test" ]]; then
        local app_image="test_app_$$"
        
        if docker build -f Dockerfile.test -t "$app_image" .; then
            log_success "Test application image built"
        else
            log_error "Failed to build test application image"
            return 1
        fi
        
        # Start application container
        local app_container="test_app_$$"
        
        if docker run -d \
            --name "$app_container" \
            -p "$app_port:8080" \
            -e DATABASE_URL="postgresql://$TEST_DB_USER:$TEST_DB_PASSWORD@host.docker.internal:$TEST_DB_PORT/$TEST_DB_NAME" \
            -e REDIS_URL="redis://host.docker.internal:$TEST_REDIS_PORT" \
            "$app_image"; then
            
            export TEST_APP_HOST="localhost"
            export TEST_APP_PORT="$app_port"
            
            echo "$app_container" > "$TEST_ENV_DIR/app_container"
            log_success "Test application started"
        else
            log_error "Failed to start test application"
            return 1
        fi
    else
        log_warn "No Dockerfile.test found, skipping application container"
    fi
}

# Wait for test services
wait_for_test_services() {
    log_info "Waiting for test services to be ready"
    
    # Wait for application health check
    if [[ -n "${TEST_APP_HOST:-}" && -n "${TEST_APP_PORT:-}" ]]; then
        local app_url="http://$TEST_APP_HOST:$TEST_APP_PORT"
        local max_wait=60
        local waited=0
        
        while [[ $waited -lt $max_wait ]]; do
            if curl -f -s "$app_url/health" >/dev/null 2>&1; then
                log_success "Test application is healthy"
                break
            fi
            
            sleep 2
            waited=$((waited + 2))
        done
        
        if [[ $waited -ge $max_wait ]]; then
            log_error "Test application health check failed"
            return 1
        fi
    fi
}

# Integration test teardown
integration_test_teardown() {
    log_info "Tearing down integration test environment"
    
    # Stop and remove containers
    for container_file in "$TEST_ENV_DIR"/*_container; do
        if [[ -f "$container_file" ]]; then
            local container_name
            container_name=$(cat "$container_file")
            
            log_info "Stopping container: $container_name"
            docker stop "$container_name" >/dev/null 2>&1 || true
            docker rm "$container_name" >/dev/null 2>&1 || true
        fi
    done
    
    # Remove test images
    docker rmi "test_app_$$" >/dev/null 2>&1 || true
    
    # Clean up test environment
    rm -rf "$TEST_ENV_DIR"
    
    log_info "Integration test environment cleaned up"
}

# API integration tests
test_api_endpoint() {
    local endpoint="$1"
    local method="${2:-GET}"
    local expected_status="${3:-200}"
    local request_body="${4:-}"
    local expected_response="${5:-}"
    
    local base_url="http://$TEST_APP_HOST:$TEST_APP_PORT"
    local url="$base_url$endpoint"
    
    log_debug "Testing API endpoint: $method $endpoint"
    
    # Build curl command
    local curl_opts=(
        --silent
        --show-error
        --write-out "HTTPSTATUS:%{http_code}"
        --max-time 30
        --request "$method"
    )
    
    if [[ -n "$request_body" ]]; then
        curl_opts+=(--data "$request_body" --header "Content-Type: application/json")
    fi
    
    # Make request
    local response
    response=$(curl "${curl_opts[@]}" "$url")
    
    # Extract HTTP status and body
    local http_status
    http_status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    local response_body
    response_body=$(echo "$response" | sed -e 's/HTTPSTATUS.*$//')
    
    # Validate status code
    if [[ "$http_status" -ne "$expected_status" ]]; then
        log_error "API test failed: expected status $expected_status, got $http_status"
        log_error "Response: $response_body"
        return 1
    fi
    
    # Validate response body if provided
    if [[ -n "$expected_response" ]]; then
        if [[ "$response_body" == *"$expected_response"* ]]; then
            log_debug "Response body validation passed"
        else
            log_error "API test failed: response body does not contain expected content"
            log_error "Expected: $expected_response"
            log_error "Actual: $response_body"
            return 1
        fi
    fi
    
    log_success "API test passed: $method $endpoint"
    return 0
}

# Database integration tests
test_database_operation() {
    local operation="$1"
    local expected_result="${2:-}"
    
    case "$operation" in
        "connection")
            if pg_isready -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" >/dev/null 2>&1; then
                log_success "Database connection test passed"
                return 0
            else
                log_error "Database connection test failed"
                return 1
            fi
            ;;
        "create_table")
            local sql="CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(100));"
            
            if PGPASSWORD="$TEST_DB_PASSWORD" psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d "$TEST_DB_NAME" -c "$sql" >/dev/null 2>&1; then
                log_success "Database table creation test passed"
                return 0
            else
                log_error "Database table creation test failed"
                return 1
            fi
            ;;
        "insert_data")
            local sql="INSERT INTO test_table (name) VALUES ('test_name');"
            
            if PGPASSWORD="$TEST_DB_PASSWORD" psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d "$TEST_DB_NAME" -c "$sql" >/dev/null 2>&1; then
                log_success "Database insert test passed"
                return 0
            else
                log_error "Database insert test failed"
                return 1
            fi
            ;;
        *)
            log_error "Unknown database operation: $operation"
            return 1
            ;;
    esac
}
```

### 2. End-to-End Testing
```bash
#!/bin/bash

# End-to-end test framework
e2e_test_setup() {
    local test_suite="$1"
    
    log_info "Setting up E2E test environment: $test_suite"
    
    # Setup full application stack
    setup_full_stack
    
    # Setup test data
    seed_test_data
    
    # Setup monitoring
    setup_test_monitoring
    
    log_info "E2E test environment ready"
}

# Setup full application stack
setup_full_stack() {
    local compose_file="docker-compose.test.yml"
    
    if [[ -f "$compose_file" ]]; then
        log_info "Starting full application stack"
        
        if docker-compose -f "$compose_file" up -d; then
            log_success "Application stack started"
            
            # Wait for all services to be healthy
            wait_for_stack_health "$compose_file"
        else
            log_error "Failed to start application stack"
            return 1
        fi
    else
        log_error "Docker Compose file not found: $compose_file"
        return 1
    fi
}

# Wait for stack health
wait_for_stack_health() {
    local compose_file="$1"
    local max_wait=180
    local waited=0
    
    log_info "Waiting for application stack to be healthy"
    
    while [[ $waited -lt $max_wait ]]; do
        local unhealthy_services
        unhealthy_services=$(docker-compose -f "$compose_file" ps --filter "health=unhealthy" -q)
        
        if [[ -z "$unhealthy_services" ]]; then
            # Check if all services are running
            local stopped_services
            stopped_services=$(docker-compose -f "$compose_file" ps --filter "status=exited" -q)
            
            if [[ -z "$stopped_services" ]]; then
                log_success "All services are healthy and running"
                return 0
            fi
        fi
        
        sleep 5
        waited=$((waited + 5))
    done
    
    log_error "Timeout waiting for services to be healthy"
    docker-compose -f "$compose_file" ps
    return 1
}

# Seed test data
seed_test_data() {
    log_info "Seeding test data"
    
    # Run data seeding script
    local seed_script="scripts/seed_test_data.sh"
    
    if [[ -f "$seed_script" ]]; then
        if bash "$seed_script"; then
            log_success "Test data seeded successfully"
        else
            log_error "Failed to seed test data"
            return 1
        fi
    else
        log_warn "No test data seeding script found"
    fi
}

# User journey testing
test_user_journey() {
    local journey_name="$1"
    local steps_file="$2"
    
    log_info "Testing user journey: $journey_name"
    
    if [[ ! -f "$steps_file" ]]; then
        log_error "Journey steps file not found: $steps_file"
        return 1
    fi
    
    local step_number=1
    local failed_step=""
    
    # Read and execute each step
    while IFS= read -r step; do
        # Skip empty lines and comments
        [[ -z "$step" || "$step" =~ ^[[:space:]]*# ]] && continue
        
        log_info "Executing step $step_number: $step"
        
        if eval "$step"; then
            log_success "Step $step_number completed successfully"
        else
            failed_step="Step $step_number: $step"
            log_error "Step $step_number failed: $step"
            break
        fi
        
        ((step_number++))
    done < "$steps_file"
    
    if [[ -n "$failed_step" ]]; then
        log_error "User journey failed at: $failed_step"
        return 1
    else
        log_success "User journey completed successfully: $journey_name"
        return 0
    fi
}

# Performance testing integration
run_performance_test() {
    local test_config="$1"
    local duration="${2:-60}"
    local concurrent_users="${3:-10}"
    
    log_info "Running performance test: $test_config"
    
    # Use Apache Bench for simple performance testing
    if command -v ab >/dev/null 2>&1; then
        local total_requests=$((concurrent_users * duration))
        local app_url="http://localhost:8080/"
        
        log_info "Running $total_requests requests with $concurrent_users concurrent users"
        
        local ab_output
        ab_output=$(ab -n "$total_requests" -c "$concurrent_users" "$app_url" 2>&1)
        
        # Parse results
        local requests_per_second
        requests_per_second=$(echo "$ab_output" | grep "Requests per second" | awk '{print $4}')
        
        local avg_response_time
        avg_response_time=$(echo "$ab_output" | grep "Time per request" | head -n1 | awk '{print $4}')
        
        log_info "Performance test results:"
        log_info "  Requests per second: $requests_per_second"
        log_info "  Average response time: ${avg_response_time}ms"
        
        # Store results
        echo "$ab_output" > "$TEST_OUTPUT_DIR/performance_test_$(date +%Y%m%d_%H%M%S).txt"
        
    else
        log_warn "Apache Bench (ab) not available for performance testing"
    fi
}

# E2E test teardown
e2e_test_teardown() {
    log_info "Tearing down E2E test environment"
    
    # Stop application stack
    local compose_file="docker-compose.test.yml"
    
    if [[ -f "$compose_file" ]]; then
        docker-compose -f "$compose_file" down -v --remove-orphans
        log_info "Application stack stopped and cleaned up"
    fi
    
    # Clean up test data and artifacts
    cleanup_test_artifacts
}

# Cleanup test artifacts
cleanup_test_artifacts() {
    # Remove test volumes
    docker volume ls -q -f "name=test_" | xargs -r docker volume rm
    
    # Remove test networks
    docker network ls -q -f "name=test_" | xargs -r docker network rm
    
    # Clean up temporary files
    find /tmp -name "test_*" -type d -mtime +1 -exec rm -rf {} + 2>/dev/null || true
    
    log_info "Test artifacts cleaned up"
}
```

### 3. Test Automation and CI Integration
```bash
#!/bin/bash

# Automated test runner
run_all_tests() {
    local test_type="${1:-all}"  # unit, integration, e2e, all
    local output_format="${2:-text}"  # text, junit, json
    
    log_info "Running automated tests: $test_type"
    
    local overall_result=0
    
    case "$test_type" in
        "unit"|"all")
            log_info "Running unit tests..."
            if run_unit_tests "$output_format"; then
                log_success "Unit tests passed"
            else
                log_error "Unit tests failed"
                overall_result=1
            fi
            ;;
    esac
    
    case "$test_type" in
        "integration"|"all")
            log_info "Running integration tests..."
            if run_integration_tests "$output_format"; then
                log_success "Integration tests passed"
            else
                log_error "Integration tests failed"
                overall_result=1
            fi
            ;;
    esac
    
    case "$test_type" in
        "e2e"|"all")
            log_info "Running E2E tests..."
            if run_e2e_tests "$output_format"; then
                log_success "E2E tests passed"
            else
                log_error "E2E tests failed"
                overall_result=1
            fi
            ;;
    esac
    
    # Generate combined report
    generate_combined_test_report
    
    return $overall_result
}

# Run unit tests
run_unit_tests() {
    local output_format="$1"
    
    local test_files=()
    mapfile -t test_files < <(find "$TEST_DIR" -name "*_test.sh" -type f)
    
    if [[ ${#test_files[@]} -eq 0 ]]; then
        log_warn "No unit test files found in $TEST_DIR"
        return 0
    fi
    
    local failed_suites=0
    
    for test_file in "${test_files[@]}"; do
        local suite_name
        suite_name=$(basename "$test_file" .sh)
        
        init_test_framework "$suite_name"
        
        if run_test_suite "$test_file"; then
            log_success "Test suite passed: $suite_name"
        else
            log_error "Test suite failed: $suite_name"
            ((failed_suites++))
        fi
    done
    
    if [[ $failed_suites -gt 0 ]]; then
        log_error "$failed_suites unit test suites failed"
        return 1
    else
        log_success "All unit test suites passed"
        return 0
    fi
}

# Run integration tests
run_integration_tests() {
    local output_format="$1"
    
    # Setup integration test environment
    integration_test_setup "integration_suite"
    
    local test_result=0
    
    # Run integration test scenarios
    local integration_tests=(
        "test_database_integration"
        "test_api_integration"
        "test_service_communication"
    )
    
    for test_name in "${integration_tests[@]}"; do
        if command -v "$test_name" >/dev/null 2>&1; then
            if "$test_name"; then
                log_success "Integration test passed: $test_name"
            else
                log_error "Integration test failed: $test_name"
                test_result=1
            fi
        else
            log_warn "Integration test function not found: $test_name"
        fi
    done
    
    # Teardown integration test environment
    integration_test_teardown
    
    return $test_result
}

# Run E2E tests
run_e2e_tests() {
    local output_format="$1"
    
    # Setup E2E test environment
    e2e_test_setup "e2e_suite"
    
    local test_result=0
    
    # Run user journey tests
    local journey_files=()
    mapfile -t journey_files < <(find "$TEST_DIR/journeys" -name "*.txt" -type f 2>/dev/null)
    
    for journey_file in "${journey_files[@]}"; do
        local journey_name
        journey_name=$(basename "$journey_file" .txt)
        
        if test_user_journey "$journey_name" "$journey_file"; then
            log_success "User journey passed: $journey_name"
        else
            log_error "User journey failed: $journey_name"
            test_result=1
        fi
    done
    
    # Run performance tests
    if [[ "${RUN_PERFORMANCE_TESTS:-false}" == "true" ]]; then
        run_performance_test "default" 60 10
    fi
    
    # Teardown E2E test environment
    e2e_test_teardown
    
    return $test_result
}

# Generate combined test report
generate_combined_test_report() {
    local combined_report="$TEST_OUTPUT_DIR/combined_test_report_$(date +%Y%m%d_%H%M%S).html"
    
    cat > "$combined_report" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .passed { color: green; }
        .failed { color: red; }
        .skipped { color: orange; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Automated Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Generated:</strong> $(date)</p>
        <p><strong>Total Test Suites:</strong> $(find "$TEST_OUTPUT_DIR" -name "test_report_*.txt" | wc -l)</p>
    </div>
    
    <h2>Test Results</h2>
    <div id="test-results">
        <!-- Test results will be populated here -->
    </div>
</body>
</html>
EOF
    
    log_info "Combined test report generated: $combined_report"
}

# CI/CD integration
prepare_ci_artifacts() {
    local ci_artifacts_dir="${CI_ARTIFACTS_DIR:-./ci-artifacts}"
    
    mkdir -p "$ci_artifacts_dir"
    
    # Copy test reports
    cp -r "$TEST_OUTPUT_DIR"/* "$ci_artifacts_dir/" 2>/dev/null || true
    
    # Generate test summary for CI
    local test_summary="$ci_artifacts_dir/test_summary.json"
    
    cat > "$test_summary" << EOF
{
    "test_run": {
        "timestamp": "$(date -Iseconds)",
        "total_tests": $TOTAL_TESTS,
        "passed_tests": $PASSED_TESTS,
        "failed_tests": $FAILED_TESTS,
        "skipped_tests": $SKIPPED_TESTS,
        "success_rate": $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")
    }
}
EOF
    
    log_info "CI artifacts prepared in: $ci_artifacts_dir"
}
```

This comprehensive testing and validation framework provides unit testing, mocking, integration testing, end-to-end testing, and CI/CD integration capabilities for ensuring Bash scripts are reliable and production-ready.