# Kubernetes Commands

**kubectl** is the command-line interface for Kubernetes clusters, providing comprehensive resource management, debugging capabilities, and DevOps automation workflows for production environments.


## Cluster Management

### Cluster Information & Status

```bash
# Cluster connectivity and info
kubectl cluster-info
kubectl cluster-info dump > cluster-info.txt

# API server and component status
kubectl get componentstatuses
kubectl get cs

# Cluster version information
kubectl version --short
kubectl version --client
kubectl api-versions
kubectl api-resources

# Cluster configuration
kubectl config view
kubectl config current-context
kubectl config get-contexts
kubectl config use-context context-name

# Cluster events
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl get events --field-selector type=Warning
kubectl get events --watch
```

### Context & Configuration Management

```bash
# Context operations
kubectl config set-context --current --namespace=production
kubectl config set-context dev --cluster=dev-cluster --user=dev-user
kubectl config delete-context old-context

# Cluster access setup
kubectl config set-cluster production --server=https://k8s-api.example.com
kubectl config set-credentials admin --token=your-token
kubectl config set-credentials admin --client-certificate=admin.crt --client-key=admin.key

# Kubeconfig management
export KUBECONFIG=~/.kube/config:~/.kube/dev-config
kubectl config view --flatten > ~/.kube/merged-config
```

---

## Resource Creation & Management

### Resource Creation Patterns

```bash
# Imperative creation
kubectl create deployment nginx --image=nginx:1.21
kubectl create service clusterip nginx --tcp=80:80
kubectl create configmap app-config --from-literal=env=production
kubectl create secret generic app-secret --from-literal=password=secret123

# Declarative creation
kubectl apply -f deployment.yaml
kubectl apply -f .
kubectl apply -k overlays/production
kubectl apply -f https://raw.githubusercontent.com/example/k8s-manifests/main/app.yaml

# Resource creation with output
kubectl create deployment nginx --image=nginx --output=yaml > deployment.yaml
kubectl create service clusterip nginx --tcp=80:80 --output=json > service.json
```

### Resource Listing & Inspection

```bash
# Basic resource listing
kubectl get all
kubectl get all --all-namespaces
kubectl get all -A

# Specific resource types
kubectl get pods,services,deployments
kubectl get pods --selector=app=nginx
kubectl get pods --field-selector=status.phase=Running

# Wide output and custom columns
kubectl get pods -o wide
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName
kubectl get pods --sort-by=.metadata.creationTimestamp

# Watch resources in real-time
kubectl get pods --watch
kubectl get events --watch
kubectl get pods --watch-only
```

### Resource Details & Description

```bash
# Detailed resource information
kubectl describe pod pod-name
kubectl describe deployment deployment-name
kubectl describe service service-name
kubectl describe node node-name

# Resource definitions and status
kubectl get pod pod-name -o yaml
kubectl get deployment deployment-name -o json
kubectl get pod pod-name -o jsonpath='{.status.phase}'
kubectl get pods -o jsonpath='{.items[*].metadata.name}'

# Resource history and annotations
kubectl annotate pod pod-name description="Web server pod"
kubectl label pod pod-name environment=production
kubectl get pod pod-name --show-labels
```

---

## Dry-Run & Validation

### Client-Side Dry Run (Local Validation)

```bash
# Validate manifests without sending to server
kubectl apply -f deployment.yaml --dry-run=client
kubectl create deployment nginx --image=nginx --dry-run=client
kubectl delete pod pod-name --dry-run=client

# Generate manifests with dry-run
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml
kubectl create service clusterip nginx --tcp=80:80 --dry-run=client -o yaml
kubectl create configmap app-config --from-literal=env=prod --dry-run=client -o yaml

# Validate and save manifests
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml
kubectl create service nodeport nginx --tcp=80:80 --dry-run=client -o yaml > service.yaml

# Complex manifest generation
kubectl create job backup --image=backup:latest --dry-run=client -o yaml > backup-job.yaml
kubectl create cronjob backup --image=backup:latest --schedule="0 2 * * *" --dry-run=client -o yaml > backup-cronjob.yaml
```

