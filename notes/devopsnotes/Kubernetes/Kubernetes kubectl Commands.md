# Kubernetes kubectl Commands Reference

**kubectl** is the primary command-line interface for Kubernetes operations, providing comprehensive resource management, debugging capabilities, and production automation workflows for DevOps teams.

## Cluster Management

### Cluster Information & Status

```bash
# Cluster connectivity and basic info
kubectl cluster-info
kubectl cluster-info dump > cluster-info.txt
kubectl get nodes
kubectl get nodes -o wide
kubectl describe node <node-name>
kubectl get componentstatuses

# Cluster version and API information
kubectl version --short
kubectl version --client
kubectl api-versions
kubectl api-resources
kubectl api-resources --verbs=list --namespaced -o name

# Context and configuration
kubectl config view
kubectl config current-context
kubectl config get-contexts
kubectl config use-context <context-name>
```

### Cluster Health & Events

```bash
# Check cluster events
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl get events --all-namespaces --sort-by='.lastTimestamp'
kubectl get events --field-selector type=Warning

# Cluster resource usage
kubectl top nodes
kubectl top pods --all-namespaces
kubectl top pods --containers --all-namespaces
```

---

## Resource Operations

### Basic Resource Management

```bash
# Apply and create resources
kubectl apply -f <file.yaml>
kubectl apply -f <directory>/
kubectl apply -k <kustomization-directory>
kubectl create -f <file.yaml>

# Get resources
kubectl get all
kubectl get all --all-namespaces
kubectl get <resource-type>
kubectl get <resource-type> -o wide
kubectl get <resource-type> -o yaml
kubectl get <resource-type> -o json

# Describe resources
kubectl describe <resource-type> <resource-name>
kubectl describe <resource-type>/<resource-name>

# Delete resources
kubectl delete -f <file.yaml>
kubectl delete <resource-type> <resource-name>
kubectl delete <resource-type> --all
```

### Advanced Resource Queries

```bash
# Label and field selectors
kubectl get pods -l app=nginx
kubectl get pods --field-selector status.phase=Running
kubectl get nodes --selector='!node-role.kubernetes.io/master'

# Custom output formats
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'

# Watch resources
kubectl get pods --watch
kubectl get events --watch
```

---

## Pod Management

### Pod Creation & Lifecycle

```bash
# Create pods
kubectl run nginx --image=nginx --port=80
kubectl run busybox --image=busybox --rm -it --restart=Never -- sh
kubectl run test-pod --image=nginx --dry-run=client -o yaml > pod.yaml

# Apply pod manifests
kubectl apply -f pod.yaml
kubectl create -f pod.yaml

# Get pod information
kubectl get pods
kubectl get pods -o wide
kubectl get pods --show-labels
kubectl get pods --sort-by=.metadata.creationTimestamp
kubectl get pods --field-selector status.phase=Running

# Pod details and status
kubectl describe pod <pod-name>
kubectl describe pod <pod-name> -n <namespace>
kubectl get pod <pod-name> -o yaml
kubectl get pod <pod-name> -o json | jq '.status.containerStatuses[]'
```

### Pod Debugging & Interaction

```bash
# Container logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>
kubectl logs <pod-name> --previous
kubectl logs -f <pod-name>  # Follow logs
kubectl logs <pod-name> --since=1h
kubectl logs -l app=nginx --all-containers=true

# Execute commands in containers
kubectl exec -it <pod-name> -- bash
kubectl exec -it <pod-name> -c <container-name> -- sh
kubectl exec <pod-name> -- ls /app
kubectl exec <pod-name> -- env
kubectl exec <pod-name> -- cat /etc/resolv.conf

# Port forwarding
kubectl port-forward <pod-name> 8080:80
kubectl port-forward <pod-name> 8080:80 --address 0.0.0.0
kubectl port-forward pods/<pod-name> 8080:80

# Copy files
kubectl cp <pod-name>:/path/to/file ./local-file
kubectl cp ./local-file <pod-name>:/path/to/file
kubectl cp <pod-name>:/path/to/file ./local-file -c <container-name>
```

### Pod Troubleshooting

```bash
# Pod events and status
kubectl get events --field-selector involvedObject.name=<pod-name>
kubectl describe pod <pod-name> | grep -A 10 Events

# Resource usage
kubectl top pod <pod-name>
kubectl top pod <pod-name> --containers

# Restart and delete
kubectl delete pod <pod-name>
kubectl delete pod <pod-name> --grace-period=0 --force
kubectl delete pods --field-selector status.phase=Failed
```

---

## Deployment Management

### Deployment Creation & Configuration

```bash
# Create deployments
kubectl create deployment nginx --image=nginx --replicas=3
kubectl create deployment app --image=myapp:v1.0 --port=8080
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml

# Apply deployment manifests
kubectl apply -f deployment.yaml
kubectl apply -f deployments/ --recursive

# Get deployment information
kubectl get deployments
kubectl get deployments -o wide
kubectl get deployments --show-labels
kubectl describe deployment <deployment-name>
```

### Deployment Operations

