# Pod Manifests

## Overview

A **Pod** is the smallest deployable unit in Kubernetes. It represents one or more containers that share network and storage resources. Pods are ephemeral and typically managed by higher-level controllers (Deployments, StatefulSets, etc.).

## Basic Pod Structure

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  namespace: default
  labels:
    app: myapp
    environment: production
  annotations:
    description: "Example pod manifest"
spec:
  containers:
  - name: main-container
    image: nginx:1.25
    ports:
    - containerPort: 80
```

## Complete Pod Manifest with All Options

```yaml
apiVersion: v1
kind: Pod
metadata:
  # ==================== Metadata ====================
  name: comprehensive-pod
  namespace: production

  labels:
    app: web-server
    version: v2.1.0
    environment: production
    tier: frontend
    team: platform

  annotations:
    description: "Production web server pod"
    owner: "platform-team@company.com"
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"

spec:
  # ==================== Container Specifications ====================
  containers:
  - name: nginx
    image: nginx:1.25-alpine
    imagePullPolicy: IfNotPresent  # Always, Never, IfNotPresent

    # Command and arguments
    command: ["/bin/sh"]
    args: ["-c", "nginx -g 'daemon off;'"]

    # Working directory
    workingDir: /app

    # Ports
    ports:
    - name: http
      containerPort: 80
      protocol: TCP
    - name: https
      containerPort: 443
      protocol: TCP
    - name: metrics
      containerPort: 9090
      protocol: TCP

    # Environment variables
    env:
    - name: ENVIRONMENT
      value: "production"
    - name: LOG_LEVEL
      value: "info"
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: POD_IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName
    - name: CPU_REQUEST
      valueFrom:
        resourceFieldRef:
          containerName: nginx
          resource: requests.cpu
    - name: MEMORY_LIMIT
      valueFrom:
        resourceFieldRef:
          containerName: nginx
          resource: limits.memory

    # Environment from ConfigMap/Secret
    envFrom:
    - configMapRef:
        name: app-config
    - secretRef:
        name: app-secrets
        optional: true
    - prefix: DB_
      configMapRef:
        name: database-config

    # Resource requests and limits
    resources:
      requests:
        cpu: 250m
        memory: 256Mi
        ephemeral-storage: 1Gi
      limits:
        cpu: 1000m
        memory: 1Gi
        ephemeral-storage: 5Gi

    # Volume mounts
    volumeMounts:
    - name: config-volume
      mountPath: /etc/nginx/nginx.conf
      subPath: nginx.conf
      readOnly: true
    - name: data-volume
      mountPath: /usr/share/nginx/html
    - name: cache-volume
      mountPath: /var/cache/nginx
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
    - name: logs-volume
      mountPath: /var/log/nginx

    # Liveness probe
    livenessProbe:
      httpGet:
        path: /healthz
        port: 80
        httpHeaders:
        - name: X-Custom-Header
          value: Awesome
        scheme: HTTP
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      successThreshold: 1
      failureThreshold: 3

    # Readiness probe
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      successThreshold: 1
      failureThreshold: 3

    # Startup probe (for slow-starting containers)
    startupProbe:
      httpGet:
        path: /startup
        port: 80
      initialDelaySeconds: 0
      periodSeconds: 10
      timeoutSeconds: 3
      successThreshold: 1
      failureThreshold: 30  # 5 minutes max startup time

    # Lifecycle hooks
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "echo 'Container started' > /var/log/startup.log"]
      preStop:
        exec:
          command: ["/bin/sh", "-c", "nginx -s quit; sleep 15"]

    # Security context (container-level)
    securityContext:
      runAsUser: 1000
      runAsGroup: 3000
      runAsNonRoot: true
      readOnlyRootFilesystem: false
      allowPrivilegeEscalation: false
      capabilities:
        add:
        - NET_BIND_SERVICE
        drop:
        - ALL
      seLinuxOptions:
        level: "s0:c123,c456"
      seccompProfile:
        type: RuntimeDefault

    # stdin/tty for interactive containers
    stdin: false
    stdinOnce: false
    tty: false

    # Terminal settings
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File  # File or FallbackToLogsOnError

  # ==================== Init Containers ====================
  initContainers:
  - name: wait-for-db
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      until nslookup postgres-service; do
        echo "Waiting for database..."
        sleep 2
      done
      echo "Database is available!"
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 100m
        memory: 128Mi

  - name: setup-permissions
    image: busybox:1.36
    command: ["sh", "-c", "chown -R 1000:3000 /data"]
    volumeMounts:
    - name: data-volume
      mountPath: /data
    securityContext:
      runAsUser: 0  # Run as root for permission setup

  - name: fetch-config
    image: curlimages/curl:latest
    command:
    - sh
    - -c
    - |
      curl -o /config/app-config.json \
        http://config-service/api/v1/config
    volumeMounts:
    - name: config-volume
      mountPath: /config

  # ==================== Ephemeral Containers (for debugging) ====================
  # Note: Added dynamically via kubectl debug, not in initial manifest

  # ==================== Volumes ====================
  volumes:
  - name: config-volume
    configMap:
      name: nginx-config
      items:
      - key: nginx.conf
        path: nginx.conf
      defaultMode: 0644

  - name: data-volume
    persistentVolumeClaim:
      claimName: web-data-pvc

  - name: cache-volume
    emptyDir:
      sizeLimit: 1Gi
      medium: ""  # "" for disk, "Memory" for tmpfs

  - name: secret-volume
    secret:
      secretName: app-secrets
      items:
      - key: tls.crt
        path: tls.crt
      - key: tls.key
        path: tls.key
      defaultMode: 0400
      optional: false

  - name: logs-volume
    hostPath:
      path: /var/log/nginx
      type: DirectoryOrCreate

  - name: downward-api-volume
    downwardAPI:
      items:
      - path: "labels"
        fieldRef:
          fieldPath: metadata.labels
      - path: "annotations"
        fieldRef:
          fieldPath: metadata.annotations
      - path: "cpu-limit"
        resourceFieldRef:
          containerName: nginx
          resource: limits.cpu

  - name: projected-volume
    projected:
      sources:
      - configMap:
          name: config1
      - secret:
          name: secret1
      - downwardAPI:
          items:
          - path: "namespace"
            fieldRef:
              fieldPath: metadata.namespace
      - serviceAccountToken:
          audience: api
          expirationSeconds: 3600
          path: token

  # ==================== Image Pull Secrets ====================
  imagePullSecrets:
  - name: registry-credentials
  - name: dockerhub-credentials

  # ==================== Scheduling ====================
  # Node selection
  nodeSelector:
    disktype: ssd
    environment: production

  # Node name (manual scheduling)
  # nodeName: worker-node-1

  # Node affinity
  affinity:
    nodeAffinity:
      # Required rules (hard constraint)
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/arch
            operator: In
            values:
            - amd64
            - arm64
          - key: node-role.kubernetes.io/worker
            operator: Exists

      # Preferred rules (soft constraint)
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        preference:
          matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values:
            - us-east-1a
      - weight: 20
        preference:
          matchExpressions:
          - key: instance-type
            operator: In
            values:
            - c5.2xlarge

    # Pod affinity (co-locate with other pods)
    podAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: database
          topologyKey: kubernetes.io/hostname

    # Pod anti-affinity (spread across nodes/zones)
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: web-server
        topologyKey: kubernetes.io/hostname

      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: web-server
          topologyKey: topology.kubernetes.io/zone

  # Tolerations
  tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
  - key: dedicated
    operator: Equal
    value: web-servers
    effect: NoSchedule
  - key: node.kubernetes.io/not-ready
    operator: Exists
    effect: NoExecute
    tolerationSeconds: 300
  - key: node.kubernetes.io/unreachable
    operator: Exists
    effect: NoExecute
    tolerationSeconds: 300

  # Topology spread constraints
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: web-server
  - maxSkew: 2
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app: web-server

  # ==================== Security ====================
  # Security context (pod-level)
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    runAsNonRoot: true
    fsGroup: 2000
    fsGroupChangePolicy: OnRootMismatch
    supplementalGroups: [4000, 5000]
    seLinuxOptions:
      level: "s0:c123,c456"
    seccompProfile:
      type: RuntimeDefault
    sysctls:
    - name: net.ipv4.ip_local_port_range
      value: "1024 65535"
    - name: kernel.shm_rmid_forced
      value: "1"

  # Service account
  serviceAccountName: web-server-sa
  automountServiceAccountToken: true

  # ==================== DNS ====================
  dnsPolicy: ClusterFirst  # ClusterFirst, Default, ClusterFirstWithHostNet, None
  dnsConfig:
    nameservers:
    - 8.8.8.8
    searches:
    - my-namespace.svc.cluster.local
    - svc.cluster.local
    - cluster.local
    options:
    - name: ndots
      value: "2"
    - name: edns0

  hostname: web-server
  subdomain: production
  setHostnameAsFQDN: false

  # ==================== Networking ====================
  hostNetwork: false
  hostPID: false
  hostIPC: false
  shareProcessNamespace: false

  hostAliases:
  - ip: "192.168.1.100"
    hostnames:
    - "db.example.com"
    - "database.example.com"

  # ==================== Lifecycle ====================
  restartPolicy: Always  # Always, OnFailure, Never
  terminationGracePeriodSeconds: 30
  activeDeadlineSeconds: 3600  # Pod timeout (1 hour)

  # ==================== Priority ====================
  priorityClassName: high-priority
  priority: 1000

  # ==================== Other Settings ====================
  enableServiceLinks: true
  preemptionPolicy: PreemptLowerPriority  # Never, PreemptLowerPriority

  # Overhead (for kata containers, gVisor, etc.)
  overhead:
    cpu: 250m
    memory: 120Mi

  # Resource claims (for dynamic resource allocation)
  resourceClaims:
  - name: gpu-claim
    source:
      resourceClaimName: gpu-resource-claim

  # Scheduler name
  schedulerName: default-scheduler

  # Runtime class
  runtimeClassName: nvidia  # For GPU, kata-containers, gVisor, etc.
