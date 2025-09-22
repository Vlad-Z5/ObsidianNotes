# Linux Process Management Debugging Monitoring

**Process Debugging and Monitoring** covers system call tracing, library call tracing, and comprehensive process resource monitoring for advanced troubleshooting and analysis.

## System Call Tracing

### strace - System Call Tracer

#### Basic strace Usage
```bash
# Basic tracing
strace ls /tmp                         # Trace system calls for ls command
strace -p 1234                         # Attach to running process PID 1234
strace -f -p 1234                      # Follow child processes
strace -e open,read,write ls           # Trace specific system calls only

# Output control
strace -o trace.log ls                 # Output trace to file
strace -q ls                           # Quiet mode, suppress attach/detach messages
strace -v ls                           # Verbose mode, print unabbreviated output
strace -s 1000 cat file.txt            # Increase string display length (default: 32)

# Process attachment
strace -p $(pgrep nginx | head -1)     # Attach to first nginx process
strace -f -p $(pgrep -f "python app.py")  # Follow python application and children
```

#### Advanced strace Options
```bash
# Performance analysis
strace -c ls                           # Count and summarize system calls
strace -T ls                           # Show time spent in each system call
strace -tt -T -o trace.log program     # Timestamps and timing in trace file
strace -r ls                           # Relative timestamps between calls

# Filtering and selection
strace -e file nginx                   # File operations only
strace -e network curl https://api.com # Network operations only
strace -e desc ls                      # File descriptor operations
strace -e ipc program                  # Inter-process communication calls
strace -e memory program               # Memory-related calls
strace -e process program              # Process management calls

# Advanced filtering
strace -e '!write' ls                  # All calls except write
strace -e 'trace=file,desc' program    # Multiple categories
strace -e 'abbrev=write' program       # Abbreviate write call output
strace -e 'verbose=open' program       # Verbose output for open calls only
```

#### DevOps Debugging Scenarios
```bash
# Application startup troubleshooting
strace -f -e trace=file,process systemctl start myapp  # Track file access and process creation
strace -e open,stat,access ./myapp     # Debug configuration file loading

# Network debugging
strace -e network,desc curl -v https://api.example.com  # Network operations
strace -e socket,connect,bind nginx    # Socket operations
strace -p $(pgrep -f "port 8080") -e network  # Monitor network activity

# File system debugging
strace -e file,desc -p $(pgrep -f myapp)  # File operations for running app
strace -f -e clone,exec,exit systemctl start myapp  # Process creation tracking
strace -e write -p $(pgrep -f java)    # Track write operations

# Performance investigation
strace -c -p PID                       # Count system calls for performance analysis
strace -T -e '!read,write' -p PID      # Time analysis excluding I/O operations

# Error diagnosis
strace -e signal program               # Signal handling
strace -e fault=read:error=ENOSPC program  # Inject read errors for testing
```

### ltrace - Library Call Tracer

#### Basic ltrace Usage
```bash
# Basic library call tracing
ltrace ls                              # Trace library function calls
ltrace -p 1234                         # Attach to running process
ltrace -f program                      # Follow child processes
ltrace -c ls                           # Count library calls

# Function filtering
ltrace -e malloc,free program          # Trace specific functions
ltrace -e 'malloc*' program            # Wildcard function matching
ltrace -e '@libc.so*' program          # Functions from specific library

# Output control
ltrace -o trace.log program            # Output to file
ltrace -n 2 program                    # Show function arguments (depth 2)
ltrace -s 100 program                  # String length in output
```

#### Advanced ltrace Usage
```bash
# Memory debugging with ltrace
ltrace -e malloc,free,realloc program  # Memory allocation tracking
ltrace -e calloc,malloc,free,realloc -c program  # Complete memory profile

# Library analysis
ltrace -S program                      # Include system calls in output
ltrace -l /usr/lib/libssl.so program   # Focus on specific library
ltrace -x 'malloc*' program            # Trace library and hex dump

# Application debugging
ltrace -f -e 'printf*,puts*' program   # Output function calls
ltrace -e 'open*,close*' program       # File operation functions
ltrace -e 'pthread*' program           # Threading function calls

# Performance analysis
ltrace -T program                      # Show time in each library call
ltrace -ttt program                    # Absolute timestamps
ltrace -r program                      # Relative timestamps
```