```bash
# Scale deployments
kubectl scale deployment <deployment-name> --replicas=5
kubectl scale deployment <deployment-name> --replicas=0  # Scale down

# Rolling updates
kubectl set image deployment/<deployment-name> <container-name>=<new-image>
kubectl set image deployment/nginx nginx=nginx:1.21
kubectl set env deployment/<deployment-name> ENV_VAR=value

# Rollout management
kubectl rollout status deployment/<deployment-name>
kubectl rollout history deployment/<deployment-name>
kubectl rollout undo deployment/<deployment-name>
kubectl rollout undo deployment/<deployment-name> --to-revision=2
kubectl rollout restart deployment/<deployment-name>

# Pause and resume rollouts
kubectl rollout pause deployment/<deployment-name>
kubectl rollout resume deployment/<deployment-name>
```

### Advanced Deployment Operations

```bash
# Patch deployments
kubectl patch deployment <deployment-name> -p '{"spec":{"replicas":3}}'
kubectl patch deployment <deployment-name> --type='json' -p='[{"op": "replace", "path": "/spec/replicas", "value": 5}]'

# Edit deployments
kubectl edit deployment <deployment-name>

# Delete deployments
kubectl delete deployment <deployment-name>
kubectl delete deployment --all
```

---

## Service Management

### Service Creation & Types

```bash
# Create services
kubectl expose deployment <deployment-name> --port=80 --type=ClusterIP
kubectl expose deployment <deployment-name> --port=80 --type=NodePort
kubectl expose deployment <deployment-name> --port=80 --type=LoadBalancer
kubectl expose pod <pod-name> --port=80 --name=<service-name>

# Create service from YAML
kubectl apply -f service.yaml
kubectl create service clusterip <service-name> --tcp=80:8080

# Get service information
kubectl get services
kubectl get svc -o wide
kubectl describe service <service-name>
kubectl get endpoints
kubectl get endpoints <service-name>
```

### Service Testing & Debugging

```bash
# Test service connectivity
kubectl run test-pod --image=busybox --rm -it --restart=Never -- nslookup <service-name>
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -qO- <service-name>:80

# Port forwarding for services
kubectl port-forward service/<service-name> 8080:80
kubectl port-forward svc/<service-name> 8080:80

# Service endpoints
kubectl get endpoints <service-name> -o yaml
kubectl describe endpoints <service-name>
```

---

## Configuration Management

### ConfigMaps

```bash
# Create ConfigMaps
kubectl create configmap <config-name> --from-literal=key1=value1 --from-literal=key2=value2
kubectl create configmap <config-name> --from-file=<file-path>
kubectl create configmap <config-name> --from-file=<directory-path>
kubectl create configmap <config-name> --from-env-file=<env-file>

# Get ConfigMap information
kubectl get configmaps
kubectl describe configmap <config-name>
kubectl get configmap <config-name> -o yaml

# Edit and update ConfigMaps
kubectl edit configmap <config-name>
kubectl replace -f configmap.yaml
```

### Secrets

```bash
# Create secrets
kubectl create secret generic <secret-name> --from-literal=username=admin --from-literal=password=secret
kubectl create secret generic <secret-name> --from-file=<file-path>
kubectl create secret docker-registry <secret-name> --docker-server=<server> --docker-username=<username> --docker-password=<password>
kubectl create secret tls <secret-name> --cert=<cert-file> --key=<key-file>

# Get secret information
kubectl get secrets
kubectl describe secret <secret-name>
kubectl get secret <secret-name> -o yaml

# Decode secret values
kubectl get secret <secret-name> -o jsonpath='{.data.password}' | base64 --decode
```

### Namespace Management

```bash
# Create and manage namespaces
kubectl create namespace <namespace-name>
kubectl get namespaces
kubectl describe namespace <namespace-name>
kubectl delete namespace <namespace-name>

# Work with specific namespaces
kubectl get pods -n <namespace-name>
kubectl config set-context --current --namespace=<namespace-name>

# Resource quotas
kubectl create quota <quota-name> --hard=cpu=1,memory=1G,pods=2 -n <namespace-name>
kubectl get quota -n <namespace-name>
kubectl describe quota -n <namespace-name>
```

---

## Debugging & Troubleshooting

### Cluster Debugging

```bash
# Check cluster health
kubectl get componentstatuses
kubectl get nodes --show-labels
kubectl describe node <node-name>

# System pods and services
kubectl get pods -n kube-system
kubectl get pods -n kube-system -o wide
kubectl logs -n kube-system <pod-name>

# Events and issues
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl get events --field-selector type=Warning
kubectl get events --all-namespaces | grep -i error
```

### Resource Debugging

```bash
# Check resource status
kubectl get all --all-namespaces
kubectl get pods --all-namespaces --field-selector status.phase!=Running
kubectl get pods --all-namespaces --field-selector status.phase=Failed

# Describe resources for issues
kubectl describe pod <pod-name>
kubectl describe deployment <deployment-name>
kubectl describe service <service-name>

# Check resource usage
kubectl top nodes
kubectl top pods --all-namespaces --sort-by=cpu
kubectl top pods --all-namespaces --sort-by=memory
```

