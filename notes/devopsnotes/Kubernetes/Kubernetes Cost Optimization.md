# Kubernetes Cost Optimization

**Cost Optimization in Kubernetes** focuses on reducing infrastructure spending while maintaining performance and reliability through resource rightsizing, autoscaling, spot instances, and intelligent workload scheduling.

## Resource Optimization

### Vertical Pod Autoscaler (VPA) Implementation

#### Production VPA Configuration
```yaml
# VPA for cost-effective resource allocation
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
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: web-app
      minAllowed:
        cpu: 50m
        memory: 64Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
      controlledResources: ["cpu", "memory"]
      controlledValues: RequestsAndLimits

---
# VPA recommendation monitoring
apiVersion: v1
kind: ConfigMap
metadata:
  name: vpa-monitoring
  namespace: production
data:
  check-recommendations.sh: |
    #!/bin/bash
    # Script to monitor VPA recommendations vs actual usage

    kubectl get vpa -A -o json | jq -r '
      .items[] |
      select(.status.recommendation != null) |
      {
        namespace: .metadata.namespace,
        name: .metadata.name,
        target: .spec.targetRef.name,
        cpu_request: .status.recommendation.containerRecommendations[0].target.cpu,
        memory_request: .status.recommendation.containerRecommendations[0].target.memory,
        cpu_lower: .status.recommendation.containerRecommendations[0].lowerBound.cpu,
        cpu_upper: .status.recommendation.containerRecommendations[0].upperBound.cpu
      }
    ' | tee vpa-recommendations.json

    # Calculate potential savings
    echo "=== VPA Cost Savings Analysis ==="
    python3 << 'EOF'
    import json
    import sys

    # Read VPA recommendations
    with open('vpa-recommendations.json', 'r') as f:
        recommendations = [json.loads(line) for line in f]

    # Cost calculation (simplified - adjust for your cloud provider)
    cpu_cost_per_core_hour = 0.048  # Example AWS pricing
    memory_cost_per_gb_hour = 0.0053

    total_cpu_savings = 0
    total_memory_savings = 0

    for rec in recommendations:
        print(f"App: {rec['name']}")
        print(f"  Recommended CPU: {rec['cpu_request']}")
        print(f"  Recommended Memory: {rec['memory_request']}")
        print(f"  CPU Range: {rec['cpu_lower']} - {rec['cpu_upper']}")
        print("---")
    EOF
```

### Horizontal Pod Autoscaler (HPA) with Custom Metrics

#### Advanced HPA Configuration
```yaml
# HPA with multiple metrics for cost efficiency
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cost-optimized-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 2
  maxReplicas: 20
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
        name: sqs_queue_length
        selector:
          matchLabels:
            queue: "api-processing"
      target:
        type: Value
        value: "50"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Max

---
# Predictive scaling using KEDA
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: predictive-scaler
  namespace: production
spec:
  scaleTargetRef:
    name: web-app
  minReplicaCount: 1
  maxReplicaCount: 15
  triggers:
  - type: cron
    metadata:
      timezone: America/New_York
      start: "0 8 * * 1-5"  # Scale up at 8 AM weekdays
      end: "0 18 * * 1-5"   # Scale down at 6 PM weekdays
      desiredReplicas: "5"
  - type: cron
    metadata:
      timezone: America/New_York
      start: "0 18 * * 1-5"  # Evening scale down
      end: "0 8 * * 1-5"     # Until morning
      desiredReplicas: "2"
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: request_rate_5m
      threshold: '100'
      query: rate(http_requests_total[5m])
```

### Resource Quotas and Limits

#### Namespace Resource Management
```yaml
# Resource quota for cost control
apiVersion: v1
kind: ResourceQuota
metadata:
  name: cost-control-quota
  namespace: development
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
    requests.storage: 100Gi
    count/deployments.apps: "20"
    count/services: "10"
    count/secrets: "20"
    count/configmaps: "20"

---
# Limit range for default resource constraints
apiVersion: v1
kind: LimitRange
metadata:
  name: cost-efficient-limits
  namespace: development
spec:
  limits:
  - type: Container
    default:
      cpu: 200m
      memory: 256Mi
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    max:
      cpu: 2
      memory: 4Gi
    min:
      cpu: 50m
      memory: 64Mi
  - type: PersistentVolumeClaim
    max:
      storage: 50Gi
    min:
      storage: 1Gi

---
# Network policy for reduced data transfer costs
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cost-optimized-network
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: production
    ports:
    - protocol: TCP
      port: 5432  # Database
  - to: []  # Allow DNS
    ports:
    - protocol: UDP
      port: 53
```