```

## Common Pod Patterns

### 1. Simple Single-Container Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
```

### 2. Multi-Container Pod (Sidecar Pattern)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-logging
spec:
  containers:
  # Main application container
  - name: web-app
    image: myapp:v1
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/app

  # Logging sidecar
  - name: log-forwarder
    image: fluent/fluent-bit:2.0
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/app
      readOnly: true

  volumes:
  - name: app-logs
    emptyDir: {}
```

### 3. Pod with Init Container

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-init
spec:
  initContainers:
  - name: init-db
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      until nc -z postgres-service 5432; do
        echo "Waiting for database..."
        sleep 2
      done

  containers:
  - name: app
    image: myapp:v1
    env:
    - name: DB_HOST
      value: postgres-service
```

### 4. Pod with Resource Limits

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-limited-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
```

### 5. Pod with Health Probes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: healthy-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    ports:
    - containerPort: 8080

    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      failureThreshold: 3

    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 1

    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      periodSeconds: 10
      failureThreshold: 30
```

### 6. Pod with Secrets and ConfigMaps

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    env:
    - name: CONFIG_VAR
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: config.value
    - name: SECRET_VAR
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: password
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true

  volumes:
  - name: config-volume
    configMap:
      name: app-config
  - name: secret-volume
    secret:
      secretName: app-secret
