## Monitoring and Troubleshooting Comprehensive Guide

### Observability Stack Architecture

#### Prometheus and Grafana Stack Setup

**Prometheus Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "*.rules"
    
    scrape_configs:
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
      
    - job_name: 'kube-state-metrics'
      static_configs:
      - targets: ['kube-state-metrics:8080']
      
    - job_name: 'node-exporter'
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        replacement: '${1}:9100'
        target_label: __address__
        
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.40.0
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus/'
          - '--web.console.libraries=/etc/prometheus/console_libraries'
          - '--web.console.templates=/etc/prometheus/consoles'
          - '--storage.tsdb.retention.time=200h'
          - '--web.enable-lifecycle'
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config-volume
          mountPath: /etc/prometheus/
        - name: prometheus-storage-volume
          mountPath: /prometheus/
      volumes:
      - name: prometheus-config-volume
        configMap:
          defaultMode: 420
          name: prometheus-config
      - name: prometheus-storage-volume
        emptyDir: {}
```

**Grafana Dashboard Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
data:
  kubernetes-cluster-dashboard.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Kubernetes Cluster Overview",
        "panels": [
          {
            "title": "CPU Usage",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) by (node)",
                "legendFormat": "{{node}}"
              }
            ]
          },
          {
            "title": "Memory Usage",
            "type": "graph", 
            "targets": [
              {
                "expr": "sum(container_memory_usage_bytes) by (node)",
                "legendFormat": "{{node}}"
              }
            ]
          }
        ]
      }
    }
```

#### Centralized Logging Architecture

**Fluentd Configuration for Log Collection:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: kube-system
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
      read_from_head true
    </source>
    
    <filter kubernetes.**>
      @type kubernetes_metadata
    </filter>
    
    <filter kubernetes.**>
      @type parser
      key_name log
      reserve_data true
      <parse>
        @type json
      </parse>
    </filter>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix kubernetes
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.system.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd-elasticsearch
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: fluentd-elasticsearch
  template:
    metadata:
      labels:
        name: fluentd-elasticsearch
    spec:
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: fluentd-elasticsearch
        image: fluent/fluentd-kubernetes-daemonset:v1.14-debian-elasticsearch7-1
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: fluentd-config
          mountPath: /fluentd/etc
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: fluentd-config
        configMap:
          name: fluentd-config
```

#### ELK Stack Integration

**Elasticsearch Configuration:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
        env:
        - name: cluster.name
          value: kubernetes-logs
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: discovery.seed_hosts
          value: "elasticsearch-0.elasticsearch,elasticsearch-1.elasticsearch,elasticsearch-2.elasticsearch"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
        - name: ES_JAVA_OPTS
          value: "-Xms1g -Xmx1g"
        ports:
        - containerPort: 9200
          name: rest
          protocol: TCP
        - containerPort: 9300
          name: inter-node
          protocol: TCP
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
```

### Performance Monitoring and Metrics

#### Custom Metrics and HPA Integration

**Custom Metrics API Configuration:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-metrics-apiserver
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: custom-metrics-apiserver
  template:
    metadata:
      labels:
        app: custom-metrics-apiserver
    spec:
      containers:
      - name: custom-metrics-apiserver
        image: k8s.gcr.io/prometheus-adapter/prometheus-adapter:v0.10.0
        args:
        - --secure-port=6443
        - --tls-cert-file=/var/run/serving-cert/tls.crt
        - --tls-private-key-file=/var/run/serving-cert/tls.key
        - --logtostderr=true
        - --prometheus-url=http://prometheus.monitoring.svc:9090/
        - --metrics-relist-interval=1m
        - --v=4
        - --config=/etc/adapter/config.yaml
        ports:
        - containerPort: 6443
        volumeMounts:
        - mountPath: /var/run/serving-cert
          name: volume-serving-cert
          readOnly: true
        - mountPath: /etc/adapter/
          name: config
          readOnly: true
      volumes:
      - name: volume-serving-cert
        secret:
          secretName: cm-adapter-serving-certs
      - name: config
        configMap:
          name: adapter-config
```

**Application Performance Monitoring:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apm-config
  namespace: monitoring
data:
  apm-server.yml: |
    apm-server:
      host: "0.0.0.0:8200"
      rum:
        enabled: true
    
    output.elasticsearch:
      hosts: ["elasticsearch.logging.svc.cluster.local:9200"]
      
    setup.kibana:
      host: "kibana.logging.svc.cluster.local:5601"
      
    logging.level: info
    logging.to_files: true
    logging.files:
      path: /var/log/apm-server
      name: apm-server
      keepfiles: 7
      permissions: 0644
```

### Health Checks and Probes Deep Dive

**Advanced Health Check Configurations:**

**Multi-Protocol Liveness Probe:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
        httpHeaders:
        - name: Custom-Header
          value: Awesome
        scheme: HTTPS
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
      successThreshold: 1
```

**TCP Socket Readiness Probe:**

```yaml
spec:
  containers:
  - name: database
    image: postgres:13
    readinessProbe:
      tcpSocket:
        port: 5432
      initialDelaySeconds: 5
      periodSeconds: 10
      timeoutSeconds: 3
      successThreshold: 1
      failureThreshold: 3
```

**Command Execution Startup Probe:**

```yaml
spec:
  containers:
  - name: app
    image: myapp:latest
    startupProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      failureThreshold: 30
      periodSeconds: 10
      timeoutSeconds: 5
```

**gRPC Health Check:**

```yaml
spec:
  containers:
  - name: grpc-service
    image: grpc-app:latest
    livenessProbe:
      grpc:
        port: 9090
        service: health  # Optional service name
      initialDelaySeconds: 10
      periodSeconds: 5
```

### Resource Monitoring and Alerting

**Comprehensive Resource Monitoring:**

```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Enhanced resource monitoring commands
kubectl top nodes --sort-by=cpu
kubectl top nodes --sort-by=memory
kubectl top pods --all-namespaces --sort-by=cpu
kubectl top pods --all-namespaces --sort-by=memory
kubectl top pods --containers --sort-by=cpu

# Advanced monitoring with custom columns
kubectl get pods --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,CPU_REQUEST:.spec.containers[0].resources.requests.cpu,MEMORY_REQUEST:.spec.containers[0].resources.requests.memory"
```

**AlertManager Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      smtp_smarthost: 'localhost:587'
      smtp_from: 'alerts@company.com'
      
    route:
      group_by: ['alertname']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
      routes:
      - match:
          severity: critical
        receiver: 'critical-alerts'
      - match:
          severity: warning
        receiver: 'warning-alerts'
        
    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://webhook-server:5000/alert'
        
    - name: 'critical-alerts'
      email_configs:
      - to: 'oncall@company.com'
        subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
      slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts-critical'
        title: 'Critical Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        
    - name: 'warning-alerts'
      email_configs:
      - to: 'team@company.com'
        subject: 'WARNING: {{ .GroupLabels.alertname }}'
```

**Prometheus Alert Rules:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: monitoring
data:
  kubernetes.rules: |
    groups:
    - name: kubernetes.rules
      rules:
      - alert: KubernetesPodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod {{ $labels.pod }} is crash looping"
          description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is crash looping"
          
      - alert: KubernetesNodeNotReady
        expr: kube_node_status_condition{condition="Ready",status="true"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Node {{ $labels.node }} is not ready"
          description: "Node {{ $labels.node }} has been not ready for more than 5 minutes"
          
      - alert: KubernetesPodNotReady
        expr: kube_pod_status_ready{condition="true"} == 0
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Pod {{ $labels.pod }} not ready"
          description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} has been not ready for more than 15 minutes"
          
      - alert: KubernetesHighCPUUsage
        expr: sum(rate(container_cpu_usage_seconds_total[5m])) by (pod) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage for pod {{ $labels.pod }}"
          description: "Pod {{ $labels.pod }} has high CPU usage (> 80%) for more than 10 minutes"
          
      - alert: KubernetesHighMemoryUsage
        expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage for pod {{ $labels.pod }}"
          description: "Pod {{ $labels.pod }} has high memory usage (> 90%) for more than 10 minutes"
```

### Debugging and Troubleshooting Techniques

#### Advanced Troubleshooting Commands

**1. Comprehensive Pod Debugging:**

```bash
# Detailed pod information
kubectl get pods -o wide
kubectl describe pod <pod-name>
kubectl get pod <pod-name> -o yaml

# Pod logs analysis
kubectl logs <pod-name> --previous
kubectl logs <pod-name> -c <container-name>
kubectl logs <pod-name> --since=1h
kubectl logs <pod-name> --tail=100 -f

# Container introspection
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec -it <pod-name> -c <container-name> -- /bin/sh

# Debug container for crashed pods
kubectl debug <pod-name> -it --image=busybox --target=<container-name>
```

**2. Network Debugging:**

```bash
# Service connectivity testing
kubectl exec -it <pod-name> -- nslookup <service-name>
kubectl exec -it <pod-name> -- curl -I <service-name>:<port>
kubectl exec -it <pod-name> -- netstat -tulpn

# Network policy testing
kubectl exec -it <pod-name> -- nc -zv <target-ip> <port>
kubectl exec -it <pod-name> -- ping <target-ip>

# DNS troubleshooting
kubectl exec -it <pod-name> -- cat /etc/resolv.conf
kubectl exec -it <pod-name> -- nslookup kubernetes.default.svc.cluster.local
```

**3. Resource and Performance Analysis:**

```bash
# Node resource analysis
kubectl describe node <node-name>
kubectl get nodes -o custom-columns="NAME:.metadata.name,CPU_CAPACITY:.status.capacity.cpu,MEMORY_CAPACITY:.status.capacity.memory"

# Pod resource consumption
kubectl top pods --sort-by=cpu --no-headers | head -10
kubectl top pods --sort-by=memory --no-headers | head -10

# Cluster resource utilization
kubectl get pods --all-namespaces -o json | jq '.items[] | select(.status.phase=="Running") | .spec.containers[] | .resources.requests'
```

#### Common Troubleshooting Scenarios

**1. ImagePullBackOff Resolution:**

```bash
# Check image details
kubectl describe pod <pod-name> | grep -A 10 Events

# Verify image exists
docker pull <image-name>

# Check image pull secrets
kubectl get secrets
kubectl describe secret <image-pull-secret>

# Test manual image pull
kubectl run test-pod --image=<image-name> --rm -it --restart=Never -- /bin/sh
```

**2. CrashLoopBackOff Analysis:**

```bash
# Check exit codes and restart counts
kubectl get pods
kubectl describe pod <pod-name>

# Analyze container logs
kubectl logs <pod-name> --previous
kubectl logs <pod-name> -c <container-name> --previous

# Check resource limits
kubectl describe pod <pod-name> | grep -A 5 Limits
kubectl describe pod <pod-name> | grep -A 5 Requests

# Debug with different command
kubectl run debug-pod --image=<same-image> --rm -it --restart=Never -- /bin/bash
```

**3. Persistent Volume Issues:**

```bash
# Check PV and PVC status
kubectl get pv,pvc
kubectl describe pv <pv-name>
kubectl describe pvc <pvc-name>

# Verify storage class
kubectl get storageclass
kubectl describe storageclass <storage-class-name>

# Check node storage
kubectl describe node <node-name> | grep -A 10 Capacity
```

#### Performance Debugging Tools

**1. Cluster Performance Analysis:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: performance-debug
spec:
  containers:
  - name: debug-tools
    image: nicolaka/netshoot
    command: ["/bin/bash"]
    args: ["-c", "while true; do sleep 30; done;"]
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
    securityContext:
      capabilities:
        add: ["NET_ADMIN", "SYS_PTRACE"]
```

**2. Network Performance Testing:**

```bash
# Inside debug pod
kubectl exec -it performance-debug -- iperf3 -c <target-service>
kubectl exec -it performance-debug -- wget -O /dev/null <service-url>
kubectl exec -it performance-debug -- curl -w "@curl-format.txt" -o /dev/null <service-url>
```

### Distributed Tracing

**Jaeger Configuration:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: tracing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:1.41
        ports:
        - containerPort: 16686
          name: ui
        - containerPort: 14268
          name: collector
        env:
        - name: COLLECTOR_ZIPKIN_HOST_PORT
          value: ":9411"
```

### Legacy Examples

**Basic Health Checks:**

```yaml
# Basic liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

# Basic readiness probe  
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

**Simple Resource Monitoring:**

```bash
kubectl top nodes
kubectl top pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

**Common Troubleshooting Steps:**

1. **Check Pod Status**: `kubectl get pods -o wide`
2. **Describe Resources**: `kubectl describe pod/service/deployment`
3. **Check Logs**: `kubectl logs pod-name --previous`
4. **Check Events**: `kubectl get events --sort-by=.metadata.creationTimestamp`
5. **Resource Usage**: `kubectl top nodes/pods`
6. **Network Debug**: `kubectl exec -it pod -- nslookup service-name`

**Common Pod Failure Reasons:**

- Image pull errors (ImagePullBackOff)
- Resource constraints (CPU/Memory limits exceeded)
- Failed health checks (CrashLoopBackOff)
- Configuration issues (ConfigMap/Secret missing)
- Network connectivity problems