### Server-Side Dry Run (API Validation)

```bash
# Validate against API server without persisting
kubectl apply -f deployment.yaml --dry-run=server
kubectl create -f manifest.yaml --dry-run=server

# Validate resource updates
kubectl set image deployment/nginx nginx=nginx:1.22 --dry-run=server
kubectl scale deployment nginx --replicas=5 --dry-run=server

# Validate complex operations
kubectl patch deployment nginx -p '{"spec":{"replicas":3}}' --dry-run=server
kubectl replace -f updated-deployment.yaml --dry-run=server

# Validate with different output formats
kubectl apply -f deployment.yaml --dry-run=server -o yaml
kubectl apply -f deployment.yaml --dry-run=server -o json
```

### Manifest Validation & Linting

```bash
# Validate YAML syntax
kubectl apply -f manifest.yaml --validate=true --dry-run=client

# Server-side validation
kubectl apply -f manifest.yaml --server-dry-run --validate=true

# Validate against schema
kubectl apply -f manifest.yaml --validate=strict

# Combined validation workflow
validate_manifest() {
    local file="$1"
    echo "Validating $file..."

    # YAML syntax check
    yamllint "$file" || return 1

    # Client-side validation
    kubectl apply -f "$file" --dry-run=client --validate=true || return 1

    # Server-side validation
    kubectl apply -f "$file" --dry-run=server --validate=true || return 1

    echo "✓ $file is valid"
}

# Usage: validate_manifest deployment.yaml
```

---

## Edit Workflows & Patching

### Interactive Editing

```bash
# Edit resources directly
kubectl edit deployment deployment-name
kubectl edit service service-name
kubectl edit configmap config-name

# Edit with specific editor
EDITOR=vim kubectl edit deployment deployment-name
EDITOR=nano kubectl edit pod pod-name

# Edit multiple resources
kubectl edit deployment,service nginx
```

### Temporary File Workflows

```bash
# Extract, edit, and apply pattern
kubectl get deployment nginx -o yaml > /tmp/nginx-deployment.yaml
# Edit /tmp/nginx-deployment.yaml
kubectl apply -f /tmp/nginx-deployment.yaml

# Extract and create new resource
kubectl get deployment nginx -o yaml > /tmp/nginx-copy.yaml
# Modify name and other fields in /tmp/nginx-copy.yaml
kubectl apply -f /tmp/nginx-copy.yaml

# Backup before editing
backup_and_edit() {
    local resource="$1"
    local name="$2"
    local backup_file="/tmp/${name}-$(date +%Y%m%d-%H%M%S).yaml"

    # Create backup
    kubectl get "$resource" "$name" -o yaml > "$backup_file"
    echo "Backup created: $backup_file"

    # Edit in temporary file
    local temp_file="/tmp/${name}-edit.yaml"
    kubectl get "$resource" "$name" -o yaml > "$temp_file"
    ${EDITOR:-vi} "$temp_file"

    # Apply changes
    read -p "Apply changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl apply -f "$temp_file"
    else
        echo "Changes discarded"
    fi

    rm -f "$temp_file"
}

# Usage: backup_and_edit deployment nginx
```

### Strategic Merge Patching

```bash
# JSON merge patch
kubectl patch deployment nginx -p '{"spec":{"replicas":3}}'
kubectl patch service nginx -p '{"spec":{"type":"NodePort"}}'

# YAML merge patch
kubectl patch deployment nginx --patch '
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:1.22'

# JSON patch for arrays
kubectl patch deployment nginx --type='json' -p='[{"op": "replace", "path": "/spec/replicas", "value": 3}]'

# Strategic merge patch with file
echo 'spec:
  replicas: 4
  template:
    metadata:
      labels:
        version: v2' > /tmp/patch.yaml

kubectl patch deployment nginx --patch-file /tmp/patch.yaml
```

