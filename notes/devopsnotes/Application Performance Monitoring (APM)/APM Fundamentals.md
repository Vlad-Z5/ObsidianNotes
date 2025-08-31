# APM Fundamentals

## APM Strategy and Implementation

#### Distributed Tracing with OpenTelemetry
```yaml
# otel/otel-collector.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: monitoring
data:
  otel-collector-config.yml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
      prometheus:
        config:
          scrape_configs:
          - job_name: 'otel-collector'
            scrape_interval: 15s
            static_configs:
            - targets: ['localhost:8888']
          - job_name: 'kubernetes-pods'
            kubernetes_sd_configs:
            - role: pod
            relabel_configs:
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
              action: keep
              regex: true
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
              action: replace
              target_label: __metrics_path__
              regex: (.+)
            - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
              action: replace
              regex: ([^:]+)(?::\d+)?;(\d+)
              replacement: $1:$2
              target_label: __address__
    
    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024
        send_batch_max_size: 2048
      memory_limiter:
        limit_mib: 512
        spike_limit_mib: 128
      resource:
        attributes:
        - key: environment
          value: production
          action: upsert
        - key: cluster
          from_attribute: k8s.cluster.name
          action: upsert
      k8sattributes:
        auth_type: "serviceAccount"
        passthrough: false
        filter:
          node_from_env_var: KUBE_NODE_NAME
        extract:
          metadata:
          - k8s.pod.name
          - k8s.pod.uid
          - k8s.deployment.name
          - k8s.namespace.name
          - k8s.node.name
          - k8s.pod.start_time
    
    exporters:
      jaeger:
        endpoint: jaeger-collector:14250
        tls:
          insecure: true
      prometheus:
        endpoint: "0.0.0.0:8889"
        const_labels:
          cluster: production
      loki:
        endpoint: http://loki:3100/loki/api/v1/push
        tenant_id: production
      zipkin:
        endpoint: http://zipkin:9411/api/v2/spans
      otlp/datadog:
        endpoint: https://api.datadoghq.com
        headers:
          "DD-API-KEY": "${DATADOG_API_KEY}"
    
    extensions:
      health_check:
        endpoint: 0.0.0.0:13133
      pprof:
        endpoint: 0.0.0.0:1777
      zpages:
        endpoint: 0.0.0.0:55679
    
    service:
      extensions: [health_check, pprof, zpages]
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, k8sattributes, resource, batch]
          exporters: [jaeger, zipkin, otlp/datadog]
        metrics:
          receivers: [otlp, prometheus]
          processors: [memory_limiter, resource, batch]
          exporters: [prometheus, otlp/datadog]
        logs:
          receivers: [otlp]
          processors: [memory_limiter, resource, batch]
          exporters: [loki]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      serviceAccountName: otel-collector
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector-contrib:0.89.0
        command:
        - "/otelcol-contrib"
        - "--config=/etc/otel-collector-config.yml"
        - "--log-level=INFO"
        volumeMounts:
        - name: otel-collector-config-vol
          mountPath: /etc
        ports:
        - containerPort: 4317   # OTLP gRPC
        - containerPort: 4318   # OTLP HTTP
        - containerPort: 8888   # Prometheus metrics
        - containerPort: 8889   # Prometheus exporter
        - containerPort: 13133  # Health check
        env:
        - name: KUBE_NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: DATADOG_API_KEY
          valueFrom:
            secretKeyRef:
              name: datadog-secret
              key: api-key
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /
            port: 13133
          initialDelaySeconds: 30
          periodSeconds: 15
        readinessProbe:
          httpGet:
            path: /
            port: 13133
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - configMap:
          name: otel-collector-config
        name: otel-collector-config-vol
---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector
  namespace: monitoring
spec:
  selector:
    app: otel-collector
  ports:
  - name: otlp-grpc
    port: 4317
    targetPort: 4317
  - name: otlp-http
    port: 4318
    targetPort: 4318
  - name: prometheus-metrics
    port: 8888
    targetPort: 8888
```

### Application Instrumentation Examples

#### Node.js Application with OpenTelemetry
```javascript
// instrumentation.js - OpenTelemetry setup for Node.js
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-http');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-otlp-http');
const { PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { RedisInstrumentation } = require('@opentelemetry/instrumentation-redis-4');
const { PgInstrumentation } = require('@opentelemetry/instrumentation-pg');

// Production APM configuration
const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: process.env.SERVICE_NAME || 'web-api',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.SERVICE_VERSION || '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.ENVIRONMENT || 'production',
    [SemanticResourceAttributes.SERVICE_INSTANCE_ID]: process.env.HOSTNAME || 'unknown',
    [SemanticResourceAttributes.K8S_POD_NAME]: process.env.K8S_POD_NAME,
    [SemanticResourceAttributes.K8S_NAMESPACE_NAME]: process.env.K8S_NAMESPACE_NAME,
    [SemanticResourceAttributes.K8S_DEPLOYMENT_NAME]: process.env.K8S_DEPLOYMENT_NAME,
  }),
  
  // Trace exporter
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT || 'http://otel-collector:4318/v1/traces',
    headers: {
      'x-service-name': process.env.SERVICE_NAME || 'web-api',
    },
  }),
  
  // Metric reader
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT || 'http://otel-collector:4318/v1/metrics',
    }),
    exportIntervalMillis: 30000, // 30 seconds
  }),
  
  // Auto-instrumentation
  instrumentations: [
    new HttpInstrumentation({
      ignoreIncomingRequestHook: (req) => {
        // Ignore health checks and internal requests
        const ignoredPaths = ['/health', '/metrics', '/ready'];
        return ignoredPaths.includes(req.url);
      },
      responseHook: (span, response) => {
        // Add response size and custom attributes
        span.setAttributes({
          'http.response.size': response.getHeader('content-length') || 0,
          'http.response.content_type': response.getHeader('content-type'),
        });
      },
    }),
    
    new ExpressInstrumentation({
      spanNameHook: (info) => {
        // Custom span names for better organization
        return `${info.request.method} ${info.route || 'unknown'}`;
      },
    }),
    
    new RedisInstrumentation({
      dbStatementSerializer: (cmdName, cmdArgs) => {
        // Sanitize Redis commands for security
        if (cmdName.toLowerCase() === 'auth') {
          return 'auth [REDACTED]';
        }
        return `${cmdName} ${cmdArgs.slice(0, 3).join(' ')}${cmdArgs.length > 3 ? ' ...' : ''}`;
      },
    }),
    
    new PgInstrumentation({
      enhancedDatabaseReporting: true,
    }),
  ],
});

// Initialize the SDK
sdk.start();

// Graceful shutdown
process.on('SIGTERM', () => {
  sdk.shutdown()
    .then(() => console.log('OpenTelemetry terminated'))
    .catch((error) => console.error('Error terminating OpenTelemetry', error))
    .finally(() => process.exit(0));
});

console.log('OpenTelemetry started successfully');
```

#### Production Express.js Application with Custom Metrics
```javascript
// app.js - Production Express app with APM integration
const express = require('express');
const { trace, metrics } = require('@opentelemetry/api');
const { Counter, Histogram } = require('@opentelemetry/api-metrics');

const app = express();

// Get tracer and meter instances
const tracer = trace.getTracer('web-api', '1.0.0');
const meter = metrics.getMeter('web-api', '1.0.0');

// Custom metrics
const httpRequestsTotal = meter.createCounter('http_requests_total', {
  description: 'Total number of HTTP requests',
});

const httpRequestDuration = meter.createHistogram('http_request_duration_seconds', {
  description: 'HTTP request duration in seconds',
  unit: 's',
});

const businessMetrics = meter.createCounter('business_operations_total', {
  description: 'Total number of business operations',
});

// Middleware for custom metrics and tracing
app.use((req, res, next) => {
  const startTime = Date.now();
  
  // Increment request counter
  httpRequestsTotal.add(1, {
    method: req.method,
    route: req.route?.path || req.path,
    status_code: res.statusCode.toString(),
  });
  
  // Track request duration
  res.on('finish', () => {
    const duration = (Date.now() - startTime) / 1000;
    httpRequestDuration.record(duration, {
      method: req.method,
      route: req.route?.path || req.path,
      status_code: res.statusCode.toString(),
    });
  });
  
  next();
});

// API endpoints with custom tracing
app.get('/api/users/:id', async (req, res) => {
  const span = tracer.startSpan('get_user');
  
  try {
    const userId = req.params.id;
    
    // Add custom attributes to span
    span.setAttributes({
      'user.id': userId,
      'operation.type': 'user_lookup',
    });
    
    // Simulate user lookup with child span
    const user = await getUserById(userId);
    
    if (!user) {
      span.recordException(new Error('User not found'));
      span.setStatus({ code: trace.SpanStatusCode.ERROR, message: 'User not found' });
      return res.status(404).json({ error: 'User not found' });
    }
    
    // Record business metric
    businessMetrics.add(1, {
      operation: 'user_lookup',
      status: 'success',
    });
    
    span.setStatus({ code: trace.SpanStatusCode.OK });
    res.json(user);
    
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: trace.SpanStatusCode.ERROR, message: error.message });
    
    businessMetrics.add(1, {
      operation: 'user_lookup',
      status: 'error',
    });
    
    console.error('Error fetching user:', error);
    res.status(500).json({ error: 'Internal server error' });
  } finally {
    span.end();
  }
});

// Async operation with tracing
async function getUserById(userId) {
  const span = tracer.startSpan('database_query', {
    attributes: {
      'db.operation': 'SELECT',
      'db.sql.table': 'users',
    },
  });
  
  try {
    // Simulate database query
    await new Promise(resolve => setTimeout(resolve, Math.random() * 100));
    
    if (userId === '404') {
      return null; // Simulate not found
    }
    
    const user = {
      id: userId,
      name: `User ${userId}`,
      email: `user${userId}@example.com`,
    };
    
    span.setAttributes({
      'db.rows_affected': 1,
    });
    
    return user;
  } finally {
    span.end();
  }
}

// Error handling middleware with tracing
app.use((error, req, res, next) => {
  const span = trace.getActiveSpan();
  if (span) {
    span.recordException(error);
    span.setStatus({ code: trace.SpanStatusCode.ERROR, message: error.message });
  }
  
  businessMetrics.add(1, {
    operation: 'error_handler',
    error_type: error.constructor.name,
  });
  
  console.error('Unhandled error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

module.exports = app;
```

### APM Monitoring and Alerting Script

```bash
#!/bin/bash
# scripts/apm-monitoring.sh - Production APM monitoring and alerting

set -euo pipefail

readonly JAEGER_ENDPOINT="http://jaeger-query:16686"
readonly PROMETHEUS_ENDPOINT="http://prometheus:9090"
readonly GRAFANA_ENDPOINT="http://grafana:3000"
readonly SERVICE_NAME="web-api"
readonly ENVIRONMENT="production"

log_info() { echo -e "[$(date '+%H:%M:%S')] INFO: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] SUCCESS: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] WARN: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ERROR: $*"; }

# Monitor trace metrics and performance
monitor_trace_metrics() {
    local duration="${1:-300}"  # 5 minutes default
    
    log_info "Monitoring trace metrics for ${duration}s..."
    
    local end_time=$(($(date +%s) + duration))
    local check_interval=30
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Get trace statistics from Jaeger
        local traces_count error_rate avg_duration
        
        # Query Jaeger API for recent traces
        local jaeger_response
        jaeger_response=$(curl -s "${JAEGER_ENDPOINT}/api/traces" \
                         -G \
                         -d "service=${SERVICE_NAME}" \
                         -d "lookback=5m" \
                         -d "limit=100" || echo '{"data": []}')
        
        traces_count=$(echo "$jaeger_response" | jq '.data | length' 2>/dev/null || echo "0")
        
        # Calculate error rate from traces
        local error_traces
        error_traces=$(echo "$jaeger_response" | \
                      jq '[.data[] | select(.spans[] | .tags[] | select(.key=="error" and .value==true))] | length' 2>/dev/null || echo "0")
        
        if [[ "$traces_count" -gt 0 ]]; then
            error_rate=$(echo "scale=2; $error_traces * 100 / $traces_count" | bc)
        else
            error_rate=0
        fi
        
        # Calculate average duration
        local total_duration=0
        if [[ "$traces_count" -gt 0 ]]; then
            avg_duration=$(echo "$jaeger_response" | \
                          jq '[.data[] | .spans[] | select(.operationName=="http_request") | .duration] | add / length' 2>/dev/null || echo "0")
            avg_duration=$(echo "scale=2; $avg_duration / 1000" | bc)  # Convert to ms
        else
            avg_duration=0
        fi
        
        log_info "Trace Metrics: Count=$traces_count, ErrorRate=${error_rate}%, AvgDuration=${avg_duration}ms"
        
        # Check for high error rate
        if (( $(echo "$error_rate > 5.0" | bc -l) )); then
            log_warn "High error rate detected in traces: ${error_rate}%"
            send_apm_alert "HIGH_ERROR_RATE" "Error rate: ${error_rate}%" "traces"
        fi
        
        # Check for high latency
        if (( $(echo "$avg_duration > 2000" | bc -l) )); then
            log_warn "High latency detected: ${avg_duration}ms"
            send_apm_alert "HIGH_LATENCY" "Average duration: ${avg_duration}ms" "performance"
        fi
        
        sleep $check_interval
    done
}

# Monitor application metrics from Prometheus
monitor_application_metrics() {
    local duration="${1:-300}"
    
    log_info "Monitoring application metrics for ${duration}s..."
    
    local end_time=$(($(date +%s) + duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Query Prometheus metrics
        local request_rate error_rate p95_latency cpu_usage memory_usage
        
        # Request rate (requests per second)
        request_rate=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                      --data-urlencode "query=rate(http_requests_total{service=\"${SERVICE_NAME}\"}[5m])" | \
                      jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        # Error rate percentage
        error_rate=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                    --data-urlencode "query=rate(http_requests_total{service=\"${SERVICE_NAME}\",status_code=~\"5..\"}[5m]) / rate(http_requests_total{service=\"${SERVICE_NAME}\"}[5m]) * 100" | \
                    jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        # P95 latency
        p95_latency=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                     --data-urlencode "query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"${SERVICE_NAME}\"}[5m])) * 1000" | \
                     jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        # CPU usage
        cpu_usage=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                   --data-urlencode "query=avg(rate(container_cpu_usage_seconds_total{pod=~\"${SERVICE_NAME}.*\"}[5m])) * 100" | \
                   jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        # Memory usage
        memory_usage=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                      --data-urlencode "query=avg(container_memory_usage_bytes{pod=~\"${SERVICE_NAME}.*\"}) / 1024 / 1024" | \
                      jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        log_info "App Metrics: RPS=${request_rate}, ErrorRate=${error_rate}%, P95=${p95_latency}ms, CPU=${cpu_usage}%, Mem=${memory_usage}MB"
        
        # Check thresholds and alert
        if (( $(echo "$error_rate > 2.0" | bc -l) )); then
            log_warn "High application error rate: ${error_rate}%"
            send_apm_alert "HIGH_APP_ERROR_RATE" "Error rate: ${error_rate}%" "application"
        fi
        
        if (( $(echo "$p95_latency > 1000" | bc -l) )); then
            log_warn "High P95 latency: ${p95_latency}ms"
            send_apm_alert "HIGH_P95_LATENCY" "P95 latency: ${p95_latency}ms" "performance"
        fi
        
        if (( $(echo "$cpu_usage > 80.0" | bc -l) )); then
            log_warn "High CPU usage: ${cpu_usage}%"
            send_apm_alert "HIGH_CPU_USAGE" "CPU usage: ${cpu_usage}%" "resources"
        fi
        
        sleep 30
    done
}

# Analyze trace performance patterns
analyze_trace_patterns() {
    local lookback="${1:-1h}"
    
    log_info "Analyzing trace patterns for last $lookback..."
    
    # Get traces from Jaeger
    local jaeger_response
    jaeger_response=$(curl -s "${JAEGER_ENDPOINT}/api/traces" \
                     -G \
                     -d "service=${SERVICE_NAME}" \
                     -d "lookback=${lookback}" \
                     -d "limit=1000")
    
    # Analyze operations
    local operations
    operations=$(echo "$jaeger_response" | jq -r '.data[].spans[].operationName' | sort | uniq -c | sort -nr)
    
    log_info "Top Operations by Volume:"
    echo "$operations" | head -10
    
    # Analyze errors
    local error_operations
    error_operations=$(echo "$jaeger_response" | \
                      jq -r '.data[] | select(.spans[] | .tags[] | select(.key=="error" and .value==true)) | .spans[0].operationName' | \
                      sort | uniq -c | sort -nr)
    
    if [[ -n "$error_operations" ]]; then
        log_warn "Operations with Errors:"
        echo "$error_operations" | head -5
    fi
    
    # Analyze slow operations
    local slow_operations
    slow_operations=$(echo "$jaeger_response" | \
                     jq -r '.data[] | select(.spans[0].duration > 2000000) | "\(.spans[0].operationName) \(.spans[0].duration)"' | \
                     sort -k2 -nr | head -10)
    
    if [[ -n "$slow_operations" ]]; then
        log_warn "Slowest Operations (>2s):"
        echo "$slow_operations"
    fi
}

# Check service dependencies health
check_service_dependencies() {
    log_info "Checking service dependencies health..."
    
    local dependencies=("database" "redis" "external-api")
    local unhealthy_deps=()
    
    for dep in "${dependencies[@]}"; do
        # Query dependency metrics
        local dep_error_rate
        dep_error_rate=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                        --data-urlencode "query=rate(dependency_calls_total{service=\"${SERVICE_NAME}\",dependency=\"${dep}\",status=\"error\"}[5m]) / rate(dependency_calls_total{service=\"${SERVICE_NAME}\",dependency=\"${dep}\"}[5m]) * 100" | \
                        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        local dep_latency
        dep_latency=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                     --data-urlencode "query=histogram_quantile(0.95, rate(dependency_duration_seconds_bucket{service=\"${SERVICE_NAME}\",dependency=\"${dep}\"}[5m])) * 1000" | \
                     jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        log_info "Dependency $dep: ErrorRate=${dep_error_rate}%, P95Latency=${dep_latency}ms"
        
        # Check if dependency is unhealthy
        if (( $(echo "$dep_error_rate > 5.0" | bc -l) )) || (( $(echo "$dep_latency > 5000" | bc -l) )); then
            unhealthy_deps+=("$dep (ErrorRate: ${dep_error_rate}%, Latency: ${dep_latency}ms)")
        fi
    done
    
    if [[ ${#unhealthy_deps[@]} -gt 0 ]]; then
        log_warn "Unhealthy dependencies detected:"
        printf '%s\n' "${unhealthy_deps[@]}"
        send_apm_alert "UNHEALTHY_DEPENDENCIES" "Dependencies: $(IFS=', '; echo "${unhealthy_deps[*]}")" "dependencies"
    else
        log_success "All dependencies healthy"
    fi
}

# Generate APM performance report
generate_apm_report() {
    local output_file="/tmp/apm-report-$(date +%Y%m%d_%H%M%S).json"
    
    log_info "Generating APM performance report..."
    
    # Gather metrics for report
    local current_metrics
    current_metrics=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                     --data-urlencode "query=rate(http_requests_total{service=\"${SERVICE_NAME}\"}[5m])")
    
    local error_metrics
    error_metrics=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                   --data-urlencode "query=rate(http_requests_total{service=\"${SERVICE_NAME}\",status_code=~\"5..\"}[5m])")
    
    local latency_metrics
    latency_metrics=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                     --data-urlencode "query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"${SERVICE_NAME}\"}[5m]))")
    
    # Create report JSON
    cat > "$output_file" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
  "service": "${SERVICE_NAME}",
  "environment": "${ENVIRONMENT}",
  "metrics": {
    "request_rate": $(echo "$current_metrics" | jq '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0"),
    "error_rate": $(echo "$error_metrics" | jq '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0"),
    "p95_latency": $(echo "$latency_metrics" | jq '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
  },
  "health_status": "$(check_overall_health)",
  "generated_by": "apm-monitoring-script"
}
EOF
    
    log_info "APM report generated: $output_file"
    
    # Send to monitoring system if configured
    if [[ -n "${APM_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H "Content-Type: application/json" \
             -d "@$output_file" \
             "$APM_WEBHOOK_URL" || log_warn "Failed to send APM report to webhook"
    fi
}

# Check overall application health
check_overall_health() {
    local health_status="healthy"
    
    # Check if any critical metrics are above thresholds
    local error_rate
    error_rate=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                --data-urlencode "query=rate(http_requests_total{service=\"${SERVICE_NAME}\",status_code=~\"5..\"}[5m]) / rate(http_requests_total{service=\"${SERVICE_NAME}\"}[5m]) * 100" | \
                jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    if (( $(echo "$error_rate > 5.0" | bc -l) )); then
        health_status="degraded"
    fi
    
    local p95_latency
    p95_latency=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
                 --data-urlencode "query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"${SERVICE_NAME}\"}[5m]))" | \
                 jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    if (( $(echo "$p95_latency > 2.0" | bc -l) )); then
        health_status="degraded"
    fi
    
    echo "$health_status"
}

# Send APM alerts
send_apm_alert() {
    local alert_type="$1"
    local details="$2"
    local category="$3"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="warning"
        local icon="⚠️"
        
        case "$alert_type" in
            "HIGH_ERROR_RATE"|"HIGH_APP_ERROR_RATE")
                color="danger"
                icon="🚨"
                ;;
            "UNHEALTHY_DEPENDENCIES")
                color="danger"
                icon="💥"
                ;;
        esac
        
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "$icon APM Alert: $SERVICE_NAME",
            "fields": [
                {
                    "title": "Alert Type",
                    "value": "$alert_type",
                    "short": true
                },
                {
                    "title": "Category", 
                    "value": "$category",
                    "short": true
                },
                {
                    "title": "Details",
                    "value": "$details",
                    "short": false
                },
                {
                    "title": "Service",
                    "value": "$SERVICE_NAME ($ENVIRONMENT)",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date)",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
    
    # Send to PagerDuty for critical alerts
    if [[ "$alert_type" =~ ^(HIGH_ERROR_RATE|HIGH_APP_ERROR_RATE|UNHEALTHY_DEPENDENCIES)$ ]] && [[ -n "${PAGERDUTY_INTEGRATION_KEY:-}" ]]; then
        local pd_payload=$(cat <<EOF
{
  "routing_key": "$PAGERDUTY_INTEGRATION_KEY",
  "event_action": "trigger",
  "payload": {
    "summary": "APM Alert: $alert_type - $SERVICE_NAME",
    "source": "apm-monitoring",
    "severity": "critical",
    "component": "$SERVICE_NAME",
    "group": "$category",
    "custom_details": {
      "alert_type": "$alert_type",
      "details": "$details",
      "service": "$SERVICE_NAME",
      "environment": "$ENVIRONMENT"
    }
  }
}
EOF
)
        
        curl -X POST -H "Content-Type: application/json" \
             -d "$pd_payload" \
             "https://events.pagerduty.com/v2/enqueue" >/dev/null 2>&1 || true
    fi
}

# Main function
main() {
    local command="${1:-monitor}"
    local duration="${2:-300}"
    
    case "$command" in
        "monitor-traces")
            monitor_trace_metrics "$duration"
            ;;
        "monitor-metrics")
            monitor_application_metrics "$duration"
            ;;
        "analyze-patterns")
            analyze_trace_patterns "${2:-1h}"
            ;;
        "check-dependencies")
            check_service_dependencies
            ;;
        "generate-report")
            generate_apm_report
            ;;
        "full-monitor")
            log_info "Starting comprehensive APM monitoring..."
            
            # Run all monitoring tasks in parallel
            monitor_trace_metrics "$duration" &
            monitor_application_metrics "$duration" &
            
            # Run dependency check every 2 minutes
            while [[ $duration -gt 0 ]]; do
                check_service_dependencies
                sleep 120  # 2 minutes
                duration=$((duration - 120))
            done
            
            wait  # Wait for background monitoring to complete
            
            # Generate final report
            generate_apm_report
            ;;
        *)
            cat <<EOF
APM Monitoring Tool

Usage: $0 <command> [options]

Commands:
  monitor-traces [duration]       - Monitor distributed tracing metrics
  monitor-metrics [duration]      - Monitor application performance metrics
  analyze-patterns [lookback]     - Analyze trace patterns (default: 1h)
  check-dependencies             - Check service dependencies health
  generate-report                - Generate APM performance report
  full-monitor [duration]        - Run comprehensive APM monitoring

Examples:
  $0 monitor-traces 600
  $0 monitor-metrics 300
  $0 analyze-patterns 2h
  $0 check-dependencies
  $0 full-monitor 900

Environment Variables:
  SLACK_WEBHOOK_URL         - Slack webhook for alerts
  PAGERDUTY_INTEGRATION_KEY - PagerDuty integration key
  APM_WEBHOOK_URL          - Custom webhook for reports
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive APM implementation with OpenTelemetry, distributed tracing, custom metrics, performance monitoring, and automated alerting for production applications.