### Network Debugging

```bash
# DNS resolution testing
kubectl run dnsutils --image=tutum/dnsutils --rm -it --restart=Never -- nslookup kubernetes.default
kubectl run dnsutils --image=tutum/dnsutils --rm -it --restart=Never -- dig <service-name>.<namespace>.svc.cluster.local

# Network connectivity testing
kubectl run netshoot --image=nicolaka/netshoot --rm -it --restart=Never -- ping <service-ip>
kubectl run netshoot --image=nicolaka/netshoot --rm -it --restart=Never -- curl <service-name>:80

# Check network policies
kubectl get networkpolicies --all-namespaces
kubectl describe networkpolicy <policy-name>
```

---

## Monitoring & Logs

### Log Collection

```bash
# Pod logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>
kubectl logs <pod-name> --previous
kubectl logs -f <pod-name>
kubectl logs <pod-name> --since=1h
kubectl logs <pod-name> --tail=100

# Deployment/ReplicaSet logs
kubectl logs deployment/<deployment-name>
kubectl logs rs/<replicaset-name>

# Multiple pod logs
kubectl logs -l app=nginx --all-containers=true
kubectl logs -l app=nginx --all-containers=true --prefix=true
```

### Resource Monitoring

```bash
# Resource usage
kubectl top nodes
kubectl top pods
kubectl top pods --containers
kubectl top pods --all-namespaces
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory

# Watch resources
kubectl get pods --watch
kubectl get events --watch
kubectl get nodes --watch
```

---

## Production Operations

### Maintenance Operations

```bash
# Node maintenance
kubectl cordon <node-name>          # Mark node as unschedulable
kubectl uncordon <node-name>        # Mark node as schedulable
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Pod eviction
kubectl delete pod <pod-name> --grace-period=0 --force
kubectl delete pods --field-selector status.phase=Failed

# Resource cleanup
kubectl delete pods --all --grace-period=0 --force
kubectl delete all --all -n <namespace>
```

### Backup Operations

```bash
# Export resources
kubectl get all --export -o yaml > backup.yaml
kubectl get configmaps --all-namespaces -o yaml > configmaps-backup.yaml
kubectl get secrets --all-namespaces -o yaml > secrets-backup.yaml

# Cluster state dump
kubectl cluster-info dump --all-namespaces --output-directory=cluster-dump
```

### Security Operations

```bash
# RBAC debugging
kubectl auth can-i create pods
kubectl auth can-i create pods --as=system:serviceaccount:default:default
kubectl auth can-i '*' '*' --as=admin

# Check permissions
kubectl get rolebindings,clusterrolebindings --all-namespaces
kubectl describe rolebinding <binding-name>
kubectl describe clusterrolebinding <binding-name>
```

---

## Advanced Commands

### JSON/JSONPath Queries

```bash
# JSONPath examples
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
kubectl get pods -o jsonpath='{.items[*].status.podIP}'
kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# Custom columns
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,IP:.status.podIP
kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,AGE:.metadata.creationTimestamp
```

### Advanced Patching

```bash
# Strategic merge patch
kubectl patch deployment <deployment-name> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","image":"<new-image>"}]}}}}'

# JSON patch
kubectl patch pod <pod-name> --type='json' -p='[{"op": "replace", "path": "/spec/containers/0/image", "value": "nginx:1.21"}]'

# Merge patch
kubectl patch service <service-name> --type merge -p '{"spec":{"type":"NodePort"}}'
```

### Bulk Operations

```bash
# Apply multiple files
kubectl apply -f deployment.yaml,service.yaml,configmap.yaml
kubectl apply -f manifests/ --recursive

# Delete multiple resources
kubectl delete deployments,services -l app=myapp
kubectl delete pods --all --grace-period=0

# Bulk resource updates
kubectl get pods -o name | xargs -I {} kubectl delete {}
kubectl get deployments -o name | xargs -I {} kubectl scale {} --replicas=0
```

---

## Cross-References

**Related Documentation:**
- [Kubernetes Commands](Kubernetes%20Commands.md) - Comprehensive kubectl reference with DevOps automation
- [Kubernetes Troubleshooting](Kubernetes%20Troubleshooting.md) - Detailed debugging workflows and production scenarios
- [Kubernetes Monitoring and Troubleshooting](Kubernetes%20Monitoring%20and%20Troubleshooting.md) - Observability and monitoring strategies
- [Kubernetes Production Best Practices](Kubernetes%20Production%20Best%20Practices.md) - Production deployment and operational excellence

**Command Categories:**
- **Basic Operations**: Resource creation, deletion, and basic management
- **Debugging**: Troubleshooting, logs, events, and cluster health
- **Production**: Maintenance, scaling, updates, and security operations
- **Advanced**: JSONPath queries, bulk operations, and complex patching

**Best Practices:**
- Always use `--dry-run=client` before applying changes in production
- Use specific resource names and namespaces in production scripts
- Implement proper RBAC and limit access to sensitive operations
- Monitor resource usage and set appropriate limits
- Keep regular backups of critical configurations and secrets