# Deployment Manifest

## Overview

A Deployment is a higher-level Kubernetes resource that provides declarative updates for Pods and ReplicaSets. It manages the complete lifecycle of stateless applications including rollout, rollback, scaling, and self-healing capabilities.

**API Version:** `apps/v1`
**Kind:** `Deployment`
**Scope:** Namespaced

## When to Use Deployment

### Ideal Use Cases

**Stateless Applications:**
- Web servers (Nginx, Apache, Caddy)
- REST/GraphQL APIs (Node.js, Go, Python, Java services)
- Frontend applications (React, Vue, Angular, static sites)
- Microservices architectures
- Message queue consumers without state persistence
- API gateways (Kong, Tyk, Ambassador)
- Caching layers (Redis in replica mode, Memcached)
- Serverless function runners (Knative, OpenFaaS)

**Horizontally Scalable Services:**
- Load-balanced web applications
- Stateless backend services
- Worker pools processing from queues
- Proxy services (Envoy, HAProxy, Traefik)

### When NOT to Use Deployment

**Use StatefulSet instead for:**
- Databases requiring persistent identity (PostgreSQL, MySQL, MongoDB)
- Distributed systems needing stable network identities (Kafka, Elasticsearch, Cassandra)
- Applications with ordered deployment/scaling requirements
- Services requiring stable persistent storage per pod

**Use DaemonSet instead for:**
- Node monitoring agents (Prometheus Node Exporter, Datadog agent)
- Log collectors (Fluentd, Fluent Bit, Filebeat)
- CNI network plugins
- Storage daemons

**Use Job/CronJob instead for:**
- One-time batch processing tasks
- Scheduled operations (backups, reports, cleanup)
- Database migrations
- ETL processes

## Architecture and Concepts

### Controller Hierarchy

```
Deployment
  └── ReplicaSet (manages replicas)
        └── Pods (actual running containers)
```

**How it works:**
1. Deployment creates and manages ReplicaSets
2. ReplicaSet ensures desired number of pod replicas
3. During updates, Deployment creates new ReplicaSet and scales down old one
4. Old ReplicaSets kept for rollback (controlled by `revisionHistoryLimit`)

### Update Strategies

#### 1. RollingUpdate (Default)
Gradually replaces old pods with new ones, ensuring zero downtime.

**Configuration:**
- `maxSurge`: Maximum number of pods above desired count during update
- `maxUnavailable`: Maximum number of pods that can be unavailable during update

**Example calculation (5 replicas):**
```
maxSurge: 2, maxUnavailable: 1
- Can have up to 7 pods during update (5 + 2)
- Must have at least 4 pods available (5 - 1)
```

#### 2. Recreate
Terminates all existing pods before creating new ones. Results in downtime.

**Use when:**
- Application versions are incompatible
- Single-writer database migrations
- Resource constraints prevent running two versions
- Downtime is acceptable

## Basic Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-web
  namespace: production
  labels:
    app: nginx
    component: frontend
    environment: production
  annotations:
    deployment.kubernetes.io/revision: "1"
    kubernetes.io/change-cause: "Initial deployment"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
      component: frontend
  template:
    metadata:
      labels:
        app: nginx
        component: frontend
        version: "1.21.6"
    spec:
      containers:
      - name: nginx
        image: nginx:1.21.6
        ports:
        - containerPort: 80
          name: http
          protocol: TCP
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

## Production-Grade Deployment

### Complete Example with All Best Practices

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: production
  labels:
    app: api-service
    component: backend
    tier: application
    version: v2.1.0
  annotations:
    kubernetes.io/change-cause: "Update to v2.1.0 with performance improvements"
    deployment.kubernetes.io/revision: "5"
    team: platform-team
    pagerduty: "https://company.pagerduty.com/services/api-service"
