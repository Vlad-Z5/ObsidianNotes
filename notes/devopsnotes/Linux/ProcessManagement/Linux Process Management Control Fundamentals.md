# Linux Process Management Control Fundamentals

**Process Control Fundamentals** covers basic process monitoring, signal management, job control, and background processing essential for Linux system administration.

## Process Monitoring and Management

### ps Command Variations
```bash
# Standard process listing formats
ps aux                                  # All processes, user-oriented format
ps -ef                                  # All processes, full format
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu  # Custom format with sorting

# DevOps-specific process analysis
ps -C nginx                            # Processes by command name
ps --forest                            # Process tree visualization
ps -o pid,ppid,state,comm -g $(pgrep -f myapp)  # Process group information

# Memory and CPU analysis
ps aux --sort=-%mem | head -10          # Top memory consumers
ps aux --sort=-%cpu | head -10          # Top CPU consumers
ps -eo pid,ppid,cmd,pmem,pcpu,time --sort=-pmem # Detailed resource usage

# Advanced process filtering
ps -eo pid,ppid,uid,gid,cmd --no-headers | awk '$3 >= 1000'  # User processes only
ps -eo pid,cmd,etime --sort=etime       # Processes sorted by runtime
ps -eo pid,cmd,rss,vsz | awk 'NR>1 {sum+=$3} END {print "Total RSS:", sum "KB"}'  # Memory sum
```

### Process Information Gathering
```bash
# Detailed process information
pstree                                  # Process tree with relationships
pstree -p                              # Include process IDs
pstree -u                              # Show user transitions
pstree -a                              # Show command line arguments

# Process status files
cat /proc/PID/status                   # Detailed process status
cat /proc/PID/cmdline                  # Command line used to start process
cat /proc/PID/environ                  # Environment variables
cat /proc/PID/maps                     # Memory mappings
cat /proc/PID/fd/                      # File descriptors
ls -l /proc/PID/fd/                    # Open file descriptors

# Real-time process monitoring
watch 'ps aux | head -20'              # Monitor top processes
watch 'ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -15'  # CPU usage monitor
```

## Process States and Signals

### Understanding Process States
```bash
# Process state monitoring
ps -eo pid,stat,comm
# Process state codes:
# D: Uninterruptible sleep (usually I/O wait)
# R: Running or runnable (on run queue)
# S: Interruptible sleep (waiting for event)
# T: Stopped (by job control signal)
# Z: Zombie (terminated but not reaped)
# < : High priority process
# N : Low priority process
# + : Foreground process group

# Find processes in specific states
ps -eo pid,stat,comm | grep "^[[:space:]]*[0-9]*[[:space:]]*D"  # Uninterruptible sleep
ps -eo pid,stat,comm | grep "^[[:space:]]*[0-9]*[[:space:]]*Z"  # Zombie processes
ps -eo pid,stat,comm | grep "^[[:space:]]*[0-9]*[[:space:]]*T"  # Stopped processes

# Process state analysis
echo "Running processes: $(ps -eo stat | grep -c '^R')"
echo "Sleeping processes: $(ps -eo stat | grep -c '^S')"
echo "Zombie processes: $(ps -eo stat | grep -c '^Z')"
```

### Signal Management
```bash
# Signal operations
kill -l                                 # List all available signals
kill -TERM pid                         # Graceful termination (SIGTERM)
kill -KILL pid                         # Force kill (SIGKILL)
kill -HUP pid                          # Reload configuration (SIGHUP)
kill -USR1 pid                         # User-defined signal 1
kill -USR2 pid                         # User-defined signal 2
kill -STOP pid                         # Stop process (SIGSTOP)
kill -CONT pid                         # Continue process (SIGCONT)

# Process groups and pattern matching
killall nginx                          # Kill all nginx processes
killall -u username                    # Kill all processes by user
pkill -f "python.*myapp"               # Kill processes matching pattern
pgrep -u apache                        # Find processes by user
pgrep -f "java.*tomcat"                # Find processes by command pattern

# Signal sending examples
kill -HUP $(pgrep nginx)               # Reload nginx configuration
kill -USR2 $(pgrep gunicorn)           # Graceful restart gunicorn workers
pkill -TERM -f "worker_process"        # Terminate all worker processes

# Signal handling verification
timeout 10 ping google.com &           # Start background process
PID=$!
sleep 2
kill -TERM $PID                        # Send TERM signal
wait $PID 2>/dev/null; echo "Exit code: $?"  # Check exit status
```

### Advanced Signal Operations
```bash
# Send signals to process groups
kill -TERM -$(ps -o pgid= -p $PID | tr -d ' ')  # Kill entire process group

# Signal handling with trap in scripts
cat << 'EOF' > signal_handler.sh
#!/bin/bash
# Signal handling example

cleanup() {
    echo "Received signal, cleaning up..."
    # Cleanup operations here
    exit 0
}

# Set signal handlers
trap cleanup SIGTERM SIGINT SIGHUP

echo "Process started with PID: $$"
while true; do
    echo "Working... $(date)"
    sleep 5
done
EOF

chmod +x signal_handler.sh

# Test signal handling
./signal_handler.sh &
SCRIPT_PID=$!
sleep 10
kill -TERM $SCRIPT_PID
```

## Job Control and Background Processing