## Process Resource Monitoring

### lsof - List Open Files

#### Basic lsof Usage
```bash
# File and process relationships
lsof                                   # List all open files (very verbose)
lsof /var/log/messages                 # Processes using specific file
lsof -p 1234                           # Files opened by specific process
lsof -u username                       # Files opened by user
lsof -c nginx                          # Files opened by command name
lsof -g 1000                           # Files opened by process group

# Directory analysis
lsof +D /var/log                       # Recursively show directory usage
lsof +d /tmp                           # Files in directory (non-recursive)
lsof /home                             # Processes using /home filesystem
```

#### Network Connection Analysis
```bash
# Network connections
lsof -i                                # All network connections
lsof -i :80                            # Connections on port 80
lsof -i :8080-8090                     # Port range
lsof -i tcp                            # TCP connections only
lsof -i udp                            # UDP connections only
lsof -i 4                              # IPv4 connections only
lsof -i 6                              # IPv6 connections only

# Specific network analysis
lsof -i @192.168.1.100                 # Connections to specific IP
lsof -i @192.168.1.0/24                # Connections to subnet
lsof -i tcp:ssh                        # SSH connections
lsof -i :443 | grep LISTEN             # Who's listening on HTTPS port

# Connection states
lsof -i -sTCP:ESTABLISHED              # Established TCP connections
lsof -i -sTCP:LISTEN                   # Listening TCP ports
lsof -i -sUDP:Idle                     # Idle UDP sockets
```

#### DevOps Troubleshooting Scenarios
```bash
# Deleted files still held open (disk space issues)
lsof | grep deleted                    # Find deleted files still held open
lsof +L1                               # Files with link count less than 1 (deleted)

# Port conflicts and service debugging
lsof -i :80 | grep LISTEN              # What's listening on port 80
lsof -u apache -i                      # Network connections by apache user
lsof -c java -i :8080                  # Java processes on port 8080

# File lock investigation
lsof /var/lib/mysql/ibdata1            # What's accessing database files
lsof /var/run/lock/                    # Lock file usage

# Application file usage
lsof -c myapp +L1                      # Application with unlinked files
lsof -p $(pgrep -f myapp) | grep -v REG # Non-regular files (sockets, pipes)

# System resource debugging
lsof -u root -a -i                     # Root processes with network connections
lsof /dev/null                         # Processes using /dev/null
```

### Advanced Process Monitoring

#### Comprehensive Process Analysis
```bash
# Combined debugging approach
debug_process() {
    local pid="$1"
    local duration="${2:-30}"

    if [[ -z "$pid" ]]; then
        echo "Usage: debug_process <PID> [duration]"
        return 1
    fi

    echo "=== Process Debug Analysis for PID $pid ==="
    echo "Command: $(ps -p $pid -o comm=)"
    echo "Start time: $(date)"
    echo

    # Basic process information
    echo "Process Information:"
    ps -p $pid -o pid,ppid,pgid,sid,user,comm,args
    echo

    # Open files
    echo "Open Files (first 20):"
    lsof -p $pid | head -20
    echo

    # Network connections
    echo "Network Connections:"
    lsof -p $pid -i
    echo

    # Start tracing
    echo "Starting system call trace for $duration seconds..."
    timeout $duration strace -p $pid -c 2>&1 | tail -20
    echo

    # Memory and resource usage
    echo "Memory Usage:"
    cat /proc/$pid/status | grep -E 'VmPeak|VmSize|VmRSS|VmData|VmStk|VmExe'
    echo

    # File descriptor usage
    echo "File Descriptor Count: $(ls /proc/$pid/fd 2>/dev/null | wc -l)"
    echo "File Descriptor Limit: $(ulimit -n)"
}

# Process tree analysis
analyze_process_tree() {
    local root_pid="$1"

    echo "=== Process Tree Analysis ==="
    pstree -p $root_pid
    echo

    echo "Child Process Resource Usage:"
    ps --forest -o pid,ppid,pcpu,pmem,cmd -g $(ps -p $root_pid -o pgid=)
}

# Service dependency analysis
analyze_service_deps() {
    local service="$1"

    echo "=== Service Dependency Analysis: $service ==="

    # Service status
    systemctl status $service
    echo

    # Process tree
    main_pid=$(systemctl show $service --property=MainPID --value)
    if [[ "$main_pid" != "0" ]]; then
        echo "Main Process Tree:"
        pstree -p $main_pid
        echo

        echo "Open Files:"
        lsof -p $main_pid | head -15
        echo
    fi

    # Service dependencies
    echo "Service Dependencies:"
    systemctl list-dependencies $service
}
```

