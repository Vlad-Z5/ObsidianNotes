## Autoscaling & Resource Management Comprehensive Guide

### Horizontal Pod Autoscaler (HPA) Deep Dive

HPA automatically scales the number of pods in a deployment, replica set, or stateful set based on observed CPU utilization, memory usage, or custom metrics.

#### Basic HPA Configuration

**CPU-based HPA:**

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
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

**Memory-based HPA:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: memory-intensive-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: memory-intensive-app
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Advanced HPA with Custom Metrics

**Multi-metric HPA Configuration:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: advanced-web-app-hpa
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
        averageUtilization: 60
  # Memory utilization  
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
  # Custom metric: requests per second
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  # External metric: SQS queue length
  - type: External
    external:
      metric:
        name: sqs_messages_visible
        selector:
          matchLabels:
            queue_name: "processing-queue"
      target:
        type: AverageValue
        averageValue: "30"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
      - type: Pods
        value: 5
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 10
        periodSeconds: 60
      selectPolicy: Max
```

**Custom Metrics Server Configuration:**

```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: app-metrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: web-app
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-adapter-config
  namespace: monitoring
data:
  config.yaml: |
    rules:
    - seriesQuery: 'http_requests_per_second{namespace!="",pod!=""}'
      resources:
        overrides:
          namespace: {resource: "namespace"}
          pod: {resource: "pod"}
      name:
        matches: "^(.*)_per_second"
        as: "requests_per_second"
      metricsQuery: 'sum(<<.Series>>{<<.LabelMatchers>>}) by (<<.GroupBy>>)'
    - seriesQuery: 'queue_messages_visible{queue_name!=""}'
      name:
        as: "sqs_messages_visible"
      metricsQuery: 'avg(<<.Series>>{<<.LabelMatchers>>}) by (<<.GroupBy>>)'
```

#### HPA Troubleshooting and Best Practices

**HPA Status Monitoring:**

```bash
# Check HPA status
kubectl get hpa
kubectl describe hpa web-app-hpa

# Monitor scaling events
kubectl get events --field-selector involvedObject.kind=HorizontalPodAutoscaler

# Check metrics availability
kubectl top pods
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods
```

**DevOps HPA Best Practices:**

- Set appropriate resource requests/limits on target pods
- Use stabilization windows to prevent flapping
- Monitor scaling metrics and adjust thresholds based on traffic patterns
- Test scaling behavior under load
- Use multiple metrics for more accurate scaling decisions
- Set reasonable min/max replica bounds

### Vertical Pod Autoscaler (VPA) Deep Dive

VPA automatically adjusts CPU and memory requests/limits for containers based on usage patterns.

#### VPA Configuration

**Basic VPA Setup:**

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
    updateMode: "Auto"  # Auto, Recreate, Initial, Off
  resourcePolicy:
    containerPolicies:
    - containerName: web-server
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
      controlledResources: ["cpu", "memory"]
      controlledValues: RequestsAndLimits
```

**VPA with Custom Resource Policies:**

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: database-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: postgres-db
  updatePolicy:
    updateMode: "Initial"  # Only set resources on pod creation
  resourcePolicy:
    containerPolicies:
    - containerName: postgres
      minAllowed:
        cpu: 500m
        memory: 1Gi
      maxAllowed:
        cpu: 4
        memory: 8Gi
      controlledResources: ["memory"]
      controlledValues: RequestsOnly
    - containerName: metrics-exporter
      mode: "Off"  # Don't autoscale this container
```

**VPA Installation:**

```bash
# Install VPA components
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler/
./hack/vpa-install.sh

# Verify VPA installation
kubectl get pods -n kube-system | grep vpa
kubectl get crd | grep verticalpodautoscaler
```

#### VPA Modes and Strategies

**Update Modes:**

1. **Auto**: VPA assigns resource requests on pod creation and updates them on existing pods by evicting and recreating them
2. **Recreate**: VPA assigns resource requests on pod creation and updates them by evicting pods when requested resources differ significantly
3. **Initial**: VPA only assigns resource requests on pod creation and never changes them
4. **Off**: VPA doesn't automatically change resource requirements, only provides recommendations

**VPA Recommendations Analysis:**

```bash
# Check VPA recommendations
kubectl describe vpa web-app-vpa