### Basic Job Control
```bash
# Background and foreground job management
command &                              # Run command in background
jobs                                   # List active jobs in current shell
jobs -l                                # List jobs with process IDs
jobs -p                                # List only process IDs
jobs -r                                # List only running jobs
jobs -s                                # List only stopped jobs

# Job control operations
fg %1                                  # Bring job 1 to foreground
bg %2                                  # Send job 2 to background
kill %3                                # Kill job 3
suspend                                # Suspend current shell

# Job referencing
fg %?partial_name                      # Bring job containing 'partial_name' to foreground
kill %+                                # Kill current job
kill %-                                # Kill previous job
```

### Advanced Background Processing
```bash
# Persistent background processes
nohup command &                        # Run command immune to hangups
disown %1                              # Remove job from shell's job table
disown -h %1                           # Mark job to ignore SIGHUP
disown -r                              # Remove all running jobs from table

# Advanced nohup usage
nohup ./long_running_script.sh > /tmp/script.log 2>&1 &
echo $! > /tmp/script.pid              # Save PID for later reference

# Start detached processes
(command &)                            # Start in subshell (automatically disowned)
exec command &                         # Replace current shell with command

# Job control in scripts
cat << 'EOF' > background_job_manager.sh
#!/bin/bash
# Background job management script

start_background_job() {
    local job_name="$1"
    local command="$2"

    echo "Starting background job: $job_name"
    nohup $command > "/tmp/${job_name}.log" 2>&1 &
    local pid=$!
    echo $pid > "/tmp/${job_name}.pid"
    echo "Job $job_name started with PID: $pid"
}

stop_background_job() {
    local job_name="$1"
    local pid_file="/tmp/${job_name}.pid"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid"
            echo "Stopped job: $job_name (PID: $pid)"
        else
            echo "Job $job_name is not running"
        fi
        rm -f "$pid_file"
    else
        echo "PID file for $job_name not found"
    fi
}

# Usage examples
case "$1" in
    start)
        start_background_job "data_processor" "python /opt/scripts/process_data.py"
        ;;
    stop)
        stop_background_job "data_processor"
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        ;;
esac
EOF

chmod +x background_job_manager.sh
```

### Screen and Tmux for Persistent Sessions
```bash
# Screen session management
screen -S session_name                 # Create named screen session
screen -r session_name                 # Reattach to screen session
screen -d session_name                 # Detach from screen session
screen -list                           # List available screen sessions
screen -X -S session_name quit         # Kill screen session

# Screen keyboard shortcuts (Ctrl+A prefix)
# Ctrl+A + d: Detach from session
# Ctrl+A + c: Create new window
# Ctrl+A + n: Next window
# Ctrl+A + p: Previous window
# Ctrl+A + ": List windows

# Tmux session management
tmux new-session -s mysession          # Create named tmux session
tmux attach -t mysession               # Attach to tmux session
tmux detach-client                     # Detach current client
tmux list-sessions                     # List available tmux sessions
tmux kill-session -t mysession        # Kill tmux session

# Tmux keyboard shortcuts (Ctrl+B prefix)
# Ctrl+B + d: Detach from session
# Ctrl+B + c: Create new window
# Ctrl+B + n: Next window
# Ctrl+B + p: Previous window
# Ctrl+B + w: List windows

# Advanced tmux usage
tmux new-session -d -s worker 'python /opt/scripts/worker.py'  # Create detached session
tmux send-keys -t worker 'source /opt/venv/bin/activate' Enter  # Send commands to session
tmux capture-pane -t worker -p > /tmp/worker_output.txt        # Capture session output
```

### Process Control in Production
```bash
# Production-ready process management
cat << 'EOF' > production_process_manager.sh
#!/bin/bash
# Production process management

PROCESS_NAME="$1"
ACTION="$2"
PID_FILE="/var/run/${PROCESS_NAME}.pid"
LOG_FILE="/var/log/${PROCESS_NAME}.log"

start_process() {
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Process $PROCESS_NAME is already running"
        return 1
    fi

    echo "Starting $PROCESS_NAME..."
    nohup "/opt/bin/${PROCESS_NAME}" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Process started with PID: $(cat "$PID_FILE")"
}

stop_process() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "PID file not found. Process may not be running."
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "Process not running. Removing stale PID file."
        rm -f "$PID_FILE"
        return 1
    fi

    echo "Stopping $PROCESS_NAME (PID: $pid)..."
    kill -TERM "$pid"

    # Wait for graceful shutdown
    local count=0
    while kill -0 "$pid" 2>/dev/null && [[ $count -lt 30 ]]; do
        sleep 1
        ((count++))
    done

    if kill -0 "$pid" 2>/dev/null; then
        echo "Process did not stop gracefully. Force killing..."
        kill -KILL "$pid"
    fi

    rm -f "$PID_FILE"
    echo "Process stopped"
}

status_process() {
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "$PROCESS_NAME is running (PID: $(cat "$PID_FILE"))"
    else
        echo "$PROCESS_NAME is not running"
        return 1
    fi
}

case "$ACTION" in
    start)   start_process ;;
    stop)    stop_process ;;
    restart) stop_process && sleep 2 && start_process ;;
    status)  status_process ;;
    *)       echo "Usage: $0 <process_name> {start|stop|restart|status}" ;;
esac
EOF

chmod +x production_process_manager.sh
```