```

### 7. Privileged Pod (System Workload)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  hostNetwork: true
  hostPID: true
  containers:
  - name: system-tool
    image: system-tools:latest
    securityContext:
      privileged: true
      capabilities:
        add:
        - SYS_ADMIN
        - NET_ADMIN
    volumeMounts:
    - name: host-root
      mountPath: /host
      readOnly: true

  volumes:
  - name: host-root
    hostPath:
      path: /
      type: Directory
```

### 8. Pod with Affinity Rules

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd

    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: myapp
        topologyKey: kubernetes.io/hostname

  containers:
  - name: app
    image: myapp:v1
```

## Advanced Use Cases

### GPU Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  runtimeClassName: nvidia
  containers:
  - name: cuda-app
    image: nvidia/cuda:11.8.0-base
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 2
```

### Pod with Huge Pages

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hugepages-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        memory: 8Gi
        hugepages-2Mi: 4Gi
      limits:
        memory: 8Gi
        hugepages-2Mi: 4Gi
    volumeMounts:
    - name: hugepage-2mi
      mountPath: /hugepages-2Mi

  volumes:
  - name: hugepage-2mi
    emptyDir:
      medium: HugePages-2Mi
```

### Pod with Service Account Token Projection

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sa-token-pod
spec:
  serviceAccountName: myapp-sa
  containers:
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: sa-token
      mountPath: /var/run/secrets/tokens
      readOnly: true

  volumes:
  - name: sa-token
    projected:
      sources:
      - serviceAccountToken:
          audience: api
          expirationSeconds: 3600
          path: token
```

