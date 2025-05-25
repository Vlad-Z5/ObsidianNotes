### Basic Syntax

```promql
# Instant vector - current value
up

# Range vector - values over time
up[5m]

# Scalar - single numeric value
scalar(up)

# String - string value (rare)
```

### Selectors and Matchers

```promql
# Exact match
http_requests_total{job="api"}

# Regex match
http_requests_total{job=~"api|web"}

# Negative regex match
http_requests_total{job!~"test.*"}

# Not equal
http_requests_total{status!="200"}

# Multiple labels
http_requests_total{job="api", method="GET", status="200"}
```

### Operators and Functions

#### Arithmetic Operators

```promql
# Addition
node_memory_MemTotal_bytes + node_memory_MemFree_bytes

# Subtraction (memory usage)
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes

# Multiplication
rate(cpu_usage_seconds_total[5m]) * 100

# Division (percentage)
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100
```

#### Comparison Operators

```promql
# Greater than
node_memory_MemAvailable_bytes > 1000000000

# Less than or equal
cpu_usage_percent <= 80

# Equal
up == 1

# Not equal
up != 0
```

#### Logical Operators

```promql
# AND
up == 1 and rate(http_requests_total[5m]) > 0.1

# OR
up == 0 or rate(http_requests_total[5m]) == 0

# UNLESS (AND NOT)
up == 1 unless on(job) rate(http_requests_total[5m]) == 0
```

### Rate and Increase Functions

```promql
# Rate per second over 5 minutes
rate(http_requests_total[5m])

# Increase over 1 hour
increase(http_requests_total[1h])

# irate - instantaneous rate
irate(http_requests_total[5m])

# delta - difference
delta(cpu_temp_celsius[10m])

# idelta - instantaneous delta
idelta(cpu_temp_celsius[5m])
```

### Aggregation Functions

```promql
# Sum across all instances
sum(rate(http_requests_total[5m]))

# Sum by job
sum by (job) (rate(http_requests_total[5m]))

# Sum without specific labels
sum without (instance) (rate(http_requests_total[5m]))

# Average
avg(node_memory_MemAvailable_bytes)

# Maximum
max(node_cpu_seconds_total)

# Minimum
min(node_memory_MemFree_bytes)

# Count
count(up == 1)

# Standard deviation
stddev(response_time_seconds)

# Quantiles
quantile(0.95, response_time_seconds)
```

### Time Functions

```promql
# Current timestamp
time()

# Days since epoch
days_in_month()

# Day of month
day_of_month()

# Day of week
day_of_week()

# Hour of day
hour()

# Minute
minute()

# Month
month()

# Year
year()
```

### Advanced Functions

```promql
# Histogram quantile
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Absent - check if metric exists
absent(up{job="important-service"})

# Changes - number of times value changed
changes(up[1h])

# Deriv - derivative
deriv(cpu_temp_celsius[10m])

# Predict linear - linear prediction
predict_linear(node_memory_MemFree_bytes[1h], 3600)

# Reset - counter resets
resets(http_requests_total[1h])

# Sort
sort(sum by (job) (up))

# Sort descending
sort_desc(sum by (job) (up))

# Top K
topk(5, sum by (job) (rate(http_requests_total[5m])))

# Bottom K
bottomk(3, sum by (instance) (up))
```

### Vector Matching

```promql
# One-to-one matching
method_code:http_errors:rate5m / ignoring(code) method:http_requests:rate5m

# Many-to-one matching
method_code:http_errors:rate5m / on(method) group_left method:http_requests:rate5m

# One-to-many matching
method:http_requests:rate5m / on(method) group_right method_code:http_errors:rate5m
```
