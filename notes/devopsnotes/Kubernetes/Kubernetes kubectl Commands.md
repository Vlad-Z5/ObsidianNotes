### Cluster Management

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes
kubectl describe node node-name
kubectl get componentstatuses

# Cluster version
kubectl version
kubectl api-versions
kubectl api-resources
```

### Pod Management

```bash
# Create and manage pods
kubectl run nginx --image=nginx
kubectl apply -f pod.yaml
kubectl get pods
kubectl get pods -o wide
kubectl describe pod pod-name
kubectl logs pod-name
kubectl logs -f pod-name
kubectl logs pod-name -c container-name

# Execute commands in pod
kubectl exec -it pod-name -- bash
kubectl exec pod-name -- ls /app

kubectl port-forward pod-name 8080:80 # Port forwarding

# Delete pods
kubectl delete pod pod-name
kubectl delete -f pod.yaml
```

### Deployment Management

```bash
# Create deployment
kubectl create deployment nginx --image=nginx
kubectl apply -f deployment.yaml

# List deployments
kubectl get deployments
kubectl describe deployment deployment-name

# Scale deployment
kubectl scale deployment nginx --replicas=5
kubectl autoscale deployment nginx --min=2 --max=10 --cpu-percent=80

# Rolling updates
kubectl set image deployment/nginx nginx=nginx:1.21
kubectl rollout status deployment/nginx
kubectl rollout history deployment/nginx
kubectl rollout undo deployment/nginx
kubectl rollout undo deployment/nginx --to-revision=2

kubectl delete deployment deployment-name # Delete deployment
```

### Service Management

```bash
# Create service
kubectl expose deployment nginx --port=80 --type=ClusterIP
kubectl apply -f service.yaml

# List services
kubectl get services
kubectl get svc
kubectl describe service service-name

kubectl run test-pod --image=busybox -it --rm -- wget -qO- service-name # Test service connectivity
```

### Configuration Management

```bash
# ConfigMaps
kubectl create configmap app-config --from-literal=key1=value1
kubectl create configmap app-config --from-file=config.properties
kubectl get configmaps
kubectl describe configmap app-config

# Secrets
kubectl create secret generic app-secret --from-literal=username=admin
kubectl create secret generic app-secret --from-file=password.txt
kubectl get secrets
kubectl describe secret app-secret
```

### Debugging and Troubleshooting

```bash
# Resource inspection
kubectl get all
kubectl get events
kubectl describe pod pod-name
kubectl logs pod-name --previous

# Resource usage
kubectl top nodes
kubectl top pods

# Network debugging
kubectl exec -it pod-name -- nslookup service-name
kubectl exec -it pod-name -- curl service-name:port

# Resource cleanup
kubectl delete all --all
kubectl delete all -l app=nginx
```
