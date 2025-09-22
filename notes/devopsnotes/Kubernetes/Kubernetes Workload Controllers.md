# Kubernetes Workload Controllers

**Workload controllers** manage the deployment, scaling, and lifecycle of applications in Kubernetes, providing different patterns for stateless, stateful, batch, and daemon workloads in production environments.

## Deployments

### Basic Deployment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
  labels:
    app: web-app
    environment: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 25%
      maxSurge: 25%
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
        environment: production
    spec:
      containers:
      - name: web-app
        image: web-app:v1.2.3
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Deployment Strategies

```yaml
# Blue-Green Deployment Strategy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-blue
spec:
  replicas: 3
  strategy:
    type: Recreate  # All pods replaced at once
  selector:
    matchLabels:
      app: web-app
      version: blue
  template:
    metadata:
      labels:
        app: web-app
        version: blue
    spec:
      containers:
      - name: web-app
        image: web-app:v1.2.3

---
# Canary Deployment Strategy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-canary
spec:
  replicas: 1  # Small subset for testing
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: web-app
      version: canary
  template:
    metadata:
      labels:
        app: web-app
        version: canary
    spec:
      containers:
      - name: web-app
        image: web-app:v1.2.4  # New version
```

---

## StatefulSets

### Production StatefulSet for Databases

For stateful applications requiring stable identity, persistent storage, and ordered deployment

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql-cluster
  namespace: database
  labels:
    app: mysql
    component: database
spec:
  serviceName: mysql-headless
  replicas: 3
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
        component: database
    spec:
      securityContext:
        runAsUser: 999
        fsGroup: 999
      containers:
      - name: mysql
        image: mysql:8.0
        ports:
        - containerPort: 3306
          name: mysql
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: root-password
        - name: MYSQL_REPLICATION_USER
          value: "repl"
        - name: MYSQL_REPLICATION_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: replication-password

        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
          subPath: mysql
        - name: conf
          mountPath: /etc/mysql/conf.d
        - name: initdb
          mountPath: /docker-entrypoint-initdb.d

        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1000m"
            memory: "2Gi"

        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "mysqladmin ping -u root -p$MYSQL_ROOT_PASSWORD"
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5

        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "mysql -u root -p$MYSQL_ROOT_PASSWORD -e 'SELECT 1'"
          initialDelaySeconds: 5
          periodSeconds: 2
          timeoutSeconds: 1

      volumes:
      - name: conf
        configMap:
          name: mysql-config
      - name: initdb
        configMap:
          name: mysql-initdb

  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi

---
# Headless service for StatefulSet
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
  namespace: database
spec:
  selector:
    app: mysql
  clusterIP: None
  ports:
  - port: 3306
    targetPort: 3306
```

### StatefulSet Scaling and Updates

```bash
# Scaling StatefulSets
kubectl scale statefulset mysql-cluster --replicas=5 -n database

# Rolling updates with partition
kubectl patch statefulset mysql-cluster -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":2}}}}' -n database

# Update image gradually
kubectl set image statefulset/mysql-cluster mysql=mysql:8.0.32 -n database

# Check rollout status
kubectl rollout status statefulset/mysql-cluster -n database
```

### DaemonSets

Ensures pod runs on every node

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluentd:latest
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

### Jobs and CronJobs

**Job:**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  template:
    spec:
      containers:
      - name: migration
        image: migration:latest
        command: ["python", "migrate.py"]
      restartPolicy: Never
  backoffLimit: 4
```

**CronJob:**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup:latest
            command: ["backup.sh"]
          restartPolicy: OnFailure
```

---

## DaemonSets

### Production DaemonSet for Node Agents

Ensures a pod runs on every node (or selected nodes) for system-level services

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
  labels:
    app: node-exporter
    component: monitoring
spec:
  selector:
    matchLabels:
      app: node-exporter
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 25%
  template:
    metadata:
      labels:
        app: node-exporter
        component: monitoring
    spec:
      hostNetwork: true
      hostPID: true
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.3.1
        args:
        - '--path.sysfs=/host/sys'
        - '--path.rootfs=/host/root'
        - '--no-collector.wifi'
        - '--no-collector.hwmon'
        - '--collector.filesystem.ignored-mount-points=^/(dev|proc|sys|var/lib/docker/.+)($|/)'
        - '--collector.filesystem.ignored-fs-types=^(autofs|binfmt_misc|bpf|cgroup2?|configfs|debugfs|devpts|devtmpfs|fusectl|hugetlbfs|iso9660|mqueue|nsfs|overlay|proc|procfs|pstore|rpc_pipefs|securityfs|selinuxfs|squashfs|sysfs|tracefs)$'

        ports:
        - containerPort: 9100
          protocol: TCP
          name: metrics

        livenessProbe:
          httpGet:
            path: /
            port: 9100
          initialDelaySeconds: 30
          timeoutSeconds: 5

        readinessProbe:
          httpGet:
            path: /
            port: 9100
          initialDelaySeconds: 5
          timeoutSeconds: 5

        resources:
          requests:
            memory: 30Mi
            cpu: 100m
          limits:
            memory: 50Mi
            cpu: 200m

        volumeMounts:
        - name: sys
          mountPath: /host/sys
          mountPropagation: HostToContainer
          readOnly: true
        - name: root
          mountPath: /host/root
          mountPropagation: HostToContainer
          readOnly: true

      volumes:
      - name: sys
        hostPath:
          path: /sys
      - name: root
        hostPath:
          path: /

      tolerations:
      - operator: Exists
        effect: NoSchedule
      - operator: Exists
        effect: NoExecute

      nodeSelector:
        kubernetes.io/os: linux
```