# Get detailed recommendations
kubectl get vpa web-app-vpa -o yaml
```

### Cluster Autoscaler Deep Dive

Cluster Autoscaler automatically adjusts the number of nodes in a cluster when pods fail to schedule due to insufficient resources.

#### Cloud Provider Configurations

**AWS EKS Cluster Autoscaler:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    app: cluster-autoscaler
spec:
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
      annotations:
        prometheus.io/scrape: 'true'
        prometheus.io/port: '8085'
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
        name: cluster-autoscaler
        resources:
          limits:
            cpu: 100m
            memory: 300Mi
          requests:
            cpu: 100m
            memory: 300Mi
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/eks-cluster-name
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
        env:
        - name: AWS_REGION
          value: us-west-2
```

**Azure AKS Cluster Autoscaler:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
        name: cluster-autoscaler
        resources:
          limits:
            cpu: 100m
            memory: 300Mi
          requests:
            cpu: 100m
            memory: 300Mi
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=azure
        - --scan-interval=10s
        - --expander=random
        - --skip-nodes-with-local-storage=false
        - --skip-nodes-with-system-pods=false
        env:
        - name: ARM_SUBSCRIPTION_ID
          valueFrom:
            secretKeyRef:
              name: cluster-autoscaler-azure
              key: SubscriptionID
        - name: ARM_RESOURCE_GROUP
          valueFrom:
            secretKeyRef:
              name: cluster-autoscaler-azure
              key: ResourceGroup
```

**GKE Cluster Autoscaler:**

```bash
# Enable cluster autoscaler on GKE
gcloud container clusters update my-cluster \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=10 \
    --zone=us-central1-a

# Configure multiple node pools
gcloud container node-pools update default-pool \
    --cluster=my-cluster \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5 \
    --zone=us-central1-a
```

#### Cluster Autoscaler Configuration Options

**Advanced Configuration:**

```yaml
command:
- ./cluster-autoscaler
- --v=4
- --stderrthreshold=info
- --cloud-provider=aws
- --skip-nodes-with-local-storage=false
- --expander=least-waste
- --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/my-cluster
- --balance-similar-node-groups
- --skip-nodes-with-system-pods=false
- --scale-down-enabled=true
- --scale-down-delay-after-add=10m
- --scale-down-unneeded-time=10m
- --scale-down-utilization-threshold=0.5
- --scale-down-gpu-utilization-threshold=0.5
- --scale-down-delay-after-delete=10s
- --scale-down-delay-after-failure=3m
- --max-node-provision-time=15m
- --max-empty-bulk-delete=10
- --max-graceful-termination-sec=600
```

**Expander Strategies:**

- **random**: Random selection among suitable node groups
- **most-pods**: Select node group that would schedule the most pods
- **least-waste**: Select node group with least wasted CPU/memory
- **price**: Select cheapest node group (cloud provider specific)
- **priority**: Use configured priorities

### Resource Management Best Practices

#### Resource Requests and Limits

**Proper Resource Configuration:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-managed-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: resource-managed-app
  template:
    metadata:
      labels:
        app: resource-managed-app
    spec:
      containers:
      - name: web-server
        image: nginx:1.21
        resources:
          requests:
            cpu: 100m      # Guaranteed CPU
            memory: 128Mi  # Guaranteed memory
          limits:
            cpu: 500m      # Maximum CPU
            memory: 512Mi  # Maximum memory
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

#### Quality of Service (QoS) Classes

**Guaranteed QoS:**

```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 500m    # Same as requests
    memory: 1Gi  # Same as requests
```

**Burstable QoS:**

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m    # Higher than requests
    memory: 512Mi # Higher than requests
```

**BestEffort QoS:**

```yaml
# No resources specified - not recommended for production
resources: {}
```

#### Pod Disruption Budgets (PDB)

**PDB Configuration:**

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-app-pdb
spec:
  minAvailable: 2  # Minimum pods that must remain available
  selector:
    matchLabels:
      app: web-app
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: database-pdb
spec:
  maxUnavailable: 1  # Maximum pods that can be unavailable
  selector:
    matchLabels:
      app: database
