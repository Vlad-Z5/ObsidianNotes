# Linux Cron Syntax

**Cron syntax** uses five time fields plus the command to define when jobs run.

## Basic Cron Format

```
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of week (0 - 6) (Sunday=0)
# │ │ │ │ │
# * * * * * command to execute
```

## Special Characters

- `*` - Any value (all)
- `,` - List separator (1,3,5)
- `-` - Range (1-5)
- `/` - Step values (*/5)
- `?` - No specific value (day of month OR day of week)

## Common Examples

```bash
# Every minute
* * * * * /path/to/script.sh

# Every hour at minute 0
0 * * * * /path/to/script.sh

# Every day at 2:30 AM
30 2 * * * /path/to/script.sh

# Every Monday at 9 AM
0 9 * * 1 /path/to/script.sh

# Every 15 minutes
*/15 * * * * /path/to/script.sh

# Every weekday at 6 PM
0 18 * * 1-5 /path/to/script.sh

# First day of every month at midnight
0 0 1 * * /path/to/script.sh

# Every 5 minutes between 9 AM and 5 PM on weekdays
*/5 9-17 * * 1-5 /path/to/script.sh
```

## Special Keywords

```bash
@reboot    # Run once at startup
@yearly    # Run once a year (0 0 1 1 *)
@annually  # Same as @yearly
@monthly   # Run once a month (0 0 1 * *)
@weekly    # Run once a week (0 0 * * 0)
@daily     # Run once a day (0 0 * * *)
@midnight  # Same as @daily
@hourly    # Run once an hour (0 * * * *)
```

## Examples with Keywords

```bash
@reboot /path/to/startup-script.sh
@daily /usr/local/bin/backup.sh
@weekly /usr/local/bin/cleanup.sh
@monthly /usr/local/bin/report.sh
```

## Time Calculation Tips

```bash
# To run every N minutes: */N * * * *
# To run every N hours: 0 */N * * *
# To run every N days: 0 0 */N * *

# Multiple times: 0 6,12,18 * * *  (6 AM, 12 PM, 6 PM)
# Business hours: 0 9-17 * * 1-5   (9 AM to 5 PM, Mon-Fri)
# Weekends only: 0 10 * * 6,0      (10 AM Sat and Sun)
```