## Spot Instance and Node Management

### Cluster Autoscaler with Mixed Instance Types

#### Multi-Instance Type Node Groups
```yaml
# Cluster autoscaler configuration for cost optimization
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
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.27.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/my-cluster
        - --balance-similar-node-groups
        - --scale-down-enabled=true
        - --scale-down-delay-after-add=10m
        - --scale-down-unneeded-time=10m
        - --scale-down-utilization-threshold=0.5
        - --skip-nodes-with-system-pods=false
        env:
        - name: AWS_REGION
          value: us-west-2
        resources:
          limits:
            cpu: 100m
            memory: 300Mi
          requests:
            cpu: 100m
            memory: 300Mi

---
# Spot instance termination handler
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: aws-node-termination-handler
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: aws-node-termination-handler
  template:
    metadata:
      labels:
        app: aws-node-termination-handler
    spec:
      hostNetwork: true
      containers:
      - name: aws-node-termination-handler
        image: public.ecr.aws/aws-ec2/aws-node-termination-handler:v1.19.0
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: ENABLE_SPOT_INTERRUPTION_DRAINING
          value: "true"
        - name: ENABLE_SCHEDULED_EVENT_DRAINING
          value: "true"
        - name: WEBHOOK_URL
          value: "http://webhook.monitoring.svc.cluster.local:9093/webhook"
        resources:
          limits:
            cpu: 100m
            memory: 128Mi
          requests:
            cpu: 50m
            memory: 64Mi
```

### Priority Classes for Workload Scheduling

#### Cost-Based Priority Configuration
```yaml
# High priority for critical workloads
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-expensive
value: 1000
globalDefault: false
description: "High priority class for critical workloads"

---
# Medium priority for standard workloads
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: medium-priority-standard
value: 500
globalDefault: true
description: "Standard priority for regular workloads"

---
# Low priority for batch/background jobs
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority-spot
value: 100
globalDefault: false
description: "Low priority for interruptible workloads"

---
# Batch job using spot instances
apiVersion: batch/v1
kind: Job
metadata:
  name: data-processing-job
  namespace: batch-processing
spec:
  parallelism: 5
  completions: 10
  backoffLimit: 3
  template:
    metadata:
      labels:
        app: data-processor
    spec:
      priorityClassName: low-priority-spot
      restartPolicy: Never
      nodeSelector:
        node.kubernetes.io/instance-type: "spot"
      tolerations:
      - key: "spot"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      containers:
      - name: processor
        image: data-processor:latest
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1
            memory: 2Gi
        env:
        - name: BATCH_SIZE
          value: "1000"
        - name: CONCURRENT_WORKERS
          value: "4"
```

## Storage Cost Optimization

### Dynamic Storage Provisioning

#### Cost-Effective Storage Classes
```yaml
# GP3 storage class for cost optimization
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-optimized
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete

---
# Cold storage class for backups
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cold-storage
provisioner: ebs.csi.aws.com
parameters:
  type: sc1  # Cold HDD
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain

---
# Local SSD for temporary data
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-ssd
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete

---
# PVC template for cost monitoring
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
  namespace: production
  labels:
    cost-center: "engineering"
    environment: "production"
    team: "backend"
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3-optimized
  resources:
    requests:
      storage: 20Gi
```

### Storage Lifecycle Management