spec:
  replicas: 10
  revisionHistoryLimit: 10
  progressDeadlineSeconds: 600
  minReadySeconds: 30

  selector:
    matchLabels:
      app: api-service
      component: backend

  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 3
      maxUnavailable: 1

  template:
    metadata:
      labels:
        app: api-service
        component: backend
        version: v2.1.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
        fluentd.io/parser: "json"

    spec:
      # Security Context at Pod Level
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 3000
        fsGroup: 2000
        seccompProfile:
          type: RuntimeDefault

      # Service Account
      serviceAccountName: api-service-sa

      # DNS Policy
      dnsPolicy: ClusterFirst
      dnsConfig:
        options:
        - name: ndots
          value: "2"
        - name: timeout
          value: "2"
        - name: attempts
          value: "2"

      # Topology Spread Constraints
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: api-service
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: api-service

      # Pod Affinity/Anti-Affinity
      affinity:
        # Spread pods across nodes
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - api-service
            topologyKey: kubernetes.io/hostname

          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - api-service
              topologyKey: topology.kubernetes.io/zone

        # Deploy on specific node types
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: node.kubernetes.io/instance-type
                operator: In
                values:
                - c5.2xlarge
                - c5.4xlarge
              - key: topology.kubernetes.io/region
                operator: In
                values:
                - us-east-1

          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 50
            preference:
              matchExpressions:
              - key: node-pool
                operator: In
                values:
                - high-performance

      # Init Containers
      initContainers:
      - name: wait-for-database
        image: busybox:1.36
        command:
        - 'sh'
        - '-c'
        - |
          until nc -z postgres-service 5432; do
            echo "Waiting for database..."
            sleep 2
          done
          echo "Database is ready"
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL

      - name: migrate-database
        image: company/api-service:v2.1.0
        command: ["/app/migrate"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL

      # Main Application Container
      containers:
      - name: api-service
        image: company/api-service:v2.1.0
        imagePullPolicy: IfNotPresent

        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        - name: health
          containerPort: 8081
          protocol: TCP

        # Environment Variables
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        - name: PORT
          value: "8080"
        - name: METRICS_PORT
          value: "9090"

        # From ConfigMap
        - name: FEATURE_FLAGS
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: feature_flags
        - name: MAX_CONNECTIONS
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: max_connections

        # From Secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: external-api-credentials
              key: api_key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret

        # Pod Metadata
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

        # Load entire ConfigMap as env vars
        envFrom:
        - configMapRef:
            name: api-config
        - secretRef:
            name: api-secrets

        # Resource Management
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
            ephemeral-storage: "1Gi"
          limits:
            memory: "1Gi"
            cpu: "1000m"
            ephemeral-storage: "2Gi"

        # Startup Probe (for slow-starting applications)
        startupProbe:
          httpGet:
            path: /health/startup
            port: health
            httpHeaders:
            - name: X-Probe-Type
              value: Startup
          initialDelaySeconds: 0
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 30  # 30 * 5s = 150s max startup time

        # Liveness Probe (restart if unhealthy)
        livenessProbe:
          httpGet:
            path: /health/live
            port: health
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3

        # Readiness Probe (remove from load balancer if not ready)
        readinessProbe:
          httpGet:
            path: /health/ready
            port: health
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3

        # Lifecycle Hooks
        lifecycle:
          postStart:
            exec:
              command:
              - /bin/sh
              - -c
              - |
                echo "Container started at $(date)" >> /var/log/lifecycle.log
                # Pre-warm caches, load data, etc.

          preStop:
            exec:
              command:
              - /bin/sh
              - -c
              - |
                echo "Shutting down gracefully..."
                # Drain connections, finish processing
                sleep 15

        # Security Context (Container Level)
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
          runAsGroup: 3000
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
          seccompProfile:
            type: RuntimeDefault

        # Volume Mounts
        volumeMounts:
        - name: config
          mountPath: /etc/app/config
          readOnly: true
        - name: secrets
          mountPath: /etc/app/secrets
          readOnly: true
        - name: cache
          mountPath: /var/cache/app
        - name: logs
          mountPath: /var/log/app
        - name: tmp
          mountPath: /tmp
        - name: shared-data
          mountPath: /app/shared

      # Sidecar: Metrics Exporter
      - name: metrics-exporter
        image: prom/statsd-exporter:v0.24.0
        ports:
        - name: metrics
          containerPort: 9102
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
          limits:
            memory: "64Mi"
            cpu: "100m"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 65534
          capabilities:
            drop:
            - ALL

      # Sidecar: Log Aggregator
      - name: log-aggregator
        image: fluent/fluent-bit:2.0
        volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true
        - name: fluentbit-config
          mountPath: /fluent-bit/etc
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL

      # Volumes
      volumes:
      - name: config
        configMap:
          name: api-config
          defaultMode: 0444
      - name: secrets
        secret:
          secretName: api-secrets
          defaultMode: 0400
      - name: cache
        emptyDir:
          medium: Memory
          sizeLimit: 256Mi
      - name: logs
        emptyDir:
          sizeLimit: 1Gi
      - name: tmp
        emptyDir:
          sizeLimit: 512Mi
      - name: shared-data
        emptyDir: {}
      - name: fluentbit-config
        configMap:
          name: fluentbit-config

      # Image Pull Secrets
      imagePullSecrets:
      - name: registry-credentials

      # Termination Grace Period
      terminationGracePeriodSeconds: 60

      # Priority Class
      priorityClassName: high-priority

      # Tolerations
      tolerations:
      - key: "dedicated"
        operator: "Equal"
        value: "api-service"
        effect: "NoSchedule"
      - key: "node.kubernetes.io/not-ready"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
      - key: "node.kubernetes.io/unreachable"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
```

## Update Strategies in Detail

### RollingUpdate Strategy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rolling-update-example
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 3           # Can create 3 extra pods (13 total during update)
      maxUnavailable: 2     # Allow 2 pods unavailable (8 minimum available)
  minReadySeconds: 30       # Wait 30s after pod ready before next update
  progressDeadlineSeconds: 600  # Fail deployment if not progressing after 10min
  revisionHistoryLimit: 10  # Keep last 10 ReplicaSets for rollback

  selector:
    matchLabels:
      app: myapp

  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: myapp:v2.0
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          periodSeconds: 5
```

**Update Process:**
1. Creates new ReplicaSet with new pod template
2. Scales new ReplicaSet up by maxSurge (3 pods)
3. Scales old ReplicaSet down by maxUnavailable (2 pods)
4. Repeats until all pods updated
5. Keeps old ReplicaSet with 0 replicas for rollback

### Recreate Strategy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recreate-example
spec:
  replicas: 3
  strategy:
    type: Recreate  # All old pods deleted before new ones created

  selector:
    matchLabels:
      app: migration-app

  template:
    metadata:
      labels:
        app: migration-app
    spec:
      containers:
      - name: app
        image: migration-app:v2.0
```

**Update Process:**
1. Scales old ReplicaSet to 0 (terminates all pods)
2. Waits for all old pods to terminate
3. Creates new ReplicaSet
4. Scales new ReplicaSet to desired replicas

**Downtime:** Yes (duration = termination time + startup time)

## Advanced Deployment Patterns

### Blue-Green Deployment

Deploy new version alongside old, switch traffic instantly.

```yaml
# Blue Deployment (current production - v1.0)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  namespace: production
  labels:
    app: myapp
    slot: blue
    version: v1.0
spec:
  replicas: 5
  selector:
    matchLabels:
      app: myapp
      slot: blue
  template:
    metadata:
      labels:
        app: myapp
        slot: blue
        version: v1.0
    spec:
      containers:
      - name: app
        image: company/myapp:1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          periodSeconds: 5

---
# Green Deployment (new version - v2.0)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  namespace: production
  labels:
    app: myapp
    slot: green
    version: v2.0
spec:
  replicas: 5
  selector:
    matchLabels:
      app: myapp
      slot: green
  template:
    metadata:
      labels:
        app: myapp
        slot: green
        version: v2.0
    spec:
      containers:
      - name: app
        image: company/myapp:2.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          periodSeconds: 5

---
# Production Service (controls traffic routing)
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
  namespace: production
spec:
  selector:
    app: myapp
    slot: blue  # Change to 'green' to switch all traffic instantly
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer

---
# Internal Testing Service (always points to green for validation)
apiVersion: v1
kind: Service
metadata:
  name: myapp-preview
  namespace: production
spec:
  selector:
    app: myapp
    slot: green
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

**Deployment Process:**
```bash
# 1. Deploy green deployment
kubectl apply -f green-deployment.yaml

# 2. Wait for green to be ready
kubectl wait --for=condition=available --timeout=300s deployment/app-green

# 3. Test green deployment internally
curl http://myapp-preview/health
# Run smoke tests, integration tests

# 4. Switch traffic to green
kubectl patch service myapp-service -p '{"spec":{"selector":{"slot":"green"}}}'

# 5. Monitor metrics, logs, errors
kubectl logs -f deployment/app-green
# Watch metrics dashboard

# 6. If issues, instant rollback
kubectl patch service myapp-service -p '{"spec":{"selector":{"slot":"blue"}}}'

# 7. If successful, delete blue deployment
kubectl delete deployment app-blue
```

**Advantages:**
- Instant traffic switching (no gradual rollout)
- Easy instant rollback
- Full testing of new version before traffic switch
- Zero downtime

**Disadvantages:**
- Requires 2x resources during deployment
- Database migrations can be tricky (must be backward compatible)

### Canary Deployment

Gradually shift traffic to new version by adjusting replica counts.

```yaml
# Stable Deployment (v1.0 - production traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
  namespace: production
  labels:
    app: myapp
    track: stable
    version: v1.0
spec:
  replicas: 9  # 90% of traffic
  selector:
    matchLabels:
      app: myapp
      track: stable
  template:
    metadata:
      labels:
        app: myapp
        track: stable
        version: v1.0
    spec:
      containers:
      - name: app
        image: company/myapp:1.0.0
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health
            port: 8080

---
# Canary Deployment (v2.0 - testing new version)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
  namespace: production
  labels:
    app: myapp
    track: canary
    version: v2.0
spec:
  replicas: 1  # 10% of traffic initially
  selector:
    matchLabels:
      app: myapp
      track: canary
  template:
    metadata:
      labels:
        app: myapp
        track: canary
        version: v2.0
      annotations:
        prometheus.io/scrape: "true"
        # Additional monitoring for canary
    spec:
      containers:
      - name: app
        image: company/myapp:2.0.0
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health
            port: 8080

---
# Service routes to both stable and canary
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
  namespace: production
spec:
  selector:
    app: myapp  # Routes to both stable and canary based on replicas
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

**Gradual Rollout Process:**
```bash
# Phase 1: 10% canary traffic (1 replica)
kubectl apply -f canary-deployment.yaml  # replicas: 1
# stable: 9, canary: 1 (10% traffic)

# Monitor metrics for 30 minutes
# Error rate, latency, throughput, business metrics

# Phase 2: 25% canary traffic
kubectl scale deployment app-canary --replicas=3
kubectl scale deployment app-stable --replicas=9
# stable: 9, canary: 3 (25% traffic)

# Monitor for 1 hour

# Phase 3: 50% canary traffic
kubectl scale deployment app-canary --replicas=5
kubectl scale deployment app-stable --replicas=5
# stable: 5, canary: 5 (50% traffic)

# Monitor for 2 hours

# Phase 4: 100% canary traffic
kubectl scale deployment app-canary --replicas=10
kubectl scale deployment app-stable --replicas=0
# stable: 0, canary: 10 (100% traffic)

# Phase 5: Replace stable with new version
kubectl delete deployment app-stable
kubectl patch deployment app-canary -p '{"metadata":{"name":"app-stable"}}'
# Or recreate stable deployment with v2.0

# If issues at any phase, rollback
kubectl scale deployment app-stable --replicas=9
kubectl scale deployment app-canary --replicas=1
```

**Automated Canary with Flagger (Progressive Delivery):**

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp

  service:
    port: 80
    targetPort: 8080

  analysis:
    interval: 1m
    threshold: 10
    maxWeight: 50
    stepWeight: 5

    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m

    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m

    webhooks:
    - name: load-test
      url: http://loadtester.production/
      timeout: 5s
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 http://myapp-canary.production/"
```

### A/B Testing Deployment

Route specific users to specific versions based on headers/criteria.

```yaml
# Version A Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-version-a
spec:
  replicas: 5
  selector:
    matchLabels:
      app: myapp
      version: a
  template:
    metadata:
      labels:
        app: myapp
        version: a
    spec:
      containers:
      - name: app
        image: myapp:version-a
        env:
        - name: FEATURE_NEW_UI
          value: "false"

---
# Version B Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-version-b
spec:
  replicas: 5
  selector:
    matchLabels:
      app: myapp
      version: b
  template:
    metadata:
      labels:
        app: myapp
        version: b
    spec:
      containers:
      - name: app
        image: myapp:version-b
        env:
        - name: FEATURE_NEW_UI
          value: "true"

---
# Requires service mesh (Istio) for header-based routing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-ab-test
spec:
  hosts:
  - myapp.example.com
  http:
  - match:
    - headers:
        x-version:
          exact: "b"
    route:
    - destination:
        host: myapp-version-b
        port:
          number: 8080
  - route:
    - destination:
        host: myapp-version-a
        port:
          number: 8080
      weight: 50
    - destination:
        host: myapp-version-b
        port:
          number: 8080
      weight: 50
```

## GitOps Integration

### ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-deployment
  namespace: argocd
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: production

  source:
    repoURL: https://github.com/company/k8s-manifests
    targetRevision: main
    path: apps/myapp/overlays/production

    # Helm Chart Source
    # helm:
    #   valueFiles:
    #   - values-production.yaml

    # Kustomize Source
    kustomize:
      namespace: production
      namePrefix: prod-
      nameSuffix: -v2
      images:
      - company/myapp:2.0.0
      commonLabels:
        environment: production

  destination:
    server: https://kubernetes.default.svc
    namespace: production

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false

    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true

    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

  revisionHistoryLimit: 10

  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas  # Ignore replica count differences (managed by HPA)
```

**ArgoCD Sync Waves for Ordered Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  annotations:
    argocd.argoproj.io/sync-wave: "2"  # Deploy after database (wave 1)
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  # ... deployment spec
```

### FluxCD Integration

```yaml
# GitRepository Source
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: myapp-repo
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/company/k8s-manifests
  ref:
    branch: main
  secretRef:
    name: git-credentials

---
# Kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: myapp-deployment
  namespace: flux-system
spec:
  interval: 10m
  retryInterval: 1m
  timeout: 5m
  sourceRef:
    kind: GitRepository
    name: myapp-repo
  path: ./apps/myapp/production
  prune: true
  wait: true

  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: myapp
    namespace: production

  postBuild:
    substitute:
      ENVIRONMENT: "production"
      REPLICAS: "10"
    substituteFrom:
    - kind: ConfigMap
      name: cluster-vars

---
# HelmRelease (if using Helm)
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: myapp
  namespace: production
spec:
  interval: 10m
  chart:
    spec:
      chart: myapp
      version: '>=1.0.0 <2.0.0'
      sourceRef:
        kind: HelmRepository
        name: company-charts
        namespace: flux-system

  values:
    replicaCount: 10
    image:
      repository: company/myapp
      tag: 2.0.0

    resources:
      requests:
        memory: 256Mi
        cpu: 200m

  upgrade:
    remediation:
      retries: 3

  test:
    enable: true

  rollback:
    enable: true
    force: true
    recreate: true
```

## Helm Chart Integration

### Deployment Template in Helm Chart

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
    {{- with .Values.labels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
  annotations:
    {{- with .Values.annotations }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}

  revisionHistoryLimit: {{ .Values.revisionHistoryLimit }}

  selector:
    matchLabels:
      {{- include "myapp.selectorLabels" . | nindent 6 }}

  strategy:
    {{- toYaml .Values.strategy | nindent 4 }}

  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "myapp.selectorLabels" . | nindent 8 }}
        {{- with .Values.podLabels }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}

      serviceAccountName: {{ include "myapp.serviceAccountName" . }}

      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}

      {{- with .Values.initContainers }}
      initContainers:
        {{- toYaml . | nindent 8 }}
      {{- end }}

      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}

        ports:
        {{- range .Values.service.ports }}
        - name: {{ .name }}
          containerPort: {{ .targetPort }}
          protocol: {{ .protocol | default "TCP" }}
        {{- end }}

        env:
        {{- range .Values.env }}
        - name: {{ .name }}
          {{- if .value }}
          value: {{ .value | quote }}
          {{- else if .valueFrom }}
          valueFrom:
            {{- toYaml .valueFrom | nindent 12 }}
          {{- end }}
        {{- end }}

        {{- with .Values.envFrom }}
        envFrom:
          {{- toYaml . | nindent 10 }}
        {{- end }}

        resources:
          {{- toYaml .Values.resources | nindent 10 }}

        {{- with .Values.livenessProbe }}
        livenessProbe:
          {{- toYaml . | nindent 10 }}
        {{- end }}

        {{- with .Values.readinessProbe }}
        readinessProbe:
          {{- toYaml . | nindent 10 }}
        {{- end }}

        {{- with .Values.startupProbe }}
        startupProbe:
          {{- toYaml . | nindent 10 }}
        {{- end }}

        {{- with .Values.volumeMounts }}
        volumeMounts:
          {{- toYaml . | nindent 10 }}
        {{- end }}

        securityContext:
          {{- toYaml .Values.securityContext | nindent 10 }}

      {{- with .Values.sidecars }}
      {{- toYaml . | nindent 6 }}
      {{- end }}

      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}

      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}

      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}

      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}

      {{- with .Values.topologySpreadConstraints }}
      topologySpreadConstraints:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

