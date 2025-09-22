- **Shebang**: `#!/bin/bash` defines the script's interpreter, can be #!/bin/zsh, #!/usr/bin/env sh among many more. Use `which bash` to get yours. #!/bin/sh is implicit so better avoid it.
- **Script Components**
    - **Variables**: name=value (no spaces)
        - ${name}: access variable explicitly, without curly braces - implicitly
    - **Quotes**
        - "": expands variables
        - '': literal string
        - \`\`: (backticks) or $(): command substitution
    - **Conditionals**
        - if [ condition ]; then ...; fi
        - test or [ ] for comparisons
            - `-z`: string is empty; `-n`: string is not empty
            - `-f`: file exists; `-d`: directory exists
            - `-eq`, `-ne`, `-gt`, `-lt`, `-ge`, `-le`: integer comparisons
    - **Loops**
        - for var in list; do ...; done
        - while [ condition ]; do ...; done
        - until [ condition ]; do ...; done
    - **Functions**
        - name() { commands; }
    - **Special Variables**
        - `$0`: script name
        - `$1` to `$9`: positional args
        - `$#`: number of args
        - `$@`: all args
        - `$?`: exit status of last command
        - `$$`: PID of script
    - **Operators**
        - `&&`: run next only if previous succeeds
        - `||`: run next only if previous fails
        - `;`: run sequentially
        - `&`: run in background
    - **Input/Output**
        - `stdin` (0): standard input, usually from keyboard
        - `stdout` (1): standard output, usually to screen
        - `stderr` (2): standard error output
        - `>`: redirect stdout (overwrite)
        - `>>`: redirect stdout (append)
        - `&>`: redirect both stdout and stderr
        - > &2: write to stderr
        - `<`: redirect stdin from a file
        - `command > /dev/null`: discard stdout
        - `command 2> /dev/null`: discard stderr
        - read var: read input into `var`
        - echo: print to stdout
        - `|`: send stdout to the next command
        - We use heredoc with redirects often and it consists of the phrase and esarhp (phrase in reverse), everything in between will be treated as a single whole
    - **Exit**
        - `exit N`: exit with status N
        - `trap`: catch signals (e.g., `trap "echo Exiting" EXIT`)

## DevOps Automation Examples

### **System Monitoring Scripts**

#### **Server Health Check Script**
```bash
#!/bin/bash
# server_health_check.sh - Comprehensive server monitoring

set -euo pipefail

# Configuration
ALERT_EMAIL="admin@company.com"
LOG_FILE="/var/log/health_check.log"
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90

# Functions
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

check_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$cpu_usage > $CPU_THRESHOLD" | bc -l) )); then
        log_message "ALERT: CPU usage is ${cpu_usage}% (threshold: ${CPU_THRESHOLD}%)"
        return 1
    fi
    log_message "CPU usage: ${cpu_usage}%"
    return 0
}

check_memory() {
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100}')
    if [[ $mem_usage -gt $MEMORY_THRESHOLD ]]; then
        log_message "ALERT: Memory usage is ${mem_usage}% (threshold: ${MEMORY_THRESHOLD}%)"
        return 1
    fi
    log_message "Memory usage: ${mem_usage}%"
    return 0
}

check_disk() {
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    if [[ $disk_usage -gt $DISK_THRESHOLD ]]; then
        log_message "ALERT: Disk usage is ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)"
        return 1
    fi
    log_message "Disk usage: ${disk_usage}%"
    return 0
}

# Main execution
main() {
    log_message "Starting health check for $(hostname)"

    local alerts=0
    check_cpu || ((alerts++))
    check_memory || ((alerts++))
    check_disk || ((alerts++))

    if [[ $alerts -gt 0 ]]; then
        log_message "Health check completed with $alerts alerts"
        echo "Server $(hostname) health check failed with $alerts alerts" | \
            mail -s "Server Alert: $(hostname)" "$ALERT_EMAIL"
        exit 1
    else
        log_message "All health checks passed"
        exit 0
    fi
}

main "$@"
```

