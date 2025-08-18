## Advanced Scheduling Comprehensive Guide

### Node Affinity Deep Dive

Node affinity allows you to constrain which nodes your pods can be scheduled on based on node labels.

#### Node Affinity Types

**Required Node Affinity (Hard Constraint):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: node-affinity-required
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: instance-type
            operator: In
            values:
            - m5.large
            - m5.xlarge
          - key: zone
            operator: In
            values:
            - us-west-2a
            - us-west-2b
        - matchExpressions:  # OR condition with first term
          - key: node-type
            operator: In
            values:
            - compute-optimized
  containers:
  - name: app
    image: nginx:1.21
```

**Preferred Node Affinity (Soft Constraint):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: node-affinity-preferred
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100  # Higher weight = higher preference
        preference:
          matchExpressions:
          - key: instance-type
            operator: In
            values:
            - m5.2xlarge
      - weight: 50
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - us-west-2a  # Prefer specific zone
  containers:
  - name: app
    image: nginx:1.21
```

**Combined Required and Preferred:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      affinity:
        nodeAffinity:
          # Must run on SSD-enabled nodes
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: storage-type
                operator: In
                values:
                - ssd
              - key: kubernetes.io/arch
                operator: In
                values:
                - amd64
          # Prefer high-memory instances
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: instance-type
                operator: In
                values:
                - r5.large
                - r5.xlarge
          - weight: 50
            preference:
              matchExpressions:
              - key: zone
                operator: In
                values:
                - us-west-2a
      containers:
      - name: database
        image: postgres:13
        resources:
          requests:
            memory: 2Gi
            cpu: 1
```

#### Node Affinity Operators

- **In**: Label value is in the provided set
- **NotIn**: Label value is not in the provided set  
- **Exists**: Label key exists (value ignored)
- **DoesNotExist**: Label key does not exist
- **Gt**: Label value is greater than provided value (numeric)
- **Lt**: Label value is less than provided value (numeric)

### Pod Affinity and Anti-Affinity

Pod affinity/anti-affinity allows you to constrain pod scheduling based on labels of other pods.

#### Pod Affinity Configuration

**Required Pod Affinity:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
        tier: frontend
    spec:
      affinity:
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - cache
            topologyKey: kubernetes.io/hostname  # Same node
          - labelSelector:
              matchExpressions:
              - key: tier
                operator: In
                values:
                - database
            topologyKey: topology.kubernetes.io/zone  # Same zone
      containers:
      - name: web
        image: nginx:1.21
```

**Preferred Pod Affinity:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 5
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      affinity:
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - database
              topologyKey: topology.kubernetes.io/zone
          - weight: 50
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: component
                  operator: In
                  values:
                  - cache
              topologyKey: kubernetes.io/hostname
      containers:
      - name: api
        image: api-server:latest
```

#### Pod Anti-Affinity for High Availability

**Required Anti-Affinity (Hard Constraint):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: distributed-database
spec:
  replicas: 3
  selector:
    matchLabels:
      app: distributed-database
  template:
    metadata:
      labels:
        app: distributed-database
        component: storage
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - distributed-database
            topologyKey: kubernetes.io/hostname  # Different nodes
          - labelSelector:
              matchExpressions:
              - key: component
                operator: In
                values:
                - storage
            topologyKey: topology.kubernetes.io/zone  # Different zones
      containers:
      - name: database
        image: postgres:13
```

**Preferred Anti-Affinity (Soft Constraint):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 6
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-app
              topologyKey: kubernetes.io/hostname
          - weight: 50
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-app
              topologyKey: topology.kubernetes.io/zone
      containers:
      - name: web
        image: nginx:1.21
```

### Taints and Tolerations Deep Dive

Taints and tolerations work together to ensure pods are not scheduled on inappropriate nodes.

#### Node Taints

**Adding Taints to Nodes:**

```bash
# Add taint to node
kubectl taint nodes node1 key1=value1:NoSchedule
kubectl taint nodes node2 environment=production:NoSchedule
kubectl taint nodes node3 workload=gpu:NoExecute

