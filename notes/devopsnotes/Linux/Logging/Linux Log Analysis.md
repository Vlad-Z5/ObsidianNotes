# Linux Log Analysis

**Log analysis** involves examining system and application logs to troubleshoot issues, monitor performance, and detect security incidents.

## Essential Log Analysis Tools

### grep and egrep
```bash
# Basic pattern searching
grep "error" /var/log/syslog
grep -i "failed" /var/log/auth.log    # Case insensitive
grep -v "info" /var/log/app.log       # Exclude pattern
grep -n "warning" /var/log/syslog     # Show line numbers

# Multiple patterns
grep -E "error|warning|critical" /var/log/syslog
egrep "(failed|denied)" /var/log/auth.log

# Context lines
grep -A 5 -B 5 "error" /var/log/app.log    # 5 lines before/after
grep -C 3 "exception" /var/log/app.log     # 3 lines context
```

### awk for Structured Analysis
```bash
# Extract specific fields
awk '{print $1, $3, $9}' /var/log/access.log    # Print fields 1, 3, 9
awk '/error/ {print $0}' /var/log/syslog         # Print lines with "error"

# Time-based filtering
awk '$3 >= "10:00:00" && $3 <= "11:00:00"' /var/log/syslog

# Count occurrences
awk '/failed/ {count++} END {print count}' /var/log/auth.log

# Sum values
awk '{sum+=$10} END {print sum}' /var/log/access.log    # Sum response sizes
```

### sed for Text Processing
```bash
# Extract specific patterns
sed -n '/error/p' /var/log/app.log            # Print only lines with "error"
sed '1,100p' /var/log/syslog                  # Print first 100 lines

# Remove timestamp for cleaner output
sed 's/^[A-Z][a-z][a-z] [0-9]* [0-9:]*//g' /var/log/syslog

# Extract IP addresses
sed -n 's/.*\([0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\).*/\1/p' /var/log/access.log
```

## Real-Time Log Monitoring

### tail and Variants
```bash
# Follow log in real-time
tail -f /var/log/syslog
tail -F /var/log/app.log       # Follow with rotation handling

# Multiple files
tail -f /var/log/syslog /var/log/auth.log

# With highlighting
tail -f /var/log/syslog | grep --color=always -E "error|warning|$"

# Last N lines
tail -n 100 /var/log/syslog
```

### watch Command
```bash
# Monitor log file size
watch -n 1 'ls -lh /var/log/app.log'

# Monitor error count
watch -n 5 'grep -c "error" /var/log/app.log'

# Monitor latest entries
watch -n 2 'tail -5 /var/log/syslog'
```

## Advanced Analysis Techniques

### Find Top Error Sources
```bash
# Most common errors
grep "error" /var/log/app.log | awk '{print $5}' | sort | uniq -c | sort -nr | head -10

# Top IP addresses in access logs
awk '{print $1}' /var/log/access.log | sort | uniq -c | sort -nr | head -10

# Top user agents
awk -F'"' '{print $6}' /var/log/access.log | sort | uniq -c | sort -nr | head -10
```

### Time-Based Analysis
```bash
# Errors per hour
grep "error" /var/log/app.log | awk '{print $3}' | cut -d: -f1 | sort | uniq -c

# Activity by day
awk '{print $1}' /var/log/syslog | sort | uniq -c

# Peak usage times
awk '{print $3}' /var/log/access.log | cut -d: -f1-2 | sort | uniq -c | sort -nr
```

### Statistical Analysis
```bash
# Response time statistics
awk '{print $NF}' /var/log/access.log | sort -n | awk '
BEGIN {c = 0; sum = 0}
{
    a[c++] = $1; sum += $1
}
END {
    ave = sum / c;
    print "Average:", ave
    print "Min:", a[0]
    print "Max:", a[c-1]
    print "Median:", (c % 2) ? a[int(c/2)] : (a[c/2-1] + a[c/2]) / 2
}'
```

## Security Log Analysis

### Failed Login Attempts
```bash
# Count failed SSH attempts
grep "Failed password" /var/log/auth.log | wc -l

# Top failed login IPs
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -nr

# Successful logins after failures
grep -A 5 "Failed password" /var/log/auth.log | grep "Accepted"

# Brute force detection
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | awk '$1 > 10 {print $2, $1}'
```

### Privilege Escalation
```bash
# Sudo usage tracking
grep "sudo" /var/log/auth.log | awk '{print $1, $2, $3, $5, $6}'

# Root login attempts
grep "root" /var/log/auth.log | grep -E "login|session"

# User switching
grep "su:" /var/log/auth.log
```