### Logging DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      serviceAccountName: fluentd
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1.14-debian-elasticsearch7-1
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.logging.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        - name: FLUENT_ELASTICSEARCH_SCHEME
          value: "http"

        resources:
          requests:
            memory: 200Mi
            cpu: 100m
          limits:
            memory: 500Mi
            cpu: 500m

        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true

      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers

      tolerations:
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
```

---

## Jobs & CronJobs

### Production Job Patterns

```yaml
# One-time job with completion tracking
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration
  namespace: production
spec:
  parallelism: 1
  completions: 1
  backoffLimit: 3
  activeDeadlineSeconds: 3600

  template:
    metadata:
      labels:
        app: database-migration
        job-name: database-migration
    spec:
      restartPolicy: Never
      containers:
      - name: migration
        image: migration-tool:v1.2.3
        command:
        - /bin/sh
        - -c
        - |
          echo "Starting database migration..."
          migrate -path /migrations -database $DATABASE_URL up
          echo "Migration completed successfully"

        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url

        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
# Parallel processing job
apiVersion: batch/v1
kind: Job
metadata:
  name: data-processing
spec:
  parallelism: 5
  completions: 10
  backoffLimit: 6

  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: processor
        image: data-processor:latest
        command: ["process-data"]
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### CronJob for Scheduled Tasks

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: production
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  timeZone: "America/New_York"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  startingDeadlineSeconds: 300

  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 3600

      template:
        metadata:
          labels:
            app: database-backup
            cronjob: database-backup
        spec:
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: backup-tool:v2.1.0
            command:
            - /bin/bash
            - -c
            - |
              set -euo pipefail
              echo "Starting backup at $(date)"

              # Create backup
              pg_dump $DATABASE_URL | gzip > /tmp/backup-$(date +%Y%m%d-%H%M%S).sql.gz

              # Upload to S3
              aws s3 cp /tmp/backup-*.sql.gz s3://backups/database/

              # Cleanup old backups
              find /tmp -name "backup-*.sql.gz" -delete

              echo "Backup completed at $(date)"

            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-secret
                  key: url
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-secret
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-secret
                  key: secret-access-key

            resources:
              requests:
                memory: "512Mi"
                cpu: "250m"
              limits:
                memory: "1Gi"
                cpu: "500m"
```

---

## ReplicaSets

### Direct ReplicaSet Usage

```yaml
# Generally managed by Deployments, but can be used directly
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend-rs
  labels:
    app: frontend
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
      tier: frontend
  template:
    metadata:
      labels:
        app: frontend
        tier: frontend
    spec:
      containers:
      - name: frontend
        image: frontend:v1.0.0
        ports:
        - containerPort: 80
```

---

## Horizontal Pod Autoscaler

### Advanced HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 3
  maxReplicas: 50

  metrics:
  # CPU utilization
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

  # Memory utilization
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

  # Custom metrics (requires metrics adapter)
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"

  # External metrics (e.g., SQS queue length)
  - type: External
    external:
      metric:
        name: sqs_queue_length
        selector:
          matchLabels:
            queue: "work-queue"
      target:
        type: Value
        value: "30"

  # Scaling behavior
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 5
        periodSeconds: 60
      selectPolicy: Max
```

---

## Vertical Pod Autoscaler

### VPA Configuration

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-app-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app

  updatePolicy:
    updateMode: "Auto"  # Auto, Recreate, or Off

  resourcePolicy:
    containerPolicies:
    - containerName: web-app
      maxAllowed:
        cpu: "2"
        memory: "4Gi"
      minAllowed:
        cpu: "100m"
        memory: "128Mi"
      controlledResources: ["cpu", "memory"]
      controlledValues: RequestsAndLimits