### Replace Operations

```bash
# Replace entire resource
kubectl replace -f updated-deployment.yaml

# Force replace (delete and recreate)
kubectl replace -f deployment.yaml --force

# Replace with validation
kubectl replace -f deployment.yaml --validate=true

# Replace from stdin
kubectl get deployment nginx -o yaml | \
sed 's/replicas: 1/replicas: 3/' | \
kubectl replace -f -

# Conditional replace
kubectl replace -f deployment.yaml --cascade=orphan
```

---

## Pod & Container Operations

### Pod Management

```bash
# Pod creation and deletion
kubectl run nginx --image=nginx --restart=Never
kubectl run debug --image=busybox --rm -it -- sh
kubectl delete pod pod-name
kubectl delete pod pod-name --force --grace-period=0

# Pod execution
kubectl exec -it pod-name -- bash
kubectl exec -it pod-name -c container-name -- bash
kubectl exec pod-name -- ls /app
kubectl exec pod-name -c container-name -- ps aux

# File operations
kubectl cp pod-name:/path/to/file ./local-file
kubectl cp ./local-file pod-name:/path/to/file
kubectl cp pod-name:/path/to/file ./local-file -c container-name
```

### Container Debugging

```bash
# Container logs
kubectl logs pod-name
kubectl logs pod-name -c container-name
kubectl logs pod-name --previous
kubectl logs pod-name --since=1h
kubectl logs pod-name --tail=50
kubectl logs -f pod-name

# Multi-container logs
kubectl logs pod-name --all-containers=true
kubectl logs pod-name --all-containers=true --prefix=true

# Debug containers (Kubernetes 1.23+)
kubectl debug pod-name -it --image=busybox
kubectl debug pod-name -it --image=busybox --target=container-name
kubectl debug node/node-name -it --image=busybox

# Ephemeral containers
kubectl debug pod-name -it --image=busybox --target=container-name
```

### Port Forwarding & Proxy

```bash
# Port forwarding
kubectl port-forward pod/pod-name 8080:80
kubectl port-forward service/service-name 8080:80
kubectl port-forward deployment/deployment-name 8080:80

# Background port forwarding
kubectl port-forward pod/pod-name 8080:80 &
PF_PID=$!
# Do work...
kill $PF_PID

# Proxy API server
kubectl proxy --port=8080
kubectl proxy --address='0.0.0.0' --port=8080 --accept-hosts='^.*'

# Access API through proxy
curl http://localhost:8080/api/v1/namespaces/default/pods
```

---

## Service & Network Management

### Service Operations

```bash
# Service creation
kubectl expose deployment nginx --port=80 --type=ClusterIP
kubectl expose deployment nginx --port=80 --type=NodePort
kubectl expose deployment nginx --port=80 --type=LoadBalancer
kubectl create service clusterip nginx --tcp=80:80

# Service inspection
kubectl get services
kubectl get svc -o wide
kubectl describe service service-name
kubectl get endpoints service-name

# Service testing
kubectl run test-pod --image=busybox --rm -it -- wget -qO- service-name
kubectl run test-pod --image=busybox --rm -it -- nslookup service-name
kubectl run test-pod --image=busybox --rm -it -- telnet service-name 80
```

### Network Debugging

```bash
# DNS resolution testing
kubectl run dns-test --image=busybox --rm -it -- nslookup kubernetes.default
kubectl run dns-test --image=busybox --rm -it -- nslookup service-name.namespace.svc.cluster.local

# Network connectivity testing
kubectl run net-test --image=nicolaka/netshoot --rm -it -- bash
kubectl run curl-test --image=curlimages/curl --rm -it -- curl -v service-name:port

# Pod-to-pod communication
kubectl exec source-pod -- ping target-pod-ip
kubectl exec source-pod -- curl target-service:port/health

# Network policy testing
kubectl run test-pod --image=busybox --rm -it -- wget --timeout=5 -qO- denied-service
```

