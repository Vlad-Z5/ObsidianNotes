# Kubernetes Troubleshooting

**Kubernetes troubleshooting** involves systematic approaches to diagnose, debug, and resolve cluster, application, networking, and resource issues in production environments using kubectl, logs, metrics, and debugging tools.

## Cluster-Level Issues

### Cluster Connectivity Problems

```bash
# Check cluster access and connectivity
kubectl cluster-info
kubectl get nodes
kubectl get componentstatuses

# Validate kubeconfig
kubectl config view
kubectl config current-context
kubectl auth can-i get pods --as=system:serviceaccount:default:default

# Test API server connectivity
curl -k https://kubernetes.default.svc.cluster.local/api/v1/namespaces
kubectl get --raw /api/v1/namespaces

# Debug certificate issues
openssl x509 -in ~/.kube/config -text -noout
kubectl config view --raw -o jsonpath='{.users[0].user.client-certificate-data}' | base64 -d | openssl x509 -text -noout
```

### etcd and Control Plane Issues

```bash
# Check etcd health (if accessible)
kubectl get --raw=/healthz/etcd
kubectl get events --sort-by=.metadata.creationTimestamp | grep etcd

# Control plane component status
kubectl get pods -n kube-system
kubectl logs -n kube-system kube-apiserver-master-node
kubectl logs -n kube-system kube-controller-manager-master-node
kubectl logs -n kube-system kube-scheduler-master-node

# Check for control plane resource issues
kubectl top nodes
kubectl describe nodes | grep -A 10 "Allocated resources"

# API server debugging
kubectl get events --field-selector type=Warning
kubectl get events --field-selector reason=FailedScheduling
```

### Node Health Issues

```bash
# Comprehensive node check
kubectl get nodes -o wide
kubectl describe nodes

# Node conditions analysis
kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason

# Check node resource pressure
kubectl describe nodes | grep -E "(Pressure|OutOf)"

# Node logs (if accessible)
journalctl -u kubelet -f
journalctl -u docker -f
journalctl -u containerd -f

# Node capacity and allocation
kubectl describe nodes | grep -A 5 "Capacity\|Allocatable"
```

---

## Pod & Container Troubleshooting

### Pod Startup Failures

```bash
# Comprehensive pod status check
kubectl get pods -o wide
kubectl describe pod pod-name
kubectl get events --field-selector involvedObject.name=pod-name

# Image pull failures
kubectl describe pod pod-name | grep -A 10 "Failed to pull image"
kubectl get events --field-selector reason=Failed,involvedObject.kind=Pod

# Check image availability
docker pull image-name:tag
kubectl run test-pull --image=image-name:tag --rm -it --command -- echo "Image accessible"

# Registry authentication issues
kubectl get secrets -o yaml | grep dockerconfigjson
kubectl describe serviceaccount default
```

### Container Crashes and Restarts

```bash
# Container restart analysis
kubectl get pods -o custom-columns=NAME:.metadata.name,RESTARTS:.status.containerStatuses[*].restartCount,REASON:.status.containerStatuses[*].lastState.terminated.reason

# Previous container logs
kubectl logs pod-name --previous
kubectl logs pod-name -c container-name --previous

# Container exit codes
kubectl describe pod pod-name | grep -A 5 "Last State\|Exit Code"

# Resource limits causing OOMKilled
kubectl describe pod pod-name | grep -A 10 "Limits\|Requests"
kubectl top pods --containers

# Debug container startup
kubectl debug pod-name -it --image=busybox --target=container-name
```

### Init Container Issues

```bash
# Check init container status
kubectl describe pod pod-name | grep -A 20 "Init Containers"
kubectl logs pod-name -c init-container-name

# Init container dependencies
kubectl get events --field-selector involvedObject.name=pod-name,reason=FailedMount
kubectl describe pod pod-name | grep -A 10 "Volumes"

# Debug init container environment
kubectl describe pod pod-name | grep -A 10 "Environment"
```

---

## Network Debugging

### Service Discovery Issues