## Performance Analysis

### System Resource Monitoring
```bash
# High CPU usage events
grep "cpu" /var/log/syslog | grep -i "high\|load"

# Memory issues
grep -i "memory\|oom\|killed" /var/log/syslog

# Disk space warnings
grep -i "disk\|space\|full" /var/log/syslog
```

### Application Performance
```bash
# Slow queries (if logged)
grep "slow" /var/log/mysql/mysql-slow.log

# High response times
awk '$NF > 5000 {print $0}' /var/log/access.log    # Responses > 5 seconds

# Error rate calculation
total=$(wc -l < /var/log/access.log)
errors=$(grep -E "5[0-9][0-9]" /var/log/access.log | wc -l)
echo "Error rate: $(echo "scale=2; $errors * 100 / $total" | bc)%"
```

## Log Analysis Scripts

### Daily Report Script
```bash
#!/bin/bash
# daily-log-report.sh

LOG_DATE=$(date -d "yesterday" +"%b %d")
REPORT_FILE="/tmp/daily-report-$(date +%Y%m%d).txt"

{
    echo "=== Daily Log Report for $LOG_DATE ==="
    echo

    echo "=== System Errors ==="
    grep "$LOG_DATE" /var/log/syslog | grep -i error | wc -l

    echo "=== Failed Login Attempts ==="
    grep "$LOG_DATE" /var/log/auth.log | grep "Failed password" | wc -l

    echo "=== Top Error IPs ==="
    grep "$LOG_DATE" /var/log/auth.log | grep "Failed password" | \
    awk '{print $11}' | sort | uniq -c | sort -nr | head -5

    echo "=== Disk Usage Warnings ==="
    grep "$LOG_DATE" /var/log/syslog | grep -i "disk\|space" | wc -l

    echo "=== Service Restarts ==="
    grep "$LOG_DATE" /var/log/syslog | grep "systemd" | grep "Started\|Stopped" | wc -l

} > "$REPORT_FILE"

# Email report
mail -s "Daily Log Report $(date)" admin@company.com < "$REPORT_FILE"
```

### Real-time Alert Script
```bash
#!/bin/bash
# log-monitor.sh

ALERT_EMAIL="admin@company.com"
THRESHOLD=10

while true; do
    # Check for failed logins in last minute
    FAILED_COUNT=$(grep "$(date --date='1 minute ago' +'%b %d %H:%M')" /var/log/auth.log | \
                   grep "Failed password" | wc -l)

    if [ "$FAILED_COUNT" -gt "$THRESHOLD" ]; then
        echo "ALERT: $FAILED_COUNT failed login attempts in last minute" | \
        mail -s "Security Alert: High Failed Login Count" "$ALERT_EMAIL"
    fi

    # Check for system errors
    ERROR_COUNT=$(grep "$(date +'%b %d %H:%M')" /var/log/syslog | \
                  grep -i error | wc -l)

    if [ "$ERROR_COUNT" -gt 5 ]; then
        echo "ALERT: $ERROR_COUNT system errors in last minute" | \
        mail -s "System Alert: High Error Count" "$ALERT_EMAIL"
    fi

    sleep 60
done
```

## Log Analysis with External Tools

### Using jq for JSON Logs
```bash
# Parse JSON log entries
cat /var/log/app.json | jq '.level == "error"'
cat /var/log/app.json | jq '.timestamp, .message' | head -10
cat /var/log/app.json | jq 'select(.response_time > 1000)'
```

### Using cut for CSV Logs
```bash
# Extract specific columns from CSV logs
cut -d',' -f1,3,5 /var/log/app.csv
cut -d',' -f2 /var/log/app.csv | sort | uniq -c
```

## Performance Tips

### Efficient Log Searching
```bash
# Use specific time ranges to limit search scope
awk '/2024-01-15 10:00/,/2024-01-15 11:00/' /var/log/app.log

# Search compressed logs
zgrep "error" /var/log/app.log.1.gz

# Parallel processing for large logs
cat /var/log/huge.log | parallel --pipe grep "pattern"

# Index frequently searched logs
# Consider using tools like lnav, goaccess, or ELK stack for large-scale analysis
```

### Memory-Efficient Processing
```bash
# Process large files without loading into memory
while IFS= read -r line; do
    echo "$line" | grep "pattern"
done < /var/log/large.log

# Use stream processing
tail -f /var/log/app.log | while read line; do
    echo "$line" | awk '/error/ {print "ALERT:", $0}'
done
```