### Ingress Management

```bash
# Ingress inspection
kubectl get ingress
kubectl describe ingress ingress-name
kubectl get ingress -o yaml

# Ingress testing
curl -H "Host: app.example.com" http://ingress-ip/
kubectl run curl-test --image=curlimages/curl --rm -it -- curl -H "Host: app.example.com" http://ingress-service/
```

---

## Storage & Volume Commands

### Persistent Volume Management

```bash
# PersistentVolume operations
kubectl get pv
kubectl describe pv pv-name
kubectl delete pv pv-name

# PersistentVolumeClaim operations
kubectl get pvc
kubectl describe pvc pvc-name
kubectl delete pvc pvc-name

# Storage class management
kubectl get storageclass
kubectl describe storageclass standard
kubectl get sc -o yaml
```

### Volume Debugging

```bash
# Check volume mounts
kubectl describe pod pod-name | grep -A 10 Volumes
kubectl describe pod pod-name | grep -A 10 Mounts

# Volume usage inspection
kubectl exec pod-name -- df -h
kubectl exec pod-name -- ls -la /mounted/path
kubectl exec pod-name -- cat /proc/mounts | grep /mounted/path

# CSI driver debugging
kubectl get csidriver
kubectl get csistoragecapacity
kubectl get volumeattachment
```

---

## Configuration & Secrets

### ConfigMap Management

```bash
# ConfigMap creation
kubectl create configmap app-config --from-literal=env=production
kubectl create configmap app-config --from-file=config.properties
kubectl create configmap app-config --from-file=config-dir/
kubectl create configmap app-config --from-env-file=.env

# ConfigMap inspection
kubectl get configmap
kubectl describe configmap app-config
kubectl get configmap app-config -o yaml

# ConfigMap data extraction
kubectl get configmap app-config -o jsonpath='{.data.env}'
kubectl get configmap app-config -o go-template='{{.data.config}}'
```

### Secret Management

```bash
# Secret creation
kubectl create secret generic app-secret --from-literal=password=secret123
kubectl create secret generic app-secret --from-file=ssh-key=~/.ssh/id_rsa
kubectl create secret docker-registry regcred --docker-server=registry.com --docker-username=user --docker-password=pass

# Secret inspection (careful with sensitive data)
kubectl get secrets
kubectl describe secret app-secret
kubectl get secret app-secret -o yaml

# Secret data extraction (base64 encoded)
kubectl get secret app-secret -o jsonpath='{.data.password}' | base64 -d
kubectl get secret app-secret -o go-template='{{.data.password | base64decode}}'

# TLS secret creation
kubectl create secret tls tls-secret --cert=tls.crt --key=tls.key
```

---

## Debugging & Troubleshooting

### Resource Status Investigation

```bash
# Comprehensive status check
kubectl get all -A
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl get events --field-selector type=Warning

# Resource conditions
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,CONDITIONS:.status.conditions[*].type
kubectl describe pod pod-name | grep -A 10 Conditions

# Resource finalizers and owners
kubectl get pod pod-name -o jsonpath='{.metadata.finalizers}'
kubectl get pod pod-name -o jsonpath='{.metadata.ownerReferences}'
```

### Performance Debugging

```bash
# Resource usage
kubectl top nodes
kubectl top pods
kubectl top pods --containers
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory

# Resource allocation
kubectl describe nodes | grep -A 5 "Allocated resources"
kubectl describe quota -A
kubectl describe limitrange -A

# Pod resource requests/limits
kubectl get pods -o custom-columns=NAME:.metadata.name,CPU-REQ:.spec.containers[*].resources.requests.cpu,MEM-REQ:.spec.containers[*].resources.requests.memory
```

### Application Debugging