### **Deployment and CI/CD Scripts**

#### **Application Deployment Script**
```bash
#!/bin/bash
# deploy_app.sh - Blue-green deployment script

set -euo pipefail

APP_NAME="myapp"
REPO_URL="https://github.com/company/myapp.git"
DEPLOY_DIR="/opt/deployments"
CURRENT_LINK="/opt/current"
HEALTH_CHECK_URL="http://localhost:8080/health"

deploy_new_version() {
    local version="$1"
    local deploy_path="$DEPLOY_DIR/$APP_NAME-$version"

    echo "Deploying version $version to $deploy_path"

    git clone --branch "$version" --single-branch "$REPO_URL" "$deploy_path"
    cd "$deploy_path"
    npm install --production
    npm run build
    cp /etc/app/config.json ./config/

    echo "Version $version deployed successfully"
}

health_check() {
    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$HEALTH_CHECK_URL" >/dev/null; then
            echo "Health check passed"
            return 0
        fi
        echo "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done

    echo "Health check failed after $max_attempts attempts"
    return 1
}

main() {
    local version="${1:-}"
    [[ -z "$version" ]] && { echo "Usage: $0 <version>"; exit 1; }

    deploy_new_version "$version"
    ln -sfn "$DEPLOY_DIR/$APP_NAME-$version" "$CURRENT_LINK"
    systemctl restart "$APP_NAME"

    if health_check; then
        echo "Deployment of version $version completed successfully"
        ls -1t "$DEPLOY_DIR" | tail -n +4 | xargs -I {} rm -rf "$DEPLOY_DIR/{}"
    else
        echo "Deployment failed health check, rolling back"
        exit 1
    fi
}

main "$@"
```

### **Error Handling and Debugging**

#### **Advanced Error Handling Patterns**
```bash
#!/bin/bash
# error_handling_example.sh - Robust error handling patterns

set -euo pipefail

# Global error handling
cleanup() {
    local exit_code=$?
    echo "Script exiting with code: $exit_code"
    [[ -n "${TEMP_DIR:-}" ]] && rm -rf "$TEMP_DIR"
    exit $exit_code
}

trap cleanup EXIT

# Function with retry logic
retry_command() {
    local max_attempts=3
    local delay=5
    local attempt=1
    local command="$*"

    while [[ $attempt -le $max_attempts ]]; do
        echo "Attempt $attempt/$max_attempts: $command"

        if $command; then
            return 0
        fi

        if [[ $attempt -eq $max_attempts ]]; then
            echo "Command failed after $max_attempts attempts"
            return 1
        fi

        echo "Command failed, retrying in ${delay}s..."
        sleep $delay
        ((attempt++))
        delay=$((delay * 2))  # Exponential backoff
    done
}

# Validation functions
validate_input() {
    local input="$1"
    local pattern="$2"
    local description="$3"

    if [[ ! $input =~ $pattern ]]; then
        echo "Error: Invalid $description: $input"
        echo "Expected pattern: $pattern"
        return 1
    fi
}
```

## Integration with DevOps Tools

### **Configuration Management Integration**
- Use scripts as Ansible playbook tasks or modules
- Integrate with Terraform for infrastructure provisioning
- Create reusable functions for Docker container initialization
- Build deployment pipelines with Jenkins or GitLab CI

### **Monitoring and Logging Integration**
- Send script metrics to Prometheus with custom exporters
- Log structured data for ELK stack analysis
- Create custom health checks for Kubernetes readiness probes
- Generate alerts for monitoring systems (PagerDuty, Slack)

### **Cross-References**
- **[[Linux Commands]]** - Command reference for script development
- **[[Linux System Administration]]** - System service integration
- **[[Linux Process Management]]** - Advanced process handling in scripts