### Helm Values File

```yaml
# values.yaml
replicaCount: 3
revisionHistoryLimit: 10

image:
  repository: company/myapp
  pullPolicy: IfNotPresent
  tag: ""  # Defaults to chart appVersion

imagePullSecrets:
- name: registry-credentials

strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%
    maxUnavailable: 25%

service:
  type: ClusterIP
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP

env:
- name: ENVIRONMENT
  value: production
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: database-credentials
      key: url

envFrom:
- configMapRef:
    name: myapp-config

resources:
  requests:
    memory: 256Mi
    cpu: 200m
  limits:
    memory: 512Mi
    cpu: 500m

livenessProbe:
  httpGet:
    path: /health/live
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: http
  initialDelaySeconds: 10
  periodSeconds: 5

startupProbe:
  httpGet:
    path: /health/startup
    port: http
  periodSeconds: 5
  failureThreshold: 30

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: myapp
        topologyKey: kubernetes.io/hostname

tolerations: []
nodeSelector: {}
topologySpreadConstraints: []

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

## Kubectl Commands Reference

### Deployment Management

```bash
# Create deployment
kubectl apply -f deployment.yaml
kubectl create deployment nginx --image=nginx:1.21 --replicas=3

# Get deployments
kubectl get deployments
kubectl get deploy -A  # All namespaces
kubectl get deploy -n production -o wide
kubectl get deploy --show-labels