### Pod with Ephemeral Containers (Debugging)

```yaml
# Original pod
apiVersion: v1
kind: Pod
metadata:
  name: production-app
spec:
  containers:
  - name: app
    image: myapp:v1
    # Minimal distroless image, no shell

---
# Add ephemeral container for debugging (using kubectl)
# kubectl debug production-app -it --image=busybox --target=app

# The ephemeral container shares namespaces with target container
apiVersion: v1
kind: Pod
metadata:
  name: production-app
spec:
  containers:
  - name: app
    image: myapp:v1

  # Ephemeral containers (added dynamically)
  ephemeralContainers:
  - name: debugger
    image: busybox:1.36
    command: ["sh"]
    stdin: true
    tty: true
    targetContainerName: app
    securityContext:
      capabilities:
        add:
        - SYS_PTRACE  # For debugging
```

### Pod with Preemption and Priority

```yaml
# Create PriorityClass first
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: critical-priority
value: 1000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Critical production workloads"

---
# Pod with high priority
apiVersion: v1
kind: Pod
metadata:
  name: critical-pod
spec:
  priorityClassName: critical-priority
  preemptionPolicy: PreemptLowerPriority
  containers:
  - name: app
    image: critical-app:v1
    resources:
      requests:
        cpu: 2
        memory: 4Gi
```

### Pod with PodOverhead (Runtime Overhead)

```yaml
# RuntimeClass with overhead
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata-containers
handler: kata
overhead:
  podFixed:
    cpu: 250m
    memory: 120Mi

---
# Pod using kata-containers
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  runtimeClassName: kata-containers
  containers:
  - name: app
    image: untrusted-app:v1
    resources:
      requests:
        cpu: 1000m      # Total: 1250m (1000m + 250m overhead)
        memory: 1Gi     # Total: 1Gi + 120Mi overhead
      limits:
        cpu: 2000m
        memory: 2Gi
```

## Real-World Production Patterns

### 1. Microservice with Monitoring Sidecar

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: microservice-with-monitoring
  labels:
    app: order-service
    version: v2.1
spec:
  containers:
  # Main application
  - name: order-service
    image: order-service:v2.1
    ports:
    - name: http
      containerPort: 8080
    - name: grpc
      containerPort: 9090
    env:
    - name: OTEL_EXPORTER_OTLP_ENDPOINT
      value: "http://localhost:4317"
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 2000m
        memory: 2Gi
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5

  # OpenTelemetry collector sidecar
  - name: otel-collector
    image: otel/opentelemetry-collector:0.88.0
    ports:
    - name: otlp-grpc
      containerPort: 4317
    - name: otlp-http
      containerPort: 4318
    - name: metrics
      containerPort: 8888
    volumeMounts:
    - name: otel-config
      mountPath: /etc/otel
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi

  # Prometheus exporter sidecar
  - name: metrics-exporter
    image: prom/statsd-exporter:v0.26.0
    ports:
    - name: metrics
      containerPort: 9102
    args:
    - --statsd.mapping-config=/etc/statsd/mapping.yaml
    volumeMounts:
    - name: statsd-config
      mountPath: /etc/statsd
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 200m
        memory: 256Mi

  volumes:
  - name: otel-config
    configMap:
      name: otel-collector-config
  - name: statsd-config
    configMap:
      name: statsd-mapping-config