```bash
# Application logs analysis
kubectl logs pod-name --previous > previous-logs.txt
kubectl logs pod-name --since=1h | grep ERROR
kubectl logs -f deployment/app-name --max-log-requests=10

# Health check debugging
kubectl get pods -o custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[*].ready,RESTARTS:.status.containerStatuses[*].restartCount

# Probe failure investigation
kubectl describe pod pod-name | grep -A 10 "Liveness\|Readiness\|Startup"
kubectl get events --field-selector involvedObject.name=pod-name
```

### Network Troubleshooting

```bash
# Service endpoint debugging
kubectl get endpoints service-name
kubectl describe endpoints service-name

# DNS debugging
kubectl run dns-debug --image=busybox --rm -it -- nslookup service-name
kubectl run dns-debug --image=busybox --rm -it -- cat /etc/resolv.conf

# Network policy debugging
kubectl describe networkpolicy policy-name
kubectl get networkpolicy -A

# CoreDNS debugging
kubectl logs -n kube-system deployment/coredns
kubectl get configmap -n kube-system coredns -o yaml
```

---

## Node Management

### Node Operations

```bash
# Node information
kubectl get nodes
kubectl get nodes -o wide
kubectl describe node node-name

# Node labeling and annotation
kubectl label nodes node-name environment=production
kubectl annotate nodes node-name description="High memory node"
kubectl get nodes --show-labels

# Node selection
kubectl get nodes --selector=environment=production
kubectl get nodes --field-selector=spec.unschedulable=false
```

### Node Maintenance

```bash
# Drain node (evict pods)
kubectl drain node-name --ignore-daemonsets
kubectl drain node-name --ignore-daemonsets --delete-emptydir-data
kubectl drain node-name --ignore-daemonsets --force

# Cordon node (mark unschedulable)
kubectl cordon node-name
kubectl uncordon node-name

# Taint management
kubectl taint nodes node-name key=value:NoSchedule
kubectl taint nodes node-name key=value:NoExecute
kubectl taint nodes node-name key:NoSchedule-  # Remove taint

# Node condition monitoring
kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason
```

---

## Resource Monitoring

### Real-time Monitoring

```bash
# Watch resource changes
kubectl get pods --watch
kubectl get events --watch
kubectl get pods --watch-only

# Resource utilization monitoring
watch kubectl top nodes
watch kubectl top pods
watch "kubectl get pods -o wide"

# Custom monitoring scripts
monitor_pods() {
    while true; do
        clear
        echo "=== Pod Status at $(date) ==="
        kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[*].restartCount,AGE:.metadata.creationTimestamp
        sleep 5
    done
}
```

### Resource Usage Analysis

```bash
# CPU and memory usage
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory
kubectl top nodes --sort-by=cpu

# Resource requests vs usage
kubectl describe nodes | grep -A 10 "Allocated resources"
kubectl get pods -o custom-columns=NAME:.metadata.name,CPU-REQ:.spec.containers[*].resources.requests.cpu,MEM-REQ:.spec.containers[*].resources.requests.memory

# Historical resource usage (requires metrics-server)
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods
```

---

## Advanced Operations

### Resource Management

```bash
# Resource quotas
kubectl create quota compute-quota --hard=cpu=2,memory=4Gi,pods=10
kubectl describe quota compute-quota
kubectl get quota -A

# Limit ranges
kubectl create -f - <<EOF
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-memory-limit-range
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
EOF

# Priority classes
kubectl get priorityclass
kubectl describe priorityclass system-cluster-critical
```

### Scaling Operations

```bash
# Manual scaling
kubectl scale deployment nginx --replicas=5
kubectl scale statefulset database --replicas=3
kubectl scale replicaset rs-name --replicas=2

# Autoscaling
kubectl autoscale deployment nginx --min=2 --max=10 --cpu-percent=80
kubectl get hpa
kubectl describe hpa nginx

# Vertical scaling (VPA)
kubectl get vpa
kubectl describe vpa app-vpa
```

### Rollout Management