```

### Advanced Autoscaling Patterns

#### Predictive Scaling with Scheduled Jobs

**CronJob for Predictive Scaling:**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: morning-scale-up
spec:
  schedule: "0 8 * * 1-5"  # 8 AM on weekdays
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scaler
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              kubectl patch deployment web-app -p '{"spec":{"replicas":10}}'
              kubectl patch hpa web-app-hpa -p '{"spec":{"minReplicas":5}}'
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: evening-scale-down
spec:
  schedule: "0 20 * * *"  # 8 PM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scaler
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              kubectl patch hpa web-app-hpa -p '{"spec":{"minReplicas":2}}'
          restartPolicy: OnFailure
```

#### Multi-Dimensional Autoscaling

**KEDA (Kubernetes Event-Driven Autoscaling):**

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: queue-scaler
spec:
  scaleTargetRef:
    name: queue-processor
  minReplicaCount: 1
  maxReplicaCount: 30
  triggers:
  - type: rabbitmq
    metadata:
      protocol: amqp
      queueName: processing-queue
      mode: QueueLength
      value: "5"
    authenticationRef:
      name: rabbitmq-auth
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: http_requests_per_second
      threshold: '100'
      query: sum(rate(http_requests_total[1m]))
```

### Monitoring and Optimization

#### Autoscaling Metrics and Monitoring

**Custom Metrics Dashboard:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: autoscaling-dashboard
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "Kubernetes Autoscaling",
        "panels": [
          {
            "title": "HPA Current Replicas",
            "type": "graph",
            "targets": [
              {
                "expr": "kube_horizontalpodautoscaler_status_current_replicas",
                "legendFormat": "{{horizontalpodautoscaler}}"
              }
            ]
          },
          {
            "title": "HPA Desired Replicas",
            "type": "graph",
            "targets": [
              {
                "expr": "kube_horizontalpodautoscaler_status_desired_replicas",
                "legendFormat": "{{horizontalpodautoscaler}}"
              }
            ]
          },
          {
            "title": "Node Count",
            "type": "graph",
            "targets": [
              {
                "expr": "kube_node_info",
                "legendFormat": "Nodes"
              }
            ]
          }
        ]
      }
    }
```

#### Resource Optimization Commands

```bash
# Analyze resource usage
kubectl top nodes --sort-by=cpu
kubectl top pods --all-namespaces --sort-by=cpu

# Check resource recommendations
kubectl describe vpa web-app-vpa

# Monitor HPA behavior
kubectl get hpa --watch
kubectl describe hpa web-app-hpa

# Cluster autoscaler status
kubectl -n kube-system logs deployment/cluster-autoscaler

# Resource utilization analysis
kubectl get pods --all-namespaces -o json | \
  jq '.items[] | select(.status.phase=="Running") | 
      {name: .metadata.name, 
       namespace: .metadata.namespace,
       cpu_request: .spec.containers[0].resources.requests.cpu,
       memory_request: .spec.containers[0].resources.requests.memory}'
```

### DevOps Autoscaling Best Practices

#### Production Checklist

**✅ HPA Best Practices:**
- Set appropriate CPU/memory targets (60-80%)
- Use stabilization windows to prevent flapping
- Monitor and tune scaling policies
- Test scaling under various load conditions
- Use multiple metrics for accurate scaling
- Set reasonable min/max replica bounds

**✅ VPA Best Practices:**
- Start with "Initial" mode in production
- Set appropriate min/max resource bounds
- Monitor resource waste and utilization
- Use VPA recommendations to right-size applications
- Avoid VPA on critical stateful workloads initially
- Test VPA behavior in staging first

**✅ Cluster Autoscaler Best Practices:**
- Configure appropriate node group sizes
- Use node affinity and taints for workload placement
- Monitor scaling events and node utilization
- Set up proper IAM roles and permissions
- Use multiple node groups for different workload types
- Configure pod disruption budgets

**✅ Resource Management Best Practices:**
- Always set resource requests and limits
- Use appropriate QoS classes
- Monitor resource utilization continuously
- Right-size applications based on actual usage
- Implement proper monitoring and alerting
- Use resource quotas for namespace isolation

#### Cost Optimization Strategies

**1. Right-sizing Applications:**
- Use VPA to identify optimal resource requirements
- Regular review of resource requests vs actual usage
- Implement resource quotas to prevent over-provisioning

**2. Efficient Scaling Policies:**
- Use conservative scaling policies to prevent over-scaling
- Implement predictive scaling for known traffic patterns
- Use spot instances for non-critical workloads

**3. Node Optimization:**
- Use appropriate instance types for workloads
- Implement bin packing for better resource utilization
- Use cluster autoscaler with least-waste expander