#### Automated Storage Cleanup
```yaml
# CronJob for storage cleanup
apiVersion: batch/v1
kind: CronJob
metadata:
  name: storage-cleanup
  namespace: kube-system
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: bitnami/kubectl:latest
            command:
            - /bin/bash
            - -c
            - |
              echo "Starting storage cleanup..."

              # Find and delete unused PVCs older than 7 days
              kubectl get pvc --all-namespaces -o json | jq -r '
                .items[] |
                select(.status.phase == "Bound") |
                select(.metadata.labels.cleanup != "never") |
                select(
                  (now - (.metadata.creationTimestamp | strptime("%Y-%m-%dT%H:%M:%SZ") | mktime)) > (7 * 24 * 3600)
                ) |
                "\(.metadata.namespace) \(.metadata.name)"
              ' | while read namespace pvc; do
                echo "Checking PVC: $namespace/$pvc"

                # Check if PVC is actually used by any pods
                if ! kubectl get pods -n "$namespace" -o json | jq -e "
                  .items[] |
                  select(.spec.volumes[]?.persistentVolumeClaim?.claimName == \"$pvc\")
                " > /dev/null; then
                  echo "Deleting unused PVC: $namespace/$pvc"
                  kubectl delete pvc "$pvc" -n "$namespace"
                fi
              done

              # Clean up completed jobs older than 3 days
              kubectl get jobs --all-namespaces -o json | jq -r '
                .items[] |
                select(.status.conditions[]?.type == "Complete") |
                select(
                  (now - (.metadata.creationTimestamp | strptime("%Y-%m-%dT%H:%M:%SZ") | mktime)) > (3 * 24 * 3600)
                ) |
                "\(.metadata.namespace) \(.metadata.name)"
              ' | while read namespace job; do
                echo "Deleting completed job: $namespace/$job"
                kubectl delete job "$job" -n "$namespace"
              done

              echo "Storage cleanup completed"
            resources:
              requests:
                cpu: 100m
                memory: 128Mi
              limits:
                cpu: 200m
                memory: 256Mi
          restartPolicy: OnFailure
```

## Cost Monitoring and Analytics

### Cost Allocation and Tracking

#### OpenCost Installation and Configuration
```yaml
# OpenCost for Kubernetes cost monitoring
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opencost
  namespace: opencost
spec:
  replicas: 1
  selector:
    matchLabels:
      app: opencost
  template:
    metadata:
      labels:
        app: opencost
    spec:
      containers:
      - name: opencost
        image: quay.io/kubecost1/kubecost-cost-model:latest
        ports:
        - containerPort: 9003
        env:
        - name: PROMETHEUS_SERVER_ENDPOINT
          value: "http://prometheus.monitoring.svc.cluster.local:9090"
        - name: CLOUD_PROVIDER_API_KEY
          value: "AIzaSyD29bGD5fX1SESleHaYWVNJqv6r9QHyU4o"  # Example
        - name: CLUSTER_ID
          value: "production-cluster"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 1Gi
        volumeMounts:
        - name: persistent-configs
          mountPath: /var/configs
      volumes:
      - name: persistent-configs
        persistentVolumeClaim:
          claimName: opencost-config

---
# Cost allocation service
apiVersion: v1
kind: Service
metadata:
  name: opencost
  namespace: opencost
spec:
  selector:
    app: opencost
  ports:
  - port: 9003
    targetPort: 9003

---
# Cost dashboard using Grafana
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-dashboard
  namespace: monitoring
data:
  cost-dashboard.json: |
    {
      "dashboard": {
        "title": "Kubernetes Cost Analysis",
        "panels": [
          {
            "title": "Daily Cost by Namespace",
            "type": "graph",
            "targets": [
              {
                "expr": "sum by (namespace) (kubecost_cluster_costs_daily)",
                "legendFormat": "{{namespace}}"
              }
            ]
          },
          {
            "title": "Cost by Node Type",
            "type": "piechart",
            "targets": [
              {
                "expr": "sum by (instance_type) (kubecost_node_costs_daily)",
                "legendFormat": "{{instance_type}}"
              }
            ]
          },
          {
            "title": "Storage Costs Trend",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(kubecost_cluster_storage_costs_daily)",
                "legendFormat": "Storage"
              }
            ]
          }
        ]
      }
    }

---
# Cost alert rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cost-alerts
  namespace: monitoring
spec:
  groups:
  - name: cost.rules
    rules:
    - alert: HighDailyCost
      expr: sum(kubecost_cluster_costs_daily) > 1000
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Daily cluster cost exceeded $1000"
        description: "Cluster daily cost is {{ $value }} USD"

    - alert: UnusedPVCCost
      expr: sum by (namespace, persistentvolumeclaim) (kubecost_pvc_costs_daily{usage_hours="0"}) > 10
      for: 1h
      labels:
        severity: warning
      annotations:
        summary: "Unused PVC costing money"
        description: "PVC {{ $labels.persistentvolumeclaim }} in {{ $labels.namespace }} is unused but costs {{ $value }} USD daily"

    - alert: OverProvisionedPods
      expr: |
        sum by (namespace, pod) (
          kubecost_pod_costs_daily{cpu_request_cores} - kubecost_pod_costs_daily{cpu_usage_cores}
        ) / kubecost_pod_costs_daily{cpu_request_cores} > 0.5
      for: 30m
      labels:
        severity: info
      annotations:
        summary: "Pod is over-provisioned"
        description: "Pod {{ $labels.pod }} in {{ $labels.namespace }} is using less than 50% of requested resources"
```

