# Linux At Command

**At command** schedules one-time jobs to run at a specific time in the future.

## Basic At Usage

```bash
# Schedule a job for specific time
at 2:30 PM
at> echo "Hello World" > /tmp/hello.txt
at>

To See what's in the queue, Type Ctrl-D

# Alternative ways to specify time
at now + 5 minutes
at tomorrow
at 3:00 AM tomorrow
at 4:00 PM + 2 days
at 10:00 AM next Monday
```

## Time Formats

```bash
# Absolute times
at 14:30                    # 2:30 PM today
at 2:30 PM                  # 2:30 PM today
at 23:59                    # 11:59 PM today

# Relative times
at now + 30 minutes
at now + 2 hours
at now + 1 day
at now + 1 week

# Date specifications
at 2:30 PM Dec 25
at 09:00 AM tomorrow
at 14:30 next Friday
at midnight next week
```

## Managing At Jobs

```bash
# List scheduled jobs
atq
at -l

# Remove job by number
atrm 2
at -r 2

# Remove all jobs
atrm $(atq | cut -f1)

# View job details
at -c 2
```

## Practical Examples

### Schedule Immediate Tasks

```bash
# Run command in 5 minutes
echo "ls -la /tmp" | at now + 5 minutes

# Shutdown system in 1 hour
echo "shutdown -h now" | at now + 1 hour

# Send reminder email tomorrow
at 9:00 AM tomorrow
at> echo "Team meeting at 10 AM" | mail -s "Reminder" user@company.com
at>
```

### Using Scripts with At

```bash
# Schedule script execution
at midnight
at> /usr/local/bin/cleanup.sh
at>

# Schedule with input redirection
at 2:00 AM < script_commands.txt

# Schedule complex commands
at 3:00 PM Friday
at> cd /opt/backup && ./backup.sh --full
at>
```

### Batch Processing

```bash
# Use batch command for system idle time
batch
batch> find / -name "*.tmp" -delete
batch>

# Schedule when load average is low
echo "heavy-processing-script.sh" | batch
```

## At with Files

```bash
# Create command file
cat > cleanup_commands.txt <<EOF
cd /tmp
rm -rf old_files/*
echo "Cleanup completed at $(date)" >> /var/log/cleanup.log
EOF

# Schedule the file
at midnight < cleanup_commands.txt
```

## Environment in At Jobs

```bash
# At inherits current environment
export BACKUP_DIR=/opt/backup
at 2:00 AM
at> echo "Backing up to $BACKUP_DIR"
at>

# Explicitly set environment in job
at midnight
at> export PATH=/usr/local/bin:$PATH
at> /usr/local/bin/special-script.sh
at>
```

## At Service Management

```bash
# Check if atd is running
systemctl status atd

# Start atd service
sudo systemctl start atd
sudo systemctl enable atd

# Check at daemon process
ps aux | grep atd
```

## Access Control

```bash
# Allow specific users to use at
echo "username" | sudo tee -a /etc/at.allow

# Deny specific users from using at
echo "username" | sudo tee -a /etc/at.deny

# Check at permissions
ls -la /etc/at.allow /etc/at.deny
```

## Debugging At Jobs

```bash
# Check at logs
tail -f /var/log/syslog | grep atd

# View job output
# At jobs mail output to user by default
mail

# Redirect output to file
at midnight
at> /path/to/script.sh > /tmp/output.log 2>&1
at>
```

## Advanced Usage

### Conditional Execution

```bash
at 3:00 AM
at> if [ -f /tmp/proceed ]; then /usr/local/bin/maintenance.sh; fi
at>

# With timeout
at now + 30 minutes
at> timeout 300 /usr/local/bin/long-running-task.sh || echo "Task timed out"
at>
```

### Chaining At Jobs

```bash
# Schedule follow-up job
at midnight
at> /usr/local/bin/backup.sh && echo "/usr/local/bin/verify.sh" | at now + 1 hour
at>
```

### At vs Cron Decision

**Use At when:**
- One-time execution needed
- Scheduling ad-hoc tasks
- User-initiated delayed tasks
- Dynamic scheduling based on events

**Use Cron when:**
- Recurring tasks
- System maintenance
- Regular backups
- Automated monitoring

## Quick Reference

```bash
# Schedule job
at TIME
# Enter commands
# Press Ctrl-D

# List jobs: atq
# Remove job: atrm JOB_NUMBER
# View job: at -c JOB_NUMBER
# Check service: systemctl status atd
```