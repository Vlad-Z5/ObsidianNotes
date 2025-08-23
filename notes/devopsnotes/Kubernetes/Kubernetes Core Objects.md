## Workload Resources Comprehensive Guide

### Pod Deep Dive

**Pod Lifecycle Phases:**

1. **Pending**: Pod accepted but not scheduled or containers not created
2. **Running**: Pod bound to node, all containers created, at least one running
3. **Succeeded**: All containers terminated successfully
4. **Failed**: All containers terminated, at least one failed
5. **Unknown**: Pod state cannot be determined

**Container Specifications:**

**Init Containers**: Run before app containers, must complete successfully

```yaml
spec:
  initContainers:
  - name: init-db
    image: busybox:1.35
    command: ['sh', '-c', 'until nslookup mydb; do sleep 2; done;']
  - name: init-permissions
    image: busybox:1.35
    command: ['sh', '-c', 'chmod 755 /shared-data']
    volumeMounts:
    - name: shared-storage
      mountPath: /shared-data
```

**Sidecar Containers**: Run alongside main application containers

```yaml
spec:
  containers:
  - name: web-server
    image: nginx:1.21
    ports:
    - containerPort: 80
  - name: log-collector
    image: fluentd:v1.14
    volumeMounts:
    - name: varlog
      mountPath: /var/log
```

**Probe Configurations:**

**startupProbe**: Validates container startup (especially for slow-starting applications)

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
  timeoutSeconds: 5
```

**livenessProbe**: Determines if container should be restarted

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
    httpHeaders:
    - name: Custom-Header
      value: Awesome
  initialDelaySeconds: 15
  periodSeconds: 20
  timeoutSeconds: 5
  failureThreshold: 3
```

**readinessProbe**: Determines if container is ready to receive traffic

```yaml
readinessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```

**Resource Management:**

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "250m"
    ephemeral-storage: "1Gi"
  limits:
    memory: "128Mi"
    cpu: "500m"
    ephemeral-storage: "2Gi"
```

**Security Context:**

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 3000
  runAsNonRoot: true
  fsGroup: 2000
  capabilities:
    add: ["NET_ADMIN", "SYS_TIME"]
    drop: ["ALL"]
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

**DevOps Pod Management:**

- Implement proper resource requests/limits for optimal scheduling
- Configure appropriate restart policies (Always, OnFailure, Never)
- Set up monitoring for pod resource utilization
- Implement proper logging and log rotation
- Configure pod disruption budgets for high availability
- Use multi-container patterns effectively (sidecar, adapter, ambassador)

### Deployment Strategies Deep Dive

**Rolling Update Strategy:**

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 25%  # Can be percentage or absolute number
    maxSurge: 25%        # Additional pods during update
```

**Recreate Strategy:**

```yaml
strategy:
  type: Recreate  # All pods terminated before new ones created
```

**Advanced Deployment Patterns:**

**Blue-Green Deployment**: Maintain two identical environments

```yaml
# Blue deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: blue
---
# Service initially points to blue
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
    version: blue  # Switch to green for cutover
```

**Canary Deployment with Traffic Splitting:**

```yaml
# Primary deployment (90% traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-primary
spec:
  replicas: 9
  selector:
    matchLabels:
      app: myapp
      track: primary
---
# Canary deployment (10% traffic)  
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
      track: canary
---
# Service routes to both
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp  # Matches both primary and canary
```

**DevOps Deployment Best Practices:**

- Implement proper health checks before routing traffic
- Use deployment annotations for change tracking
- Configure appropriate replica counts for availability
- Implement automated rollback triggers based on metrics
- Monitor deployment progress and set timeouts
- Use labels effectively for deployment management
- Implement proper testing strategies for each deployment type

### StatefulSet Deep Dive

StatefulSets provide stable network identities and persistent storage for stateful applications.

**Key Features:**

- **Stable Network Identity**: Pods get predictable names (web-0, web-1, web-2)
- **Stable Storage**: Each pod gets persistent volume claims
- **Ordered Deployment**: Pods created sequentially (0, then 1, then 2)
- **Ordered Deletion**: Pods deleted in reverse order (2, then 1, then 0)

**StatefulSet Configuration:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
spec:
  serviceName: postgresql-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: mydb
        - name: POSTGRES_USER
          value: admin
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        ports:
        - containerPort: 5432
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 10Gi
```

**Headless Service for StatefulSet:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgresql-headless
spec:
  clusterIP: None  # Headless service
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
```

**Scaling StatefulSets:**

- Scale up: New pods created sequentially with next ordinal
- Scale down: Highest ordinal pods terminated first
- Manual scaling: `kubectl scale statefulset postgresql --replicas=5`
- Automatic scaling: Use HPA with custom metrics

**DevOps StatefulSet Management:**

- Plan for data migration during scaling operations
- Implement proper backup strategies for persistent data
- Monitor pod startup and readiness times
- Configure appropriate resource limits for stateful workloads
- Implement proper storage class selection based on performance needs
- Plan for disaster recovery and data replication strategies

### DaemonSet Deep Dive

DaemonSets ensure pods run on all (or selected) nodes in the cluster.

**Common Use Cases:**

- **Log Collection**: Fluentd, Fluent Bit, Filebeat
- **Monitoring**: Node Exporter, Datadog agent, New Relic agent
- **Networking**: CNI agents, kube-proxy
- **Storage**: Storage daemons, CSI node drivers
- **Security**: Security scanning agents, runtime security tools

**DaemonSet Configuration:**

```yaml
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
        effect: NoSchedule  # Run on master nodes too
      containers:
      - name: fluentd-elasticsearch
        image: fluent/fluentd-kubernetes-daemonset:elasticsearch
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
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

**Node Selection for DaemonSets:**

```yaml
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/os: linux  # Only Linux nodes
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      - key: node.kubernetes.io/not-ready
        effect: NoExecute
        tolerationSeconds: 300
```

### ReplicaSet

Ensures specified number of pod replicas are running

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-replicaset
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
```

### Deployment

Higher-level object that manages ReplicaSets and provides rolling updates

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
```

### Service

Exposes pods to network traffic with stable IP and DNS name

**ClusterIP Service (Default):**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
```

**NodePort Service:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  selector:
    app: nginx
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
    nodePort: 30080
  type: NodePort
```

**LoadBalancer Service:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-loadbalancer
spec:
  selector:
    app: nginx
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: LoadBalancer
```