# Describe deployment
kubectl describe deployment myapp
kubectl describe deploy myapp -n production

# Edit deployment
kubectl edit deployment myapp
kubectl patch deployment myapp -p '{"spec":{"replicas":5}}'

# Scale deployment
kubectl scale deployment myapp --replicas=10
kubectl scale deployment myapp --replicas=5 --current-replicas=10  # Conditional scale

# Autoscale deployment
kubectl autoscale deployment myapp --min=3 --max=10 --cpu-percent=70

# Delete deployment
kubectl delete deployment myapp
kubectl delete -f deployment.yaml
kubectl delete deployment --all -n development
```

### Rollout Management

```bash
# Update deployment image
kubectl set image deployment/myapp myapp=company/myapp:2.0.0
kubectl set image deployment/myapp *=company/myapp:2.0.0  # All containers

# Update with record (for rollout history)
kubectl set image deployment/myapp myapp=company/myapp:2.0.0 --record

# Check rollout status
kubectl rollout status deployment/myapp
kubectl rollout status deployment/myapp --watch

# View rollout history
kubectl rollout history deployment/myapp
kubectl rollout history deployment/myapp --revision=3

# Rollback to previous version
kubectl rollout undo deployment/myapp

# Rollback to specific revision
kubectl rollout undo deployment/myapp --to-revision=2