# Add taint with no value
kubectl taint nodes node4 dedicated:NoSchedule

# Remove taint from node
kubectl taint nodes node1 key1=value1:NoSchedule-
kubectl taint nodes node2 environment-

# List node taints
kubectl describe node node1 | grep Taints
```

**Taint Effects:**

- **NoSchedule**: Pods without matching toleration won't be scheduled
- **PreferNoSchedule**: Soft version - try to avoid scheduling pods without toleration
- **NoExecute**: Existing pods without toleration will be evicted

#### Toleration Configuration

**Basic Tolerations:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: toleration-example
spec:
  tolerations:
  - key: "environment"
    operator: "Equal"
    value: "production"
    effect: "NoSchedule"
  - key: "workload"
    operator: "Equal"
    value: "gpu"
    effect: "NoExecute"
    tolerationSeconds: 3600  # Evict after 1 hour
  containers:
  - name: app
    image: nginx:1.21
```

**Advanced Tolerations:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dedicated-workload
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dedicated-workload
  template:
    metadata:
      labels:
        app: dedicated-workload
    spec:
      tolerations:
      # Tolerate any taint with key "dedicated"
      - key: "dedicated"
        operator: "Exists"
        effect: "NoSchedule"
      # Tolerate specific environment
      - key: "environment"
        operator: "Equal"
        value: "production"
        effect: "NoSchedule"
      # Tolerate and survive eviction for limited time
      - key: "node.kubernetes.io/unreachable"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
      - key: "node.kubernetes.io/not-ready"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
      containers:
      - name: app
        image: production-app:latest
```

**Toleration Operators:**

- **Equal**: Key/value/effect must match exactly
- **Exists**: Only key and effect must match (value ignored)

#### Common Taint Use Cases

**1. Dedicated Nodes for Specific Workloads:**

```bash
# Taint GPU nodes for ML workloads only
kubectl taint nodes gpu-node1 workload=ml:NoSchedule
kubectl taint nodes gpu-node2 workload=ml:NoSchedule
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-training
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ml-training
  template:
    metadata:
      labels:
        app: ml-training
    spec:
      tolerations:
      - key: "workload"
        operator: "Equal"
        value: "ml"
        effect: "NoSchedule"
      nodeSelector:
        accelerator: nvidia-tesla-k80
      containers:
      - name: trainer
        image: tensorflow/tensorflow:latest-gpu
        resources:
          limits:
            nvidia.com/gpu: 1
```

**2. Environment Separation:**

```bash
# Taint production nodes
kubectl taint nodes prod-node1 environment=production:NoSchedule
kubectl taint nodes prod-node2 environment=production:NoSchedule
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: production-app
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: production-app
  template:
    metadata:
      labels:
        app: production-app
    spec:
      tolerations:
      - key: "environment"
        operator: "Equal"
        value: "production"
        effect: "NoSchedule"
      containers:
      - name: app
        image: production-app:v1.0.0
```

### Priority Classes and Preemption

Priority classes enable pod prioritization for scheduling and preemption.

#### Priority Class Configuration

**Creating Priority Classes:**

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000  # Higher values = higher priority
globalDefault: false
description: "High priority class for critical system components"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: medium-priority
value: 500000
globalDefault: false
description: "Medium priority for important applications"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100000
globalDefault: true  # Default for pods without priority class
description: "Low priority for batch jobs and non-critical workloads"
```

**Using Priority Classes:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: critical-app
  template:
    metadata:
      labels:
        app: critical-app
    spec:
      priorityClassName: high-priority
      containers:
      - name: critical-app
        image: critical-service:latest
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
---
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-processing
spec:
  template:
    spec:
      priorityClassName: low-priority
      containers:
      - name: batch-worker
        image: batch-processor:latest
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
      restartPolicy: OnFailure