```bash
# Service and endpoint debugging
kubectl get services
kubectl get endpoints service-name
kubectl describe service service-name

# DNS resolution testing
kubectl run dns-debug --image=busybox --rm -it -- nslookup service-name
kubectl run dns-debug --image=busybox --rm -it -- nslookup service-name.namespace.svc.cluster.local

# CoreDNS debugging
kubectl logs -n kube-system deployment/coredns
kubectl get configmap -n kube-system coredns -o yaml
kubectl describe pod -n kube-system -l k8s-app=kube-dns

# Service connectivity testing
kubectl run test-pod --image=curlimages/curl --rm -it -- curl -v http://service-name:port
kubectl exec source-pod -- curl -v http://target-service:port/health
```

### Network Policy Issues

```bash
# Network policy debugging
kubectl get networkpolicy -A
kubectl describe networkpolicy policy-name

# Test network connectivity with policies
kubectl run test-allowed --image=busybox --rm -it -- wget --timeout=5 -qO- allowed-service
kubectl run test-denied --image=busybox --rm -it -- wget --timeout=5 -qO- denied-service

# Check pod labels for policy matching
kubectl get pods --show-labels
kubectl describe networkpolicy policy-name | grep -A 10 "podSelector"

# Network policy troubleshooting with netshoot
kubectl run netshoot --image=nicolaka/netshoot --rm -it -- bash
# Inside netshoot:
# ss -tuln
# iptables -L
# tcpdump -i any port 80
```

### Ingress and Load Balancer Issues

```bash
# Ingress controller debugging
kubectl get ingress -A
kubectl describe ingress ingress-name
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Check ingress annotations
kubectl get ingress ingress-name -o yaml

# Test ingress connectivity
curl -H "Host: app.example.com" http://ingress-ip/
kubectl run curl-test --image=curlimages/curl --rm -it -- curl -H "Host: app.example.com" http://ingress-service/

# Load balancer service debugging
kubectl get services --field-selector spec.type=LoadBalancer
kubectl describe service loadbalancer-service

# Check cloud provider integration
kubectl logs -n kube-system deployment/cloud-controller-manager
```

---

## Storage & Volume Issues

### Persistent Volume Problems

```bash
# PV and PVC status
kubectl get pv,pvc -A
kubectl describe pv pv-name
kubectl describe pvc pvc-name

# Volume binding issues
kubectl get events --field-selector reason=FailedBinding
kubectl describe storageclass storage-class-name

# CSI driver debugging
kubectl get csidriver
kubectl get csistoragecapacity
kubectl logs -n kube-system daemonset/csi-driver-name

# Volume attachment issues
kubectl get volumeattachment
kubectl describe volumeattachment va-name
```

### Volume Mount Failures

```bash
# Check volume mounts in pods
kubectl describe pod pod-name | grep -A 10 "Volumes\|Mounts"

# Permission issues
kubectl exec pod-name -- ls -la /mounted/path
kubectl exec pod-name -- id
kubectl describe pod pod-name | grep -A 5 "securityContext"

# Volume availability
kubectl exec pod-name -- df -h
kubectl exec pod-name -- mount | grep /mounted/path

# Storage class provisioning
kubectl describe storageclass default
kubectl get events --field-selector reason=ProvisioningFailed
```

---

## Resource & Performance Problems

### Resource Exhaustion

```bash
# Cluster resource usage
kubectl top nodes
kubectl top pods --all-namespaces --sort-by=cpu
kubectl top pods --all-namespaces --sort-by=memory

# Resource quotas and limits
kubectl describe quota -A
kubectl describe limitrange -A
kubectl get events --field-selector reason=Exceeded

# Node resource pressure
kubectl describe nodes | grep -E "MemoryPressure|DiskPressure|PIDPressure"
kubectl get events --field-selector reason=NodeHasDiskPressure

# OOMKilled containers
kubectl get events --field-selector reason=OOMKilling
kubectl describe pod pod-name | grep -A 5 "Last State"
```

### Performance Issues

```bash
# Application performance analysis
kubectl exec pod-name -- top
kubectl exec pod-name -- ps aux --sort=-%cpu
kubectl exec pod-name -- free -h

# I/O performance
kubectl exec pod-name -- iostat 1 5
kubectl exec pod-name -- df -h
kubectl exec pod-name -- lsof | wc -l

# Network performance
kubectl exec pod-name -- ss -tuln
kubectl exec pod-name -- netstat -i

# JVM debugging (for Java apps)
kubectl exec java-pod -- jstat -gc 1
kubectl exec java-pod -- jstack 1
kubectl exec java-pod -- jmap -histo 1
```