# Pause rollout (useful for canary)
kubectl rollout pause deployment/myapp

# Resume rollout
kubectl rollout resume deployment/myapp

# Restart deployment (recreate all pods)
kubectl rollout restart deployment/myapp
```

### Viewing Resources

```bash
# Get ReplicaSets managed by deployment
kubectl get rs -l app=myapp

# Get pods managed by deployment
kubectl get pods -l app=myapp
kubectl get pods -l app=myapp -o wide
kubectl get pods -l app=myapp --field-selector=status.phase=Running

# Watch deployment
kubectl get deployment myapp --watch

# View deployment events
kubectl get events --field-selector involvedObject.name=myapp --sort-by='.lastTimestamp'

# View deployment YAML
kubectl get deployment myapp -o yaml
kubectl get deployment myapp -o json | jq .

# Export deployment (without cluster-specific fields)
kubectl get deployment myapp -o yaml --export
```

### Debugging

```bash
# Check pod logs from deployment
kubectl logs -l app=myapp --tail=100
kubectl logs -l app=myapp -f  # Follow
kubectl logs -l app=myapp --all-containers=true
kubectl logs -l app=myapp --previous  # Previous container logs

# Execute command in pod
kubectl exec -it deployment/myapp -- /bin/bash
kubectl exec -it deployment/myapp -- env
kubectl exec -it deployment/myapp -- cat /etc/config/app.conf