```

#### Preemption Configuration

**Pod Disruption Budget with Priority:**

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: critical-app-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: critical-app
      priority: high
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: preemptible-workload
spec:
  replicas: 5
  selector:
    matchLabels:
      app: preemptible-workload
  template:
    metadata:
      labels:
        app: preemptible-workload
    spec:
      priorityClassName: low-priority
      containers:
      - name: worker
        image: batch-worker:latest
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
```

### Custom Schedulers

#### Creating Custom Schedulers

**Custom Scheduler Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-scheduler-config
  namespace: kube-system
data:
  config.yaml: |
    apiVersion: kubescheduler.config.k8s.io/v1beta3
    kind: KubeSchedulerConfiguration
    profiles:
    - schedulerName: custom-scheduler
      plugins:
        score:
          enabled:
          - name: NodeResourcesFit
          - name: NodeAffinity
          - name: PodTopologySpread
          disabled:
          - name: NodeResourcesLeastAllocated
        filter:
          enabled:
          - name: NodeResourcesFit
          - name: NodeAffinity
          - name: PodTopologySpread
      pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: LeastAllocated
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-scheduler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: custom-scheduler
  template:
    metadata:
      labels:
        app: custom-scheduler
    spec:
      serviceAccountName: custom-scheduler
      containers:
      - name: custom-scheduler
        image: k8s.gcr.io/kube-scheduler:v1.25.0
        command:
        - kube-scheduler
        - --config=/etc/kubernetes/scheduler-config.yaml
        - --v=2
        volumeMounts:
        - name: config
          mountPath: /etc/kubernetes
      volumes:
      - name: config
        configMap:
          name: custom-scheduler-config
```

**Using Custom Scheduler:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-custom-scheduler
spec:
  replicas: 3
  selector:
    matchLabels:
      app: custom-scheduled-app
  template:
    metadata:
      labels:
        app: custom-scheduled-app
    spec:
      schedulerName: custom-scheduler
      containers:
      - name: app
        image: nginx:1.21
```

### Pod Topology Spread Constraints

Pod topology spread constraints control how pods are spread across nodes, zones, or other topology domains.

#### Basic Topology Spread

**Zone-level Spread:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: distributed-app
spec:
  replicas: 6
  selector:
    matchLabels:
      app: distributed-app
  template:
    metadata:
      labels:
        app: distributed-app
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: distributed-app
      containers:
      - name: app
        image: nginx:1.21
```

**Node-level Spread:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: balanced-app
spec:
  replicas: 8
  selector:
    matchLabels:
      app: balanced-app
  template:
    metadata:
      labels:
        app: balanced-app
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: balanced-app
        minDomains: 4  # Minimum 4 nodes
      containers:
      - name: app
        image: nginx:1.21
```

#### Advanced Topology Spread

**Multi-level Topology Constraints:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-topology-app
spec:
  replicas: 12
  selector:
    matchLabels:
      app: multi-topology-app
  template:
    metadata:
      labels:
        app: multi-topology-app
        version: v1
    spec:
      topologySpreadConstraints:
      # Spread across zones
      - maxSkew: 2
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: multi-topology-app
        minDomains: 3
      # Spread across nodes within zones
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: multi-topology-app
            version: v1
      containers:
      - name: app
        image: nginx:1.21
```

### Node Selectors and Labels

#### Node Labeling Strategies

**Common Node Labels:**

```bash
# Instance type labels
kubectl label nodes node1 instance-type=m5.large
kubectl label nodes node2 instance-type=c5.xlarge
kubectl label nodes node3 instance-type=r5.2xlarge

# Environment labels
kubectl label nodes node1 environment=production
kubectl label nodes node2 environment=staging
kubectl label nodes node3 environment=development