```bash
# Deployment rollouts
kubectl rollout status deployment/nginx
kubectl rollout history deployment/nginx
kubectl rollout undo deployment/nginx
kubectl rollout undo deployment/nginx --to-revision=2

# Rolling restart
kubectl rollout restart deployment/nginx
kubectl rollout restart daemonset/log-agent

# Rollout control
kubectl rollout pause deployment/nginx
kubectl rollout resume deployment/nginx
```

---

## DevOps Automation

### Batch Operations

```bash
# Apply multiple manifests
kubectl apply -f namespace.yaml,deployment.yaml,service.yaml
kubectl apply -f manifests/
kubectl apply -k overlays/production

# Delete multiple resources
kubectl delete pods --selector=app=nginx
kubectl delete all --selector=app=nginx
kubectl delete namespace test-namespace

# Bulk resource operations
kubectl get pods --no-headers -o custom-columns=":metadata.name" | xargs kubectl delete pod
kubectl get deployments --no-headers -o custom-columns=":metadata.name" | grep -E "^test-" | xargs kubectl delete deployment
```

### Automation Scripts

```bash
#!/bin/bash
# deployment-health-check.sh
check_deployment_health() {
    local deployment="$1"
    local namespace="${2:-default}"

    echo "Checking deployment: $deployment in namespace: $namespace"

    # Check deployment status
    local ready_replicas=$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath='{.status.readyReplicas}')
    local desired_replicas=$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath='{.spec.replicas}')

    if [[ "$ready_replicas" == "$desired_replicas" ]]; then
        echo "✓ Deployment $deployment is healthy ($ready_replicas/$desired_replicas)"
        return 0
    else
        echo "✗ Deployment $deployment is unhealthy ($ready_replicas/$desired_replicas)"
        return 1
    fi
}

# Wait for deployment to be ready
wait_for_deployment() {
    local deployment="$1"
    local namespace="${2:-default}"
    local timeout="${3:-300}"

    echo "Waiting for deployment $deployment to be ready..."
    kubectl wait --for=condition=available --timeout="${timeout}s" deployment/"$deployment" -n "$namespace"
}

# Usage examples:
# check_deployment_health nginx default
# wait_for_deployment nginx default 600
```

### CI/CD Integration

```bash
# GitOps deployment validation
validate_and_deploy() {
    local manifest_file="$1"

    # Validate syntax
    kubectl apply -f "$manifest_file" --dry-run=client --validate=true || {
        echo "Validation failed"
        return 1
    }

    # Server-side validation
    kubectl apply -f "$manifest_file" --dry-run=server --validate=true || {
        echo "Server validation failed"
        return 1
    }

    # Apply with recording
    kubectl apply -f "$manifest_file" --record=true

    # Wait for rollout
    kubectl rollout status -f "$manifest_file" --timeout=600s
}

# Blue-green deployment helper
blue_green_deploy() {
    local service="$1"
    local new_deployment="$2"
    local old_deployment="$3"

    # Deploy new version
    kubectl apply -f "$new_deployment"
    kubectl rollout status deployment/$(basename "$new_deployment" .yaml)

    # Switch traffic
    kubectl patch service "$service" -p '{"spec":{"selector":{"version":"green"}}}'

    # Cleanup old deployment after verification
    read -p "Delete old deployment? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete -f "$old_deployment"
    fi
}
```

---

## Production Workflows

### Emergency Procedures

```bash
# Emergency pod restart
kubectl delete pod pod-name --force --grace-period=0

# Quick deployment rollback
kubectl rollout undo deployment/app --to-revision=$(kubectl rollout history deployment/app | tail -2 | head -1 | awk '{print $1}')

# Emergency scaling
kubectl scale deployment critical-app --replicas=10

# Emergency node evacuation
kubectl drain node-name --ignore-daemonsets --force --delete-emptydir-data --grace-period=30
```

### Health Check Automation