```

### 2. Database Pod with Backup Sidecar

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: postgres-with-backup
spec:
  initContainers:
  # Restore from backup on startup
  - name: restore-backup
    image: postgres:15-alpine
    command:
    - sh
    - -c
    - |
      if [ -f /backup/latest.sql.gz ]; then
        echo "Restoring from backup..."
        gunzip -c /backup/latest.sql.gz | psql -U postgres
      else
        echo "No backup found, starting fresh"
      fi
    env:
    - name: PGPASSWORD
      valueFrom:
        secretKeyRef:
          name: postgres-secret
          key: password
    volumeMounts:
    - name: data
      mountPath: /var/lib/postgresql/data
    - name: backup
      mountPath: /backup

  containers:
  # PostgreSQL database
  - name: postgres
    image: postgres:15-alpine
    ports:
    - containerPort: 5432
    env:
    - name: POSTGRES_PASSWORD
      valueFrom:
        secretKeyRef:
          name: postgres-secret
          key: password
    - name: PGDATA
      value: /var/lib/postgresql/data/pgdata
    volumeMounts:
    - name: data
      mountPath: /var/lib/postgresql/data
    - name: config
      mountPath: /etc/postgresql/postgresql.conf
      subPath: postgresql.conf
    resources:
      requests:
        cpu: 2
        memory: 4Gi
      limits:
        cpu: 4
        memory: 8Gi
    livenessProbe:
      exec:
        command:
        - pg_isready
        - -U
        - postgres
      initialDelaySeconds: 30
      periodSeconds: 10

  # Continuous backup sidecar
  - name: backup-agent
    image: postgres:15-alpine
    command:
    - sh
    - -c
    - |
      while true; do
        sleep 3600  # Hourly backups
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        pg_dump -U postgres -h localhost | gzip > /backup/backup_${TIMESTAMP}.sql.gz
        ln -sf /backup/backup_${TIMESTAMP}.sql.gz /backup/latest.sql.gz
        # Keep only last 24 backups
        ls -t /backup/backup_*.sql.gz | tail -n +25 | xargs rm -f
      done
    env:
    - name: PGPASSWORD
      valueFrom:
        secretKeyRef:
          name: postgres-secret
          key: password
    volumeMounts:
    - name: backup
      mountPath: /backup
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 500m
        memory: 1Gi

  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: postgres-data
  - name: backup
    persistentVolumeClaim:
      claimName: postgres-backup
  - name: config
    configMap:
      name: postgres-config
```

### 3. Web Application with Service Mesh Injection

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app-with-mesh
  labels:
    app: web-app
    version: v1
  annotations:
    # Istio/Linkerd sidecar injection
    sidecar.istio.io/inject: "true"
    # Resource limits for sidecar
    sidecar.istio.io/proxyCPU: "100m"
    sidecar.istio.io/proxyMemory: "128Mi"
    # Traffic interception
    traffic.sidecar.istio.io/includeOutboundIPRanges: "*"
    traffic.sidecar.istio.io/excludeOutboundIPRanges: ""
    # Prometheus scraping
    prometheus.io/scrape: "true"
    prometheus.io/port: "15020"
    prometheus.io/path: "/stats/prometheus"

spec:
  containers:
  - name: web-app
    image: web-app:v1
    ports:
    - name: http
      containerPort: 8080
    env:
    - name: BACKEND_URL
      value: "http://backend-service:9090"
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi

  # Istio sidecar (automatically injected)
  # - name: istio-proxy
  #   image: istio/proxyv2:1.19.0
  #   Handles all network traffic in/out
```

### 4. Batch Job Pod with Spot Instance Handling

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: batch-processor
  labels:
    app: batch-processor
    workload-type: batch
spec:
  restartPolicy: OnFailure

  # Tolerate spot instance interruptions
  tolerations:
  - key: node-lifecycle
    operator: Equal
    value: spot
    effect: NoSchedule
  - key: kubernetes.azure.com/scalesetpriority
    operator: Equal
    value: spot
    effect: NoSchedule

  # Prefer spot instances
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: node-lifecycle
            operator: In
            values:
            - spot

  # Allow longer termination for checkpoint
  terminationGracePeriodSeconds: 120

  containers:
  - name: processor
    image: batch-processor:v1
    command:
    - python
    - process.py
    - --checkpoint-dir=/checkpoints
    - --checkpoint-interval=300
    args:
    - --resume-from-checkpoint
    env:
    - name: JOB_ID
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: SPOT_INSTANCE
      value: "true"
    volumeMounts:
    - name: data
      mountPath: /data
    - name: checkpoints
      mountPath: /checkpoints
    resources:
      requests:
        cpu: 4
        memory: 8Gi
      limits:
        cpu: 8
        memory: 16Gi

    # Lifecycle hook to save checkpoint on termination
    lifecycle:
      preStop:
        exec:
          command:
          - /bin/sh
          - -c
          - |
            echo "Spot instance terminating, saving checkpoint..."
            kill -SIGTERM 1
            sleep 90  # Allow time to checkpoint

  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: batch-data
  - name: checkpoints
    persistentVolumeClaim:
      claimName: batch-checkpoints
```