# Port forward to deployment
kubectl port-forward deployment/myapp 8080:8080
kubectl port-forward deployment/myapp 8080:8080 --address 0.0.0.0

# Get deployment conditions
kubectl get deployment myapp -o jsonpath='{.status.conditions[*].type}{"\n"}'
kubectl get deployment myapp -o jsonpath='{.status.conditions[?(@.type=="Progressing")].message}{"\n"}'

# Check why deployment is not progressing
kubectl describe deployment myapp | grep -A 10 Conditions
kubectl get pods -l app=myapp -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# View resource usage
kubectl top pods -l app=myapp
kubectl top pods -l app=myapp --containers
```

### Advanced Operations

```bash
# Set environment variable
kubectl set env deployment/myapp DEBUG=true
kubectl set env deployment/myapp --from=configmap/myapp-config
kubectl set env deployment/myapp --from=secret/myapp-secret

# Set resource limits
kubectl set resources deployment myapp --limits=cpu=500m,memory=512Mi --requests=cpu=200m,memory=256Mi

# Add volume
kubectl set volume deployment/myapp --add --name=config --type=configmap --configmap-name=myapp-config --mount-path=/etc/config

# Update service account
kubectl set serviceaccount deployment myapp myapp-sa

# Label deployment
kubectl label deployment myapp version=v2.0
kubectl label deployment myapp environment=production --overwrite