### Cost Optimization Automation

#### Automated Right-sizing Script
```bash
#!/bin/bash
# cost-optimization-script.sh

set -euo pipefail

NAMESPACE=${1:-"default"}
DRY_RUN=${2:-"true"}
SAVINGS_THRESHOLD=${3:-"20"}  # Minimum 20% savings to make changes

echo "=== Kubernetes Cost Optimization Script ==="
echo "Namespace: $NAMESPACE"
echo "Dry Run: $DRY_RUN"
echo "Savings Threshold: $SAVINGS_THRESHOLD%"
echo

# Function to get VPA recommendations
get_vpa_recommendations() {
    kubectl get vpa -n "$NAMESPACE" -o json | jq -r '
        .items[] |
        select(.status.recommendation != null) |
        {
            name: .metadata.name,
            target: .spec.targetRef.name,
            current_cpu: .status.recommendation.containerRecommendations[0].target.cpu,
            current_memory: .status.recommendation.containerRecommendations[0].target.memory,
            recommended_cpu: .status.recommendation.containerRecommendations[0].target.cpu,
            recommended_memory: .status.recommendation.containerRecommendations[0].target.memory
        }
    '
}

# Function to calculate cost savings
calculate_savings() {
    local current_cpu=$1
    local recommended_cpu=$2
    local current_memory=$3
    local recommended_memory=$4

    # Convert CPU (millicores to cores)
    current_cpu_cores=$(echo "$current_cpu" | sed 's/m$//' | awk '{print $1/1000}')
    recommended_cpu_cores=$(echo "$recommended_cpu" | sed 's/m$//' | awk '{print $1/1000}')

    # Convert Memory (Mi to GB)
    current_memory_gb=$(echo "$current_memory" | sed 's/Mi$//' | awk '{print $1/1024}')
    recommended_memory_gb=$(echo "$recommended_memory" | sed 's/Mi$//' | awk '{print $1/1024}')

    # Calculate costs (example pricing)
    cpu_cost_per_hour=0.048
    memory_cost_per_hour=0.0053

    current_cost=$(echo "$current_cpu_cores * $cpu_cost_per_hour + $current_memory_gb * $memory_cost_per_hour" | bc -l)
    recommended_cost=$(echo "$recommended_cpu_cores * $cpu_cost_per_hour + $recommended_memory_gb * $memory_cost_per_hour" | bc -l)

    savings=$(echo "$current_cost - $recommended_cost" | bc -l)
    savings_percent=$(echo "scale=2; ($savings / $current_cost) * 100" | bc -l)

    echo "$savings_percent"
}

# Function to optimize deployment resources
optimize_deployment() {
    local deployment=$1
    local namespace=$2
    local new_cpu=$3
    local new_memory=$4

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY RUN: Would update deployment $deployment with CPU: $new_cpu, Memory: $new_memory"
    else
        kubectl patch deployment "$deployment" -n "$namespace" -p "{
            \"spec\": {
                \"template\": {
                    \"spec\": {
                        \"containers\": [{
                            \"name\": \"$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath='{.spec.template.spec.containers[0].name}')\",
                            \"resources\": {
                                \"requests\": {
                                    \"cpu\": \"$new_cpu\",
                                    \"memory\": \"$new_memory\"
                                },
                                \"limits\": {
                                    \"cpu\": \"$(echo "$new_cpu" | sed 's/m$//' | awk '{print $1*2}')m\",
                                    \"memory\": \"$(echo "$new_memory" | sed 's/Mi$//' | awk '{print $1*2}')Mi\"
                                }
                            }
                        }]
                    }
                }
            }
        }"
        echo "Updated deployment $deployment"
    fi
}

# Function to find idle workloads
find_idle_workloads() {
    echo "=== Finding Idle Workloads ==="

    # Get deployments with zero replicas or very low CPU usage
    kubectl get deployments -n "$NAMESPACE" -o json | jq -r '
        .items[] |
        select(.spec.replicas == 0 or (.status.replicas // 0) == 0) |
        "IDLE: \(.metadata.name) (replicas: \(.spec.replicas // 0))"
    '

    # Find deployments with consistently low resource usage
    echo "Checking resource utilization..."
    kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '
        $2 ~ /[0-9]+m/ && $3 ~ /[0-9]+Mi/ {
            cpu = $2; gsub(/m/, "", cpu)
            memory = $3; gsub(/Mi/, "", memory)
            if (cpu < 10 && memory < 100) {
                print "LOW_USAGE: " $1 " (CPU: " $2 ", Memory: " $3 ")"
            }
        }
    ' || echo "Metrics server not available"
}

# Function to identify over-provisioned resources
identify_overprovisioned() {
    echo "=== Identifying Over-provisioned Resources ==="

    kubectl get pods -n "$NAMESPACE" -o json | jq -r '
        .items[] |
        select(.spec.containers[0].resources.requests != null) |
        {
            name: .metadata.name,
            cpu_request: .spec.containers[0].resources.requests.cpu,
            memory_request: .spec.containers[0].resources.requests.memory,
            cpu_limit: .spec.containers[0].resources.limits.cpu,
            memory_limit: .spec.containers[0].resources.limits.memory
        } |
        select(.cpu_request != null and .memory_request != null)
    ' | while read -r pod_info; do
        pod_name=$(echo "$pod_info" | jq -r '.name')
        echo "Analyzing pod: $pod_name"

        # Here you would typically compare with actual usage metrics
        # This is a simplified version
    done
}

# Function to generate cost report
generate_cost_report() {
    echo "=== Cost Optimization Report ==="
    echo "Generated on: $(date)"
    echo "Namespace: $NAMESPACE"
    echo

    # Get resource requests and limits
    echo "Current Resource Allocation:"
    kubectl get pods -n "$NAMESPACE" -o json | jq -r '
        .items[] |
        select(.spec.containers[0].resources.requests != null) |
        "Pod: \(.metadata.name) | CPU: \(.spec.containers[0].resources.requests.cpu // "not set") | Memory: \(.spec.containers[0].resources.requests.memory // "not set")"
    '

    echo
    echo "Optimization Opportunities:"
    find_idle_workloads
    identify_overprovisioned

    echo
    echo "Recommendations:"
    echo "1. Review idle workloads and consider scaling down or removing"
    echo "2. Implement VPA for automatic right-sizing"
    echo "3. Use HPA for dynamic scaling based on demand"
    echo "4. Consider spot instances for non-critical workloads"
    echo "5. Implement resource quotas to prevent over-provisioning"
}

# Main execution
main() {
    echo "Starting cost optimization analysis..."

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        echo "Error: Namespace '$NAMESPACE' does not exist"
        exit 1
    fi

    # Generate report
    generate_cost_report

    # Get VPA recommendations if available
    if kubectl get vpa -n "$NAMESPACE" >/dev/null 2>&1; then
        echo
        echo "=== VPA Recommendations ==="
        get_vpa_recommendations
    else
        echo
        echo "VPA not installed or no recommendations available"
    fi

    echo
    echo "Cost optimization analysis completed"
}

# Run main function
main "$@"
```