### 5. Multi-Arch Pod (ARM64 + AMD64)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-arch-app
spec:
  # Node affinity for multi-arch support
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/arch
            operator: In
            values:
            - amd64
            - arm64

  containers:
  - name: app
    # Multi-arch image (manifest list)
    image: myapp:v1-multiarch
    # Or platform-specific images
    # image: myapp:v1-amd64  # For amd64
    # image: myapp:v1-arm64  # For arm64

    env:
    - name: ARCH
      valueFrom:
        fieldRef:
          fieldPath: status.hostIP
    - name: PLATFORM
      value: "linux/amd64"  # Set by image

    resources:
      requests:
        cpu: 500m
        memory: 512Mi
```

### 6. Pod with Custom DNS Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns-pod
spec:
  # DNS policy options:
  # - ClusterFirst: Use cluster DNS (default)
  # - Default: Use node's DNS
  # - ClusterFirstWithHostNet: Cluster DNS with hostNetwork
  # - None: Custom DNS config only
  dnsPolicy: None

  dnsConfig:
    nameservers:
    - 8.8.8.8
    - 8.8.4.4
    - 1.1.1.1
    searches:
    - my-namespace.svc.cluster.local
    - svc.cluster.local
    - cluster.local
    - example.com
    options:
    - name: ndots
      value: "2"
    - name: edns0
    - name: timeout
      value: "5"
    - name: attempts
      value: "2"

  # Custom hostname
  hostname: custom-hostname
  subdomain: my-subdomain
  # FQDN: custom-hostname.my-subdomain.my-namespace.svc.cluster.local
  setHostnameAsFQDN: false

  containers:
  - name: app
    image: myapp:v1
```

### 7. Pod with Process Namespace Sharing

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared-process-namespace
spec:
  # Share PID namespace between containers
  shareProcessNamespace: true

  containers:
  # Main application
  - name: app
    image: myapp:v1
    command: ["sleep", "infinity"]

  # Debugging container (can see app processes)
  - name: debug
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      # Can see and interact with processes from 'app' container
      while true; do
        ps aux
        sleep 60
      done
    securityContext:
      capabilities:
        add:
        - SYS_PTRACE  # For debugging other processes
```

### 8. Pod with Windows Containers (Windows Node)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: windows-app
spec:
  # Schedule on Windows nodes
  nodeSelector:
    kubernetes.io/os: windows
    kubernetes.io/arch: amd64

  containers:
  - name: iis
    image: mcr.microsoft.com/windows/servercore/iis:windowsservercore-ltsc2022
    ports:
    - containerPort: 80
    resources:
      requests:
        cpu: 1000m
        memory: 2Gi
      limits:
        cpu: 2000m
        memory: 4Gi

    # Windows-specific configurations
    securityContext:
      windowsOptions:
        gmsaCredentialSpecName: webapp-gmsa
        runAsUserName: "NT AUTHORITY\\SYSTEM"
```

### 9. Pod with Extended Resources (Custom Device)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fpga-pod
spec:
  containers:
  - name: app
    image: fpga-app:v1
    resources:
      requests:
        cpu: 2
        memory: 4Gi
        # Custom resource (device plugin)
        xilinx.com/fpga: 1
      limits:
        cpu: 4
        memory: 8Gi
        xilinx.com/fpga: 1

    volumeMounts:
    - name: fpga-dev
      mountPath: /dev/fpga

  volumes:
  - name: fpga-dev
    hostPath:
      path: /dev/fpga
      type: CharDevice