# Annotate deployment
kubectl annotate deployment myapp kubernetes.io/change-cause="Update to v2.0"

# Create deployment with dry-run
kubectl create deployment test --image=nginx --dry-run=client -o yaml > deployment.yaml

# Diff before apply
kubectl diff -f deployment.yaml

# Apply with server-side apply
kubectl apply -f deployment.yaml --server-side

# Force replace deployment
kubectl replace -f deployment.yaml --force

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/myapp
kubectl wait --for=jsonpath='{.status.readyReplicas}'=5 deployment/myapp
```

## Troubleshooting Guide

### Deployment Not Creating Pods

```bash
# Check deployment status
kubectl describe deployment myapp

# Common issues:
# 1. Insufficient resources
kubectl describe nodes | grep -A 5 "Allocated resources"

# 2. Image pull errors
kubectl get pods -l app=myapp
kubectl describe pod <pod-name> | grep -A 10 Events

# 3. Quota exceeded
kubectl get resourcequota -n production
kubectl describe resourcequota -n production
```

### Pods CrashLooping

```bash
# Check pod status
kubectl get pods -l app=myapp

# View logs
kubectl logs -l app=myapp --tail=100
kubectl logs <pod-name> --previous

# Check events
kubectl describe pod <pod-name>

# Common causes:
# - Application error (check logs)
# - Missing dependencies (init containers)
# - Resource limits too low
# - Liveness probe failing too quickly
```

### Rollout Stuck

```bash
# Check rollout status
kubectl rollout status deployment/myapp