### Autoscaling Issues

```bash
# HPA debugging
kubectl get hpa -A
kubectl describe hpa hpa-name
kubectl get events --field-selector involvedObject.kind=HorizontalPodAutoscaler

# Metrics server issues
kubectl top nodes
kubectl logs -n kube-system deployment/metrics-server

# VPA debugging (if installed)
kubectl get vpa -A
kubectl describe vpa vpa-name

# Cluster autoscaler debugging
kubectl logs -n kube-system deployment/cluster-autoscaler
kubectl get events --field-selector reason=TriggeredScaleUp
```

---

## Application Debugging

### Application Logs Analysis

```bash
# Comprehensive log collection
kubectl logs pod-name --all-containers=true --prefix=true
kubectl logs deployment/app-name --max-log-requests=10
kubectl logs -f pod-name --since=1h | grep ERROR

# Log aggregation
kubectl logs -l app=myapp --tail=100
kubectl logs --selector=tier=backend --since=10m

# Previous container logs
kubectl logs pod-name --previous --all-containers=true
kubectl logs pod-name -c container-name --previous

# Log streaming and filtering
kubectl logs -f pod-name | grep -E "(ERROR|WARN|FATAL)"
kubectl logs pod-name --since=30m | awk '/ERROR/ {print $0}'
```

### Health Check Failures

```bash
# Probe configuration analysis
kubectl describe pod pod-name | grep -A 10 "Liveness\|Readiness\|Startup"

# Manual health check testing
kubectl exec pod-name -- curl -f http://localhost:8080/health
kubectl exec pod-name -- wget --spider http://localhost:8080/ready

# Probe failure events
kubectl get events --field-selector reason=Unhealthy
kubectl get events --field-selector reason=ProbeWarning

# Debug probe scripts
kubectl exec pod-name -- /path/to/health/script
kubectl describe pod pod-name | grep -A 5 "Command\|Args"
```

### Configuration Issues

```bash
# ConfigMap and Secret debugging
kubectl describe configmap config-name
kubectl get configmap config-name -o yaml
kubectl describe secret secret-name

# Environment variables
kubectl exec pod-name -- env | sort
kubectl describe pod pod-name | grep -A 20 "Environment"

# Volume-mounted configurations
kubectl exec pod-name -- ls -la /etc/config/
kubectl exec pod-name -- cat /etc/config/app.properties

# Configuration validation
kubectl exec pod-name -- /app/validate-config
```

---

## Security & RBAC Issues

### Authentication Problems

```bash
# Service account debugging
kubectl get serviceaccounts
kubectl describe serviceaccount sa-name
kubectl get secrets -o name | xargs -I {} kubectl describe secret {}

# Token validation
kubectl auth can-i get pods --as=system:serviceaccount:namespace:sa-name
kubectl auth can-i create deployments --as=user-name

# Certificate debugging
kubectl get csr
kubectl describe csr csr-name
```

### Authorization (RBAC) Issues

```bash
# RBAC debugging
kubectl get roles,rolebindings,clusterroles,clusterrolebindings -A
kubectl describe rolebinding binding-name
kubectl describe clusterrolebinding binding-name

# Permission testing
kubectl auth can-i get pods --namespace=production
kubectl auth can-i delete deployments --as=system:serviceaccount:default:default

# RBAC analysis
kubectl get rolebindings -o wide
kubectl get clusterrolebindings -o wide | grep user-name

# Security context issues
kubectl describe pod pod-name | grep -A 10 "Security Context"
kubectl exec pod-name -- id
kubectl exec pod-name -- whoami
```

### Pod Security Issues

```bash
# Pod security standards
kubectl get pods -o custom-columns=NAME:.metadata.name,SECURITY:.spec.securityContext
kubectl describe pod pod-name | grep -A 15 "Security Context"

# Privileged containers
kubectl get pods -o jsonpath='{.items[?(@.spec.containers[*].securityContext.privileged==true)].metadata.name}'

# Network policies
kubectl get networkpolicy -A
kubectl describe networkpolicy policy-name

# Image scanning (if available)
kubectl get vulnerabilityreports -A
kubectl describe vulnerabilityreport report-name
```