```

### 10. Pod with ReadWriteOncePod Volume (K8s 1.27+)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: single-pod-pvc
spec:
  accessModes:
  - ReadWriteOncePod  # Only one pod can mount (single node, single pod)
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd

---
apiVersion: v1
kind: Pod
metadata:
  name: exclusive-access-pod
spec:
  containers:
  - name: app
    image: database:v1
    volumeMounts:
    - name: data
      mountPath: /var/lib/data

  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: single-pod-pvc
```

## Advanced Debugging Techniques

### Using Ephemeral Containers

```bash
# Add debugging container to running pod
kubectl debug production-pod -it --image=busybox:1.36 --target=app

# Debug with different image
kubectl debug production-pod -it --image=ubuntu:22.04 -- bash

# Copy and debug (creates new pod)
kubectl debug production-pod --copy-to=debug-pod --container=app

# Debug node issues
kubectl debug node/worker-1 -it --image=ubuntu:22.04
```

### Port Forward for Local Testing

```bash
# Forward pod port to localhost
kubectl port-forward pod/my-pod 8080:80

# Forward to specific interface
kubectl port-forward --address 0.0.0.0 pod/my-pod 8080:80

# Forward multiple ports
kubectl port-forward pod/my-pod 8080:80 8443:443
```

### Execute Commands in Pod

```bash
# Execute single command
kubectl exec my-pod -- ls -la /app

# Interactive shell
kubectl exec -it my-pod -- /bin/bash

# Execute in specific container
kubectl exec -it my-pod -c app-container -- sh

# Execute as different user
kubectl exec -it my-pod -- su - appuser
```

## Pod Performance Optimization

### CPU Pinning (Guaranteed QoS + Static CPU Manager)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cpu-pinned-pod
spec:
  containers:
  - name: app
    image: high-performance-app:v1
    resources:
      # Must be integer CPUs for static CPU manager
      requests:
        cpu: 4
        memory: 8Gi
      limits:
        cpu: 4  # Must equal request
        memory: 8Gi

  # Node must have CPU manager enabled
  nodeSelector:
    cpu-manager: static
```

### NUMA Awareness

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: numa-aware-pod
spec:
  containers:
  - name: app
    image: database:v1
    resources:
      requests:
        cpu: 8
        memory: 16Gi
      limits:
        cpu: 8
        memory: 16Gi

  # Node must have topology manager enabled
  nodeSelector:
    topology-manager: single-numa-node
```

### Huge Pages

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hugepages-pod
spec:
  containers:
  - name: database
    image: postgres:15
    resources:
      requests:
        memory: 16Gi
        hugepages-2Mi: 8Gi  # 2MB huge pages
        # Or hugepages-1Gi: 8Gi  # 1GB huge pages
      limits:
        memory: 16Gi
        hugepages-2Mi: 8Gi

    volumeMounts:
    - name: hugepage-2mi
      mountPath: /hugepages-2Mi

  volumes:
  - name: hugepage-2mi
    emptyDir:
      medium: HugePages-2Mi
```

## Pod Security Standards

### Restricted Pod (Highest Security)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-pod
  labels:
    pod-security.kubernetes.io/enforce: restricted
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault

  containers:
  - name: app
    image: myapp:v1
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
      capabilities:
        drop:
        - ALL

    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /app/cache

  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
```

### Baseline Pod (Moderate Security)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: baseline-pod
  labels:
    pod-security.kubernetes.io/enforce: baseline
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault

  containers:
  - name: app
    image: myapp:v1
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE  # Allow binding to ports < 1024
```

## Pod Cost Optimization

### Burstable QoS for Cost Savings

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cost-optimized-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        cpu: 100m      # Minimal guarantee
        memory: 128Mi
      limits:
        cpu: 2000m     # Can burst when available
        memory: 2Gi
```

### Spot/Preemptible Instance Affinity

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: batch-job
spec:
  priorityClassName: low-priority

  affinity:
    nodeAffinity:
      # Prefer spot instances
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: node-lifecycle
            operator: In
            values:
            - spot
            - preemptible

  tolerations:
  - key: node-lifecycle
    operator: Equal
    value: spot
    effect: NoSchedule

  containers:
  - name: batch
    image: batch-processor:v1
```

## References

- [Pod Specification](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Configure Pods](https://kubernetes.io/docs/tasks/configure-pod-container/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Ephemeral Containers](https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/)
- [Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