# Check deployment conditions
kubectl get deployment myapp -o yaml | grep -A 10 conditions

# Common issues:
# 1. Insufficient resources for new pods
# 2. Image pull errors
# 3. Readiness probe never succeeding
# 4. Pod Disruption Budget preventing scale down

# Force rollout
kubectl rollout restart deployment/myapp

# Rollback if stuck
kubectl rollout undo deployment/myapp
```

### High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -l app=myapp --containers

# Check resource limits
kubectl get deployment myapp -o jsonpath='{.spec.template.spec.containers[*].resources}'

# Increase limits
kubectl set resources deployment myapp --limits=cpu=1000m,memory=1Gi --requests=cpu=500m,memory=512Mi

# Enable autoscaling
kubectl autoscale deployment myapp --cpu-percent=70 --min=3 --max=10
```

## Best Practices Summary

### Resource Management
- Always set resource requests and limits
- Use VPA (VerticalPodAutoscaler) for recommendations
- Monitor actual usage and adjust accordingly
- Use `ephemeral-storage` limits to prevent disk exhaustion

### Health Checks
- Implement all three probes: startup, liveness, readiness
- Use different endpoints for liveness vs readiness
- Set appropriate timeouts and thresholds
- Don't make probes too aggressive (causes unnecessary restarts)

### Security
- Run as non-root user
- Use read-only root filesystem
- Drop all capabilities, add only required ones
- Use Pod Security Standards/Policies
- Scan images for vulnerabilities
- Use private registries with pull secrets

### High Availability
- Minimum 2-3 replicas for production
- Use pod anti-affinity to spread across nodes
- Use topology spread constraints for zones
- Set appropriate PodDisruptionBudget
- Use multiple availability zones

### Deployment Strategy
- Use RollingUpdate for stateless apps
- Set appropriate maxSurge and maxUnavailable
- Use minReadySeconds to slow rollout
- Keep revision history for rollbacks
- Test in staging environment first
- Use progressive delivery (canary/blue-green)

### Observability
- Add Prometheus annotations for metrics
- Use structured logging
- Include correlation IDs in logs
- Export metrics (latency, error rate, throughput)
- Set up alerts for deployment failures

### GitOps
- Store manifests in version control
- Use ArgoCD or FluxCD for automated deployments
- Implement proper CI/CD pipelines
- Use Helm or Kustomize for templating
- Separate config from code

### Configuration
- Use ConfigMaps for non-sensitive config
- Use Secrets for sensitive data
- Mount configs as volumes (hot reload)
- Version your ConfigMaps/Secrets
- Trigger rollout on config changes (use annotations)

### Labels and Annotations
- Use consistent labeling strategy
- Include app, component, version labels
- Use annotations for metadata
- Tag with team ownership
- Include change-cause annotations

### Testing
- Run smoke tests after deployment
- Use readiness gates for external validation
- Implement automated rollback on metrics degradation
- Test disaster recovery procedures
- Validate resource limits in staging