```

---

## Advanced Scheduling

### Pod Affinity and Anti-Affinity

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-with-affinity
spec:
  template:
    spec:
      affinity:
        # Pod anti-affinity - spread across nodes
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - web-app
            topologyKey: kubernetes.io/hostname

          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-app
              topologyKey: topology.kubernetes.io/zone

        # Node affinity - prefer specific nodes
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: node-type
                operator: In
                values:
                - compute-optimized

          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 50
            preference:
              matchExpressions:
              - key: availability-zone
                operator: In
                values:
                - us-west-2a
                - us-west-2b

      # Topology spread constraints
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: web-app
      - maxSkew: 2
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: web-app
```

### Taints and Tolerations

```yaml
# Deployment with tolerations
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-workload
spec:
  template:
    spec:
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      - key: "dedicated"
        operator: "Equal"
        value: "gpu-nodes"
        effect: "NoExecute"
        tolerationSeconds: 3600

      nodeSelector:
        accelerator: nvidia-tesla-k80
```

---

## Production Patterns

### Multi-Container Pods

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-sidecar
spec:
  template:
    spec:
      containers:
      # Main application container
      - name: app
        image: myapp:v1.0.0
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: shared-logs
          mountPath: /var/log

      # Logging sidecar
      - name: log-forwarder
        image: fluent/fluent-bit:1.8
        volumeMounts:
        - name: shared-logs
          mountPath: /var/log
        - name: fluent-bit-config
          mountPath: /fluent-bit/etc

      # Monitoring sidecar
      - name: metrics-exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100

      # Init container for setup
      initContainers:
      - name: init-permissions
        image: busybox:1.35
        command:
        - sh
        - -c
        - "chown -R 1000:1000 /var/log"
        volumeMounts:
        - name: shared-logs
          mountPath: /var/log
        securityContext:
          runAsUser: 0

      volumes:
      - name: shared-logs
        emptyDir: {}
      - name: fluent-bit-config
        configMap:
          name: fluent-bit-config
```

### Resource Management Patterns

```yaml
# Quality of Service classes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: guaranteed-qos
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "1Gi"  # Same as requests = Guaranteed
            cpu: "500m"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: burstable-qos
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"   # Higher than requests = Burstable
            cpu: "1000m"
```

---

## Troubleshooting

### Common Issues and Solutions

**Issue**: Pods stuck in Pending state
```bash
# Check node resources and scheduling
kubectl describe pod pending-pod
kubectl get nodes -o wide
kubectl top nodes

# Check for resource constraints
kubectl describe node node-name | grep -A 10 "Allocated resources"

# Check for taints and tolerations
kubectl describe node node-name | grep -A 5 Taints
```

**Issue**: CrashLoopBackOff
```bash
# Check container logs
kubectl logs crashlooping-pod --previous
kubectl describe pod crashlooping-pod

# Check resource limits
kubectl get pod crashlooping-pod -o yaml | grep -A 10 resources

# Check liveness probe configuration
kubectl get pod crashlooping-pod -o yaml | grep -A 10 livenessProbe
```

**Issue**: StatefulSet scaling issues
```bash
# Check PVC status
kubectl get pvc
kubectl describe pvc data-mysql-cluster-2

# Check StatefulSet status
kubectl describe statefulset mysql-cluster
kubectl get pods -l app=mysql

# Force delete stuck pods
kubectl delete pod mysql-cluster-2 --force --grace-period=0
```

### Debugging Commands

```bash
# Workload controller status
kubectl get deployments,statefulsets,daemonsets,jobs,cronjobs -A

# Resource utilization
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory

# Events and logs
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl logs deployment/web-app -f --max-log-requests=10

# Scale and update operations
kubectl scale deployment web-app --replicas=5
kubectl rollout restart deployment/web-app
kubectl rollout status deployment/web-app
kubectl rollout history deployment/web-app
```

---

## Cross-References

**Related Documentation:**
- [Kubernetes Commands](Kubernetes%20Commands.md) - kubectl commands for workload management
- [Kubernetes Autoscaling & Resource Management](Kubernetes%20Autoscaling%20&%20Resource%20Management.md) - HPA, VPA, and cluster autoscaling
- [Kubernetes Production Best Practices](Kubernetes%20Production%20Best%20Practices.md) - Security and reliability patterns
- [Kubernetes Storage](Kubernetes%20Storage.md) - Persistent volumes for StatefulSets

**Integration Points:**
- **Monitoring**: Prometheus metrics for workload observability
- **Logging**: Centralized logging for application and system logs
- **Service Mesh**: Istio, Linkerd integration with workload controllers
- **GitOps**: ArgoCD, Flux for automated workload deployments