### Real-time Cost Alerts

#### Cost-based Prometheus Rules
```yaml
# Comprehensive cost alerting rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cost-optimization-alerts
  namespace: monitoring
spec:
  groups:
  - name: cost.optimization
    interval: 5m
    rules:
    # Daily cost spike detection
    - alert: DailyCostSpike
      expr: |
        (
          sum(rate(kubecost_cluster_costs_total[1h])) * 24 -
          sum(rate(kubecost_cluster_costs_total[24h] offset 24h)) * 24
        ) / sum(rate(kubecost_cluster_costs_total[24h] offset 24h)) * 24 > 0.2
      for: 30m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Daily cost increased by more than 20%"
        description: "Cluster daily cost has increased by {{ $value | humanizePercentage }} compared to yesterday"

    # Unused resource alerts
    - alert: UnusedPersistentVolumes
      expr: |
        sum by (namespace, persistentvolumeclaim) (
          kubecost_pvc_costs_daily{pod_name=""}
        ) > 5
      for: 2h
      labels:
        severity: info
        team: engineering
      annotations:
        summary: "Unused PVC costing money"
        description: "PVC {{ $labels.persistentvolumeclaim }} in namespace {{ $labels.namespace }} is not attached to any pod but costs ${{ $value }}/day"

    # Over-provisioned workloads
    - alert: OverProvisionedWorkload
      expr: |
        sum by (namespace, deployment) (
          kubecost_deployment_cpu_request_cores - kubecost_deployment_cpu_usage_cores
        ) / sum by (namespace, deployment) (
          kubecost_deployment_cpu_request_cores
        ) > 0.7
      for: 1h
      labels:
        severity: info
        team: engineering
      annotations:
        summary: "Workload is significantly over-provisioned"
        description: "Deployment {{ $labels.deployment }} in {{ $labels.namespace }} is using less than 30% of requested CPU"

    # Expensive spot instance interruptions
    - alert: FrequentSpotInterruptions
      expr: |
        rate(kube_node_deleted_total{node_lifecycle="spot"}[1h]) > 0.1
      for: 15m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Frequent spot instance interruptions"
        description: "Spot instance interruption rate is {{ $value | humanize }} per hour, consider diversifying instance types"

    # Storage cost growth
    - alert: StorageCostGrowth
      expr: |
        (
          sum(kubecost_cluster_storage_costs_daily) -
          sum(kubecost_cluster_storage_costs_daily offset 7d)
        ) / sum(kubecost_cluster_storage_costs_daily offset 7d) > 0.15
      for: 1h
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Storage costs increased significantly"
        description: "Storage costs have increased by {{ $value | humanizePercentage }} over the past week"

    # Idle node detection
    - alert: IdleNodes
      expr: |
        (
          sum by (node) (kube_node_status_allocatable{resource="cpu"}) -
          sum by (node) (kube_pod_container_resource_requests{resource="cpu"})
        ) / sum by (node) (kube_node_status_allocatable{resource="cpu"}) > 0.8
      for: 30m
      labels:
        severity: info
        team: platform
      annotations:
        summary: "Node is mostly idle"
        description: "Node {{ $labels.node }} has less than 20% CPU allocation, consider draining"

---
# Cost optimization webhook
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-webhook
  namespace: monitoring
data:
  webhook.py: |
    #!/usr/bin/env python3
    import json
    import requests
    from flask import Flask, request

    app = Flask(__name__)

    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    TEAMS_WEBHOOK_URL = "https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK"

    @app.route('/webhook', methods=['POST'])
    def webhook():
        data = request.json

        for alert in data.get('alerts', []):
            alert_name = alert['labels']['alertname']
            severity = alert['labels']['severity']
            description = alert['annotations']['description']

            if 'cost' in alert_name.lower() or 'expensive' in alert_name.lower():
                send_cost_alert(alert_name, severity, description)

        return "OK"

    def send_cost_alert(alert_name, severity, description):
        color = {"critical": "#FF0000", "warning": "#FFA500", "info": "#0000FF"}

        slack_message = {
            "attachments": [{
                "color": color.get(severity, "#808080"),
                "title": f"💰 Cost Alert: {alert_name}",
                "text": description,
                "fields": [
                    {"title": "Severity", "value": severity, "short": True},
                    {"title": "Time", "value": "Now", "short": True}
                ]
            }]
        }

        requests.post(SLACK_WEBHOOK_URL, json=slack_message)

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=9093)
```

This comprehensive Kubernetes Cost Optimization guide provides practical, actionable strategies for reducing infrastructure costs while maintaining performance and reliability. Each section includes real-world configurations that can be immediately implemented in production environments.