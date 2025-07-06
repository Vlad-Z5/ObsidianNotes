### Health Checks

**Liveness Probe:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
```

**Readiness Probe:**

```yaml
spec:
  containers:
  - name: app
    image: myapp:latest
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      successThreshold: 1
      failureThreshold: 3
```

**Startup Probe:**

```yaml
spec:
  containers:
  - name: app
    image: myapp:latest
    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      failureThreshold: 30
      periodSeconds: 10
```

### Resource Monitoring

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml # Enable metrics server

# View resource usage
kubectl top nodes
kubectl top pods
kubectl top pods --containers
kubectl top pods --sort-by=cpu
```

### Common Troubleshooting Steps

1. **Check Pod Status**: `kubectl get pods -o wide`
2. **Describe Resources**: `kubectl describe pod/service/deployment`
3. **Check Logs**: `kubectl logs pod-name --previous`
4. **Check Events**: `kubectl get events --sort-by=.metadata.creationTimestamp`
5. **Resource Usage**: `kubectl top nodes/pods`
6. **Network Debug**: `kubectl exec -it pod -- nslookup service-name`

### Common Pod Failure Reasons

- Image pull errors (ImagePullBackOff)
- Resource constraints (CPU/Memory limits exceeded)
- Failed health checks (CrashLoopBackOff)
- Configuration issues (ConfigMap/Secret missing)
- Network connectivity problems