---

## Scheduling & Node Problems

### Pod Scheduling Failures

```bash
# Scheduling events
kubectl get events --field-selector reason=FailedScheduling
kubectl describe pod pod-name | grep -A 10 "Events"

# Node affinity issues
kubectl describe pod pod-name | grep -A 10 "Node-Selectors\|Affinity"
kubectl get nodes --show-labels

# Taints and tolerations
kubectl describe nodes | grep -A 5 "Taints"
kubectl describe pod pod-name | grep -A 5 "Tolerations"

# Resource constraints
kubectl describe nodes | grep -A 10 "Allocated resources"
kubectl get events --field-selector reason=InsufficientMemory
kubectl get events --field-selector reason=InsufficientCPU
```

### Node Maintenance Issues

```bash
# Node draining problems
kubectl get pods -o wide --field-selector spec.nodeName=node-name
kubectl describe node node-name | grep -A 5 "Conditions"

# Cordoned nodes
kubectl get nodes --field-selector spec.unschedulable=true

# DaemonSet issues
kubectl get daemonsets -A
kubectl describe daemonset ds-name

# Node pressure and eviction
kubectl get events --field-selector reason=Evicted
kubectl describe pod evicted-pod-name
```

---

## Control Plane Debugging

### API Server Issues

```bash
# API server accessibility
kubectl get --raw /healthz
kubectl get --raw /version
curl -k https://kubernetes-api:6443/healthz

# API server logs
kubectl logs -n kube-system kube-apiserver-master-name
journalctl -u kube-apiserver

# API server performance
kubectl get --raw /metrics | grep apiserver
time kubectl get pods --all-namespaces

# Rate limiting
kubectl get events --field-selector reason=TooManyRequests
```

### Controller Manager Issues

```bash
# Controller manager debugging
kubectl logs -n kube-system kube-controller-manager-master-name
kubectl get --raw /metrics | grep controller_manager

# Controller loops
kubectl get events --field-selector reason=FailedCreate
kubectl get replicasets -A | grep -v READY

# Garbage collection issues
kubectl get events --field-selector reason=FailedToDeletePod
```

### Scheduler Issues

```bash
# Scheduler debugging
kubectl logs -n kube-system kube-scheduler-master-name
kubectl get events --field-selector reason=FailedScheduling

# Scheduler metrics
kubectl get --raw /metrics | grep scheduler

# Custom schedulers
kubectl get pods -o custom-columns=NAME:.metadata.name,SCHEDULER:.spec.schedulerName
```

---

## CI/CD & Deployment Issues

### Deployment Failures

```bash
# Deployment status
kubectl get deployments -A
kubectl describe deployment deployment-name
kubectl rollout status deployment/deployment-name

# Rollout history
kubectl rollout history deployment/deployment-name
kubectl rollout history deployment/deployment-name --revision=2

# ReplicaSet issues
kubectl get replicasets -A
kubectl describe replicaset rs-name

# Rolling update problems
kubectl get events --field-selector reason=ReplicaSetUpdateError
kubectl describe deployment deployment-name | grep -A 10 "Conditions"
```

### GitOps and ArgoCD Issues

```bash
# ArgoCD application debugging
kubectl get applications -n argocd
kubectl describe application app-name -n argocd
kubectl logs -n argocd deployment/argocd-application-controller

# Sync status
kubectl get application app-name -n argocd -o jsonpath='{.status.sync.status}'
kubectl get application app-name -n argocd -o jsonpath='{.status.health.status}'

# Repository connectivity
kubectl logs -n argocd deployment/argocd-repo-server
kubectl get secrets -n argocd | grep repo
```

### Helm Deployment Issues

```bash
# Helm release debugging
helm list -A
helm status release-name
helm history release-name

# Helm template validation
helm template release-name chart-name --debug
helm install release-name chart-name --dry-run --debug

# Chart issues
helm get values release-name
helm get manifest release-name
```

---

## Emergency Procedures

### Cluster Recovery

```bash
# Emergency cluster assessment
kubectl get nodes
kubectl get pods -A | grep -v Running
kubectl get events --sort-by=.metadata.creationTimestamp | tail -50

# Critical service restoration
kubectl get pods -n kube-system
kubectl delete pod -n kube-system dns-pod-name
kubectl rollout restart deployment/coredns -n kube-system

# Node recovery
kubectl drain node-name --ignore-daemonsets --force
kubectl uncordon node-name
kubectl delete node node-name  # If node is permanently lost
```

### Data Recovery

```bash
# PV recovery
kubectl get pv | grep Released
kubectl patch pv pv-name -p '{"spec":{"claimRef": null}}'

# etcd backup (if accessible)
kubectl get all --all-namespaces -o yaml > cluster-backup.yaml

# Secret recovery
kubectl get secrets -A -o yaml > secrets-backup.yaml
```

### Emergency Scaling

```bash
# Critical application scaling
kubectl scale deployment critical-app --replicas=10
kubectl patch hpa hpa-name -p '{"spec":{"maxReplicas":20}}'

# Resource cleanup
kubectl delete pods --field-selector=status.phase=Failed -A
kubectl delete pods --field-selector=status.phase=Succeeded -A
```

---

## Production Scenarios

### High Traffic Issues

```bash
#!/bin/bash
# High traffic troubleshooting script

echo "=== High Traffic Analysis ==="

# Check current load
kubectl top nodes
kubectl top pods --all-namespaces --sort-by=cpu | head -20

# Check autoscaling
kubectl get hpa -A
kubectl describe hpa critical-app-hpa

# Check resource limits
kubectl get pods -o custom-columns=NAME:.metadata.name,CPU-REQ:.spec.containers[*].resources.requests.cpu,MEM-REQ:.spec.containers[*].resources.requests.memory | grep critical-app

# Check for throttling
kubectl get events --field-selector reason=FailedScheduling | tail -10

# Application health
kubectl get pods -l app=critical-app -o custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[*].ready,RESTARTS:.status.containerStatuses[*].restartCount

echo "=== Analysis Complete ==="
```

### Database Connection Issues

```bash
# Database connectivity debugging
kubectl exec app-pod -- nc -zv database-service 5432
kubectl exec app-pod -- telnet database-service 5432

# Connection pool analysis
kubectl logs app-pod | grep -i "connection"
kubectl exec app-pod -- ps aux | grep java

# Database pod debugging
kubectl describe pod database-pod
kubectl logs database-pod | tail -100

# Service discovery
kubectl get endpoints database-service
kubectl describe service database-service
```

### Certificate Expiry Issues

```bash
# Certificate status check
kubectl get secrets -A --field-selector type=kubernetes.io/tls
kubectl describe secret tls-secret

# Certificate expiry check
kubectl get secret tls-secret -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -enddate

# Ingress TLS issues
kubectl describe ingress ingress-name
kubectl get events --field-selector reason=InvalidCertificate

# Service account token issues
kubectl describe secret $(kubectl get serviceaccount default -o jsonpath='{.secrets[0].name}')
```

### Multi-Cluster Issues

```bash
# Cluster connectivity
kubectl config get-contexts
kubectl cluster-info --context=cluster-name

# Cross-cluster service discovery
kubectl get services --context=cluster1
kubectl get services --context=cluster2

# Network connectivity between clusters
kubectl run test-pod --image=busybox --rm -it --context=cluster1 -- ping cluster2-service
```

---

## Cross-References

**Related Documentation:**
- [Kubernetes Commands](Kubernetes%20Commands.md) - kubectl commands and debugging workflows
- [Kubernetes Monitoring and Troubleshooting](Kubernetes%20Monitoring%20and%20Troubleshooting.md) - Observability and monitoring setup
- [Kubernetes Networking](Kubernetes%20Networking.md) - Service discovery and network debugging
- [Kubernetes Security](Kubernetes%20Security.md) - RBAC, security contexts, and hardening
- [Kubernetes Storage](Kubernetes%20Storage.md) - Persistent volumes and storage debugging

**Integration Points:**
- **Docker Troubleshooting**: Container runtime issues and image problems
- **Linux Commands**: System-level debugging and performance analysis
- **Monitoring Tools**: Prometheus, Grafana, and observability platforms
- **Cloud Providers**: EKS, GKE, AKS-specific troubleshooting procedures