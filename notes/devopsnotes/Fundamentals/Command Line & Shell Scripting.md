# Command Line & Shell Scripting: The DevOps Power User's Toolkit

## Why Command Line Mastery Matters

Command line proficiency is essential for DevOps engineers. It enables automation, remote system management, efficient troubleshooting, and integration with virtually every DevOps tool and platform.

## Essential Command Line Skills

### File and Directory Operations
```bash
# Navigation and exploration
pwd                    # Print working directory
ls -la                # List files with details and hidden files
cd /path/to/directory # Change directory
find . -name "*.log"  # Find files by pattern

# File manipulation
cp source dest        # Copy files
mv old_name new_name  # Move/rename files
rm -rf directory      # Remove files/directories recursively
chmod 755 script.sh   # Change file permissions
chown user:group file # Change file ownership
```

### Text Processing and Analysis
```bash
# View and search file contents
cat file.txt          # Display file contents
less file.txt         # Page through file contents
head -n 20 file.txt   # Show first 20 lines
tail -f logfile.log   # Follow log file in real-time
grep "error" *.log    # Search for patterns in files
grep -r "TODO" .      # Recursive search in directories

# Text manipulation
sed 's/old/new/g' file    # Replace text in files
awk '{print $1}' file     # Extract columns from text
sort file.txt             # Sort file contents
uniq -c sorted_file       # Count unique lines
cut -d',' -f1,3 file.csv  # Extract CSV columns
```

### Process and System Management
```bash
# Process monitoring
ps aux                # Show all running processes
ps aux | grep nginx   # Find specific processes
top                   # Real-time process monitoring
htop                  # Enhanced process monitoring
kill -9 PID          # Force kill process
killall process_name  # Kill processes by name

# System information
df -h                 # Disk space usage
du -sh directory      # Directory size
free -m              # Memory usage
uptime               # System uptime and load
uname -a             # System information
lscpu                # CPU information
```

### Network Operations
```bash
# Network connectivity
ping google.com       # Test connectivity
curl -I website.com   # HTTP headers
wget file_url         # Download files
netstat -tuln        # Show listening ports
ss -tuln             # Modern netstat alternative
nslookup domain.com   # DNS lookup
dig domain.com        # Detailed DNS information
```

## Shell Scripting Fundamentals

### Script Structure and Best Practices
```bash
#!/bin/bash
# Script description and author information

set -e  # Exit on any error
set -u  # Exit on undefined variables
set -o pipefail  # Exit on pipe failures

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/deployment.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Functions
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Main script logic
main() {
    log_message "Starting deployment process"
    # Script implementation
}

# Execute main function
main "$@"
```

### Variables and Parameter Handling
```bash
# Variable assignment and usage
SERVICE_NAME="web-server"
PORT=${PORT:-8080}  # Default value if not set
CONFIG_FILE="/etc/${SERVICE_NAME}/config.yml"

# Command line arguments
echo "Script name: $0"
echo "First argument: $1"
echo "All arguments: $@"
echo "Number of arguments: $#"

# Environment variables
export DATABASE_URL="postgres://localhost:5432/myapp"
env | grep DATABASE  # Show environment variables
```

### Control Flow and Logic
```bash
# Conditional statements
if [[ -f "$CONFIG_FILE" ]]; then
    echo "Config file exists"
elif [[ -d "/etc/alternative" ]]; then
    echo "Using alternative config"
else
    echo "No configuration found" >&2
    exit 1
fi

# Case statements
case "$ENVIRONMENT" in
    "production")
        REPLICAS=3
        ;;
    "staging")
        REPLICAS=2
        ;;
    *)
        REPLICAS=1
        ;;
esac

# Loops
for server in web1 web2 web3; do
    ssh "$server" "systemctl restart nginx"
done

while IFS= read -r line; do
    process_log_line "$line"
done < "$LOG_FILE"
```

### Error Handling and Debugging
```bash
# Error handling
deploy_application() {
    local app_name="$1"
    
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker not installed" >&2
        return 1
    fi
    
    if ! docker build -t "$app_name" .; then
        echo "Error: Build failed for $app_name" >&2
        return 1
    fi
    
    echo "Successfully built $app_name"
}

# Debugging techniques
set -x  # Enable command tracing
bash -x script.sh  # Run script with tracing
echo "Debug: Variable value is $VAR" >&2
```

## DevOps-Specific Scripting Patterns

### Deployment Scripts
```bash
#!/bin/bash
# Application deployment script

ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
APP_NAME="my-application"

deploy() {
    echo "Deploying $APP_NAME version $VERSION to $ENVIRONMENT"
    
    # Pull latest image
    docker pull "$APP_NAME:$VERSION"
    
    # Stop existing container
    docker stop "$APP_NAME-$ENVIRONMENT" 2>/dev/null || true
    docker rm "$APP_NAME-$ENVIRONMENT" 2>/dev/null || true
    
    # Start new container
    docker run -d \
        --name "$APP_NAME-$ENVIRONMENT" \
        --env-file ".env.$ENVIRONMENT" \
        -p "80:8080" \
        "$APP_NAME:$VERSION"
    
    # Health check
    sleep 10
    if curl -f "http://localhost/health"; then
        echo "Deployment successful"
    else
        echo "Deployment failed - health check failed" >&2
        exit 1
    fi
}

deploy
```