```bash
#!/bin/bash
# cluster-health-check.sh

echo "=== Kubernetes Cluster Health Check ==="

# Check node status
echo "1. Node Status:"
kubectl get nodes --no-headers | while read node status roles age version; do
    if [[ "$status" != "Ready" ]]; then
        echo "  ✗ Node $node is $status"
    else
        echo "  ✓ Node $node is Ready"
    fi
done

# Check system pods
echo "2. System Pods:"
kubectl get pods -n kube-system --no-headers | while read name ready status restarts age; do
    if [[ "$status" != "Running" ]]; then
        echo "  ✗ Pod $name is $status"
    fi
done

# Check resource usage
echo "3. Resource Usage:"
kubectl top nodes --no-headers | while read node cpu_usage cpu_percent memory_usage memory_percent; do
    cpu_num=${cpu_percent%\%}
    memory_num=${memory_percent%\%}

    if (( cpu_num > 80 )); then
        echo "  ⚠ Node $node CPU usage high: $cpu_percent"
    fi

    if (( memory_num > 80 )); then
        echo "  ⚠ Node $node Memory usage high: $memory_percent"
    fi
done

# Check persistent volumes
echo "4. Storage:"
kubectl get pv --no-headers | while read name capacity access_modes reclaim_policy status claim age; do
    if [[ "$status" != "Bound" && "$status" != "Available" ]]; then
        echo "  ✗ PV $name is $status"
    fi
done

echo "=== Health Check Complete ==="
```

### Backup Operations

```bash
# etcd backup (if direct access)
kubectl get all --all-namespaces -o yaml > cluster-backup-$(date +%Y%m%d).yaml

# Resource backup by type
backup_cluster_resources() {
    local backup_dir="cluster-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup core resources
    kubectl get configmaps --all-namespaces -o yaml > "$backup_dir/configmaps.yaml"
    kubectl get secrets --all-namespaces -o yaml > "$backup_dir/secrets.yaml"
    kubectl get services --all-namespaces -o yaml > "$backup_dir/services.yaml"
    kubectl get deployments --all-namespaces -o yaml > "$backup_dir/deployments.yaml"
    kubectl get statefulsets --all-namespaces -o yaml > "$backup_dir/statefulsets.yaml"
    kubectl get persistentvolumes -o yaml > "$backup_dir/persistentvolumes.yaml"
    kubectl get persistentvolumeclaims --all-namespaces -o yaml > "$backup_dir/persistentvolumeclaims.yaml"

    echo "Backup completed in $backup_dir"
}

# Disaster recovery validation
validate_cluster_state() {
    echo "Validating cluster state..."

    # Check critical deployments
    kubectl get deployments --all-namespaces --no-headers | while read namespace name ready_up_to_date available age; do
        if [[ "$available" == "0" ]]; then
            echo "WARNING: Deployment $namespace/$name has no available replicas"
        fi
    done

    # Check persistent volumes
    kubectl get pv --no-headers | grep -v "Bound\|Available" && echo "WARNING: Some PVs are in unexpected state"

    # Check node readiness
    kubectl get nodes --no-headers | grep -v "Ready" && echo "WARNING: Some nodes are not ready"

    echo "Cluster state validation complete"
}
```

---

## Cross-References

**Related Documentation:**
- [Kubernetes fundamental](Kubernetes%20fundamental.md) - Core concepts and architecture
- [Kubernetes Security](Kubernetes%20Security.md) - RBAC, security contexts, and hardening
- [Kubernetes Networking](Kubernetes%20Networking.md) - Service discovery, ingress, and network policies
- [Kubernetes Storage](Kubernetes%20Storage.md) - Persistent volumes, storage classes, and CSI
- [Kubernetes Monitoring and Troubleshooting](Kubernetes%20Monitoring%20and%20Troubleshooting.md) - Observability and debugging

**Integration Points:**
- **Docker Commands**: Container management and image operations
- **Linux Commands**: System administration and troubleshooting
- **DevOps Automation**: CI/CD pipelines, GitOps workflows, and infrastructure as code
- **Production Operations**: Monitoring, alerting, backup, and disaster recovery