#### Real-time Process Monitoring
```bash
# Real-time monitoring script
cat << 'EOF' > /usr/local/bin/process-monitor
#!/bin/bash
# Real-time process monitoring

monitor_process() {
    local pid="$1"
    local interval="${2:-5}"

    if [[ ! -d "/proc/$pid" ]]; then
        echo "Process $pid does not exist"
        return 1
    fi

    echo "Monitoring PID $pid (Ctrl+C to stop)"

    while [[ -d "/proc/$pid" ]]; do
        clear
        echo "=== Process Monitor: PID $pid ==="
        echo "Time: $(date)"
        echo

        # Basic info
        ps -p $pid -o pid,ppid,user,pcpu,pmem,etime,cmd
        echo

        # Memory details
        echo "Memory Usage:"
        cat /proc/$pid/status 2>/dev/null | grep -E 'VmRSS|VmSize|VmData|VmStk'
        echo

        # File descriptors
        fd_count=$(ls /proc/$pid/fd 2>/dev/null | wc -l)
        echo "File Descriptors: $fd_count"

        # Network connections
        net_count=$(lsof -p $pid -i 2>/dev/null | wc -l)
        echo "Network Connections: $net_count"

        # Recent system calls (if strace available)
        if command -v strace >/dev/null; then
            echo
            echo "Recent System Call Summary (5 seconds):"
            timeout 5 strace -p $pid -c 2>&1 | tail -10 | head -5
        fi

        sleep $interval
    done

    echo "Process $pid has terminated"
}

# Usage
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <PID> [interval_seconds]"
    echo "Example: $0 1234 10"
else
    monitor_process "$1" "$2"
fi
EOF

chmod +x /usr/local/bin/process-monitor

# Multi-process monitoring
cat << 'EOF' > /usr/local/bin/multi-process-monitor
#!/bin/bash
# Monitor multiple processes by pattern

pattern="$1"
interval="${2:-10}"

if [[ -z "$pattern" ]]; then
    echo "Usage: $0 <process_pattern> [interval]"
    echo "Example: $0 nginx 5"
    exit 1
fi

while true; do
    clear
    echo "=== Multi-Process Monitor: $pattern ==="
    echo "Time: $(date)"
    echo "Interval: ${interval}s"
    echo

    # Find matching processes
    pids=$(pgrep -f "$pattern")

    if [[ -z "$pids" ]]; then
        echo "No processes found matching: $pattern"
    else
        echo "Matching Processes:"
        ps -p $pids -o pid,ppid,user,pcpu,pmem,etime,cmd
        echo

        echo "Total Resource Usage:"
        ps -p $pids -o pid,pcpu,pmem,rss,vsz --no-headers | \
            awk '{cpu+=$2; mem+=$3; rss+=$4; vsz+=$5; count++}
                 END {printf "Processes: %d, Total CPU: %.1f%%, Total Memory: %.1f%%, RSS: %dKB, VSZ: %dKB\n",
                      count, cpu, mem, rss, vsz}'
        echo

        echo "Network Connections:"
        for pid in $pids; do
            count=$(lsof -p $pid -i 2>/dev/null | wc -l)
            echo "PID $pid: $count connections"
        done
    fi

    sleep $interval
done
EOF

chmod +x /usr/local/bin/multi-process-monitor
```