### Monitoring and Alerting Scripts
```bash
#!/bin/bash
# System monitoring script

THRESHOLD_CPU=80
THRESHOLD_MEMORY=85
THRESHOLD_DISK=90

check_system_health() {
    # CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    
    # Memory usage
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    # Disk usage
    disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    # Check thresholds and alert
    if (( $(echo "$cpu_usage > $THRESHOLD_CPU" | bc -l) )); then
        send_alert "High CPU usage: ${cpu_usage}%"
    fi
    
    if (( memory_usage > THRESHOLD_MEMORY )); then
        send_alert "High memory usage: ${memory_usage}%"
    fi
    
    if (( disk_usage > THRESHOLD_DISK )); then
        send_alert "High disk usage: ${disk_usage}%"
    fi
}

send_alert() {
    local message="$1"
    # Send to Slack, email, or monitoring system
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$message\"}" \
        "$SLACK_WEBHOOK_URL"
}

check_system_health
```

### Backup and Maintenance Scripts
```bash
#!/bin/bash
# Database backup script with rotation

DATABASE_NAME="production_db"
BACKUP_DIR="/backups/database"
RETENTION_DAYS=7

create_backup() {
    local backup_file="$BACKUP_DIR/${DATABASE_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"
    
    echo "Creating backup: $backup_file"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Create compressed backup
    pg_dump "$DATABASE_NAME" | gzip > "$backup_file"
    
    if [[ $? -eq 0 ]]; then
        echo "Backup created successfully: $backup_file"
        
        # Remove old backups
        find "$BACKUP_DIR" -name "${DATABASE_NAME}_*.sql.gz" \
            -mtime +$RETENTION_DAYS -delete
            
        echo "Old backups cleaned up (older than $RETENTION_DAYS days)"
    else
        echo "Backup failed" >&2
        exit 1
    fi
}

create_backup
```

## Advanced Shell Features

### Process Substitution and Pipelines
```bash
# Compare outputs of two commands
diff <(command1) <(command2)

# Process multiple commands in parallel
command1 & command2 & wait

# Complex pipelines
cat access.log | grep "ERROR" | awk '{print $1}' | sort | uniq -c | sort -nr
```

### Arrays and Complex Data Structures
```bash
# Arrays
servers=("web1.example.com" "web2.example.com" "web3.example.com")
for server in "${servers[@]}"; do
    ssh "$server" "uptime"
done

# Associative arrays
declare -A environments
environments[dev]="development.example.com"
environments[staging]="staging.example.com"
environments[prod]="production.example.com"
```

## Integration with DevOps Tools

### Docker Integration
```bash
# Container management
docker_cleanup() {
    echo "Removing stopped containers..."
    docker container prune -f
    
    echo "Removing unused images..."
    docker image prune -f
    
    echo "Removing unused volumes..."
    docker volume prune -f
}
```

### Kubernetes Integration
```bash
# Kubernetes deployment check
check_deployment() {
    local deployment="$1"
    local namespace="${2:-default}"
    
    if kubectl get deployment "$deployment" -n "$namespace" &>/dev/null; then
        local replicas=$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath='{.status.readyReplicas}')
        echo "Deployment $deployment has $replicas ready replicas"
    else
        echo "Deployment $deployment not found" >&2
        return 1
    fi
}
```

### CI/CD Integration
```bash
# Build and test pipeline
run_pipeline() {
    echo "Starting CI/CD pipeline..."
    
    # Run tests
    if ! npm test; then
        echo "Tests failed" >&2
        exit 1
    fi
    
    # Build application
    if ! npm run build; then
        echo "Build failed" >&2
        exit 1
    fi
    
    # Deploy if on main branch
    if [[ "$GITHUB_REF" == "refs/heads/main" ]]; then
        deploy_to_production
    fi
}
```

## Best Practices and Tips

### Script Organization
- Keep scripts in version control
- Use meaningful file names and directory structure
- Include documentation and usage examples
- Implement proper logging and error handling

### Security Considerations
- Never hardcode secrets in scripts
- Use environment variables for sensitive data
- Validate input parameters
- Run with minimal required permissions
- Use secure temporary file creation

### Performance Optimization
- Use built-in shell features instead of external commands when possible
- Minimize subprocess creation in loops
- Use appropriate tools for data processing (awk vs sed vs grep)
- Implement proper error handling to avoid hanging scripts

### Testing and Maintenance
- Test scripts in non-production environments first
- Use shellcheck for static analysis
- Implement unit tests for complex functions
- Document script dependencies and requirements
- Regular review and updates for security and functionality

Command line and shell scripting skills form the foundation for effective DevOps automation, enabling engineers to build robust, maintainable systems and processes.