# Workload-specific labels
kubectl label nodes gpu-node1 workload=ml
kubectl label nodes gpu-node2 workload=ml
kubectl label nodes storage-node1 workload=database

# Custom topology labels
kubectl label nodes node1 rack=rack-1
kubectl label nodes node2 rack=rack-2
kubectl label nodes node3 datacenter=dc-east
```

**Node Selector Usage:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-workload
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gpu-workload
  template:
    metadata:
      labels:
        app: gpu-workload
    spec:
      nodeSelector:
        workload: ml
        instance-type: p3.2xlarge
      containers:
      - name: ml-trainer
        image: tensorflow/tensorflow:latest-gpu
        resources:
          limits:
            nvidia.com/gpu: 1
```

### Advanced Scheduling Patterns

#### Multi-Zone Deployment Pattern

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resilient-service
spec:
  replicas: 9
  selector:
    matchLabels:
      app: resilient-service
  template:
    metadata:
      labels:
        app: resilient-service
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                - us-west-2a
                - us-west-2b
                - us-west-2c
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - resilient-service
              topologyKey: topology.kubernetes.io/zone
          - weight: 50
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - resilient-service
              topologyKey: kubernetes.io/hostname
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: resilient-service
      containers:
      - name: service
        image: resilient-app:latest
```

#### Resource-Aware Scheduling Pattern

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-optimized-app
spec:
  replicas: 5
  selector:
    matchLabels:
      app: resource-optimized-app
  template:
    metadata:
      labels:
        app: resource-optimized-app
    spec:
      priorityClassName: medium-priority
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: node.kubernetes.io/instance-type
                operator: In
                values:
                - m5.large
                - m5.xlarge
          - weight: 50
            preference:
              matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                - us-west-2a
      tolerations:
      - key: "node.kubernetes.io/memory-pressure"
        operator: "Exists"
        effect: "NoSchedule"
        tolerationSeconds: 600
      containers:
      - name: app
        image: optimized-app:latest
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

### Troubleshooting Scheduling Issues

#### Debugging Commands

```bash
# Check pod scheduling status
kubectl get pods -o wide
kubectl describe pod <pod-name>

# Check node capacity and allocations
kubectl describe nodes
kubectl top nodes

# Check scheduling events
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl get events --field-selector reason=FailedScheduling

# Check node taints and labels
kubectl describe node <node-name> | grep -A 5 Taints
kubectl get nodes --show-labels

# Check scheduler logs
kubectl logs -n kube-system deployment/kube-scheduler

# Force reschedule pod
kubectl delete pod <pod-name>
kubectl rollout restart deployment/<deployment-name>
```

#### Common Scheduling Issues

**1. Insufficient Resources:**
- Check node resource capacity
- Verify resource requests vs limits
- Review resource quotas

**2. Taint/Toleration Mismatches:**
- Verify node taints
- Check pod tolerations
- Ensure correct operators and effects

**3. Affinity/Anti-affinity Conflicts:**
- Review pod affinity rules
- Check node label availability
- Verify topology keys exist

**4. Pod Topology Spread Violations:**
- Check maxSkew settings
- Verify topology domain availability
- Review labelSelector matching

### DevOps Best Practices

#### Scheduling Strategy Checklist

**✅ High Availability:**
- Use pod anti-affinity for critical services
- Implement multi-zone deployments
- Configure appropriate pod disruption budgets
- Use topology spread constraints

**✅ Resource Optimization:**
- Label nodes appropriately for workload types
- Use node affinity for resource-specific workloads
- Implement priority classes for workload prioritization
- Monitor and optimize resource utilization

**✅ Environment Isolation:**
- Use taints and tolerations for environment separation
- Implement dedicated node pools for different workloads
- Configure appropriate network policies
- Use namespaces for logical separation

**✅ Performance Optimization:**
- Co-locate related services with pod affinity
- Use appropriate instance types for workloads
- Implement efficient scheduling policies
- Monitor scheduling latency and success rates