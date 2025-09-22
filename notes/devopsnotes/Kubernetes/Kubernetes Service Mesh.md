# Kubernetes Service Mesh

Comprehensive guide to service mesh technologies including Istio, Linkerd, Consul Connect, and practical implementations for microservices communication, security, and observability.

## Service Mesh Overview

### What is a Service Mesh?

A service mesh is a dedicated infrastructure layer for handling service-to-service communication in microservices architectures. It provides:

- **Traffic Management**: Load balancing, routing, failover
- **Security**: mTLS, authentication, authorization
- **Observability**: Metrics, logging, distributed tracing
- **Policy Enforcement**: Rate limiting, circuit breaking

### Service Mesh Comparison

| Feature | Istio | Linkerd | Consul Connect | AWS App Mesh |
|---------|-------|---------|----------------|--------------|
| Performance | High overhead | Low overhead | Medium overhead | Medium overhead |
| Learning Curve | Steep | Gentle | Medium | Easy (AWS users) |
| Features | Comprehensive | Focused | Comprehensive | AWS-integrated |
| CRDs | Many | Few | Medium | AWS-native |
| Multicluster | Excellent | Good | Excellent | AWS-only |

## Istio Service Mesh

### Installation

#### Using istioctl

```bash
# Download and install istioctl
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.19.0
export PATH=$PWD/bin:$PATH

# Pre-installation checks
istioctl x precheck

# Install Istio with demo profile
istioctl install --set values.defaultRevision=default

# Install with production profile
istioctl install --set values.defaultRevision=default -f - <<EOF
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: control-plane
spec:
  values:
    defaultRevision: default
  components:
    pilot:
      k8s:
        resources:
          requests:
            cpu: 500m
            memory: 2048Mi
        hpaSpec:
          maxReplicas: 5
          minReplicas: 2
    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
        hpaSpec:
          maxReplicas: 5
          minReplicas: 2
        service:
          type: LoadBalancer
EOF

# Verify installation
istioctl verify-install

# Enable Istio injection for namespace
kubectl label namespace default istio-injection=enabled
kubectl get namespace -L istio-injection
```

#### Using Helm

```bash
# Add Istio Helm repository
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# Install Istio base
helm install istio-base istio/base -n istio-system --create-namespace

# Install Istiod
helm install istiod istio/istiod -n istio-system --wait

# Install Istio Ingress Gateway
helm install istio-ingressgateway istio/gateway -n istio-system
```

### Traffic Management

#### Gateway Configuration

```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: bookinfo-gateway
  namespace: default
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - bookinfo.example.com
    tls:
      httpsRedirect: true
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: bookinfo-tls-secret
    hosts:
    - bookinfo.example.com

---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
  namespace: default
spec:
  hosts:
  - bookinfo.example.com
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        prefix: /api/v1
    route:
    - destination:
        host: productpage
        port:
          number: 9080
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

#### Advanced Traffic Routing

```yaml
# Canary deployment with traffic splitting
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews-canary
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 90
    - destination:
        host: reviews
        subset: v2
      weight: 10

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews
spec:
  host: reviews
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
    connectionPool:
      tcp:
        maxConnections: 10
      http:
        http1MaxPendingRequests: 10
        maxRequestsPerConnection: 2
    circuitBreaker:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
```

#### Fault Injection

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: ratings-fault
spec:
  hosts:
  - ratings
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    fault:
      delay:
        percentage:
          value: 100.0
        fixedDelay: 7s
    route:
    - destination:
        host: ratings
        subset: v1
  - fault:
      abort:
        percentage:
          value: 10.0
        httpStatus: 500
    route:
    - destination:
        host: ratings
        subset: v1
```

### Security with Istio

#### mTLS Configuration

```yaml
# Enable strict mTLS for entire mesh
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT

---
# Namespace-specific mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: namespace-policy
  namespace: production
spec:
  mtls:
    mode: STRICT

---
# Service-specific mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: productpage
  namespace: default
spec:
  selector:
    matchLabels:
      app: productpage
  mtls:
    mode: STRICT
  portLevelMtls:
    9080:
      mode: DISABLE  # Disable mTLS for specific port
```

#### Authorization Policies

```yaml
# Deny all policy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: default
spec: {}

---
# Allow specific services
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: default
spec:
  selector:
    matchLabels:
      app: backend
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/frontend"]
  - to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/*"]

---
# JWT Authentication
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: default
spec:
  selector:
    matchLabels:
      app: api-server
  jwtRules:
  - issuer: "https://auth.example.com"
    jwksUri: "https://auth.example.com/.well-known/jwks.json"
    audiences:
    - "api.example.com"

---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: require-jwt
  namespace: default
spec:
  selector:
    matchLabels:
      app: api-server
  rules:
  - from:
    - source:
        requestPrincipals: ["https://auth.example.com/user"]
    to:
    - operation:
        methods: ["GET", "POST"]
    when:
    - key: request.auth.claims[role]
      values: ["admin", "user"]
```

### Observability

#### Distributed Tracing

```yaml
# Install Jaeger
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: jaeger
spec:
  values:
    pilot:
      traceSampling: 100.0  # 100% sampling for testing
  meshConfig:
    extensionProviders:
    - name: jaeger
      envoyExtAuthzHttp:
        service: jaeger.istio-system.svc.cluster.local
        port: 16686

---
# Enable tracing for workload
apiVersion: v1
kind: ConfigMap
metadata:
  name: istio
  namespace: istio-system
data:
  mesh: |
    defaultConfig:
      proxyMetadata:
        BOOTSTRAP_XDS_AGENT: true
    extensionProviders:
    - name: jaeger
      envoyOtelAls:
        service: jaeger.istio-system.svc.cluster.local
        port: 14250
    defaultProviders:
      tracing:
      - jaeger
```

#### Custom Metrics

```yaml
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: custom-metrics
  namespace: default
spec:
  metrics:
  - providers:
    - name: prometheus
  - overrides:
    - match:
        metric: ALL_METRICS
      tagOverrides:
        request_id:
          operation: UPSERT
          value: "%{REQUEST_ID}"
    - match:
        metric: REQUEST_COUNT
      disabled: false
    - match:
        metric: REQUEST_DURATION
      disabled: false

---
# Custom metric definition
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: business-metrics
spec:
  metrics:
  - providers:
    - name: prometheus
  - overrides:
    - match:
        metric: requests_total
      tagOverrides:
        business_unit:
          value: "%{REQUEST_HEADERS['x-business-unit'] | 'unknown'}"
        user_type:
          value: "%{REQUEST_HEADERS['x-user-type'] | 'anonymous'}"
```

#### Access Logging

```yaml
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: access-logging
  namespace: istio-system
spec:
  accessLogging:
  - providers:
    - name: otel
  - filter:
      expression: 'response.code >= 400'
  - format:
      text: |
        [%START_TIME%] "%REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% %PROTOCOL%"
        %RESPONSE_CODE% %RESPONSE_FLAGS% %BYTES_RECEIVED% %BYTES_SENT%
        %DURATION% %RESP(X-ENVOY-UPSTREAM-SERVICE-TIME)% "%REQ(X-FORWARDED-FOR)%"
        "%REQ(USER-AGENT)%" "%REQ(X-REQUEST-ID)%" "%REQ(:AUTHORITY)%" "%UPSTREAM_HOST%"
        outbound|%UPSTREAM_LOCAL_ADDRESS%|%UPSTREAM_CLUSTER%
```

## Linkerd Service Mesh

### Installation

```bash
# Install Linkerd CLI
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install | sh
export PATH=$PATH:$HOME/.linkerd2/bin

# Pre-installation checks
linkerd check --pre

# Install Linkerd control plane
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -

# Verify installation
linkerd check

# Install Linkerd Viz extension
linkerd viz install | kubectl apply -f -
linkerd viz check

# Access Linkerd dashboard
linkerd viz dashboard &
```

### Traffic Management with Linkerd

#### Service Profiles

```yaml
apiVersion: linkerd.io/v1alpha2
kind: ServiceProfile
metadata:
  name: webapp
  namespace: default
spec:
  routes:
  - name: api_routes
    condition:
      method: GET
      pathRegex: /api/.*
    responseClasses:
    - condition:
        status:
          min: 500
          max: 599
      isFailure: true
    timeout: 30s
    retryBudget:
      retryRatio: 0.2
      minRetriesPerSecond: 10
      ttl: 10s
  - name: health_check
    condition:
      method: GET
      pathRegex: /health
    responseClasses:
    - condition:
        status:
          min: 200
          max: 299
      isFailure: false

---
# Traffic split for canary deployments
apiVersion: split.smi-spec.io/v1alpha1
kind: TrafficSplit
metadata:
  name: webapp-split
  namespace: default
spec:
  service: webapp
  backends:
  - service: webapp-v1
    weight: 90
  - service: webapp-v2
    weight: 10
```

#### Multi-cluster Setup

```yaml
# Link clusters
linkerd --context=cluster1 multicluster link --cluster-name cluster1 | \
  kubectl --context=cluster2 apply -f -

linkerd --context=cluster2 multicluster link --cluster-name cluster2 | \
  kubectl --context=cluster1 apply -f -

# Check multicluster status
linkerd --context=cluster1 multicluster gateways
linkerd --context=cluster2 multicluster gateways

# Mirror service across clusters
kubectl --context=cluster1 label service/webapp mirror.linkerd.io/cluster-name=cluster1
kubectl --context=cluster1 annotate service/webapp mirror.linkerd.io/exported=true

# Service profile for multicluster
apiVersion: linkerd.io/v1alpha2
kind: ServiceProfile
metadata:
  name: webapp-cluster2
  namespace: default
spec:
  routes:
  - name: cross_cluster_route
    condition:
      method: GET
      pathRegex: /.*
    timeout: 10s
    retryBudget:
      retryRatio: 0.1
      minRetriesPerSecond: 5
      ttl: 10s
```

### Security with Linkerd

#### Automatic mTLS

```bash
# Check mTLS status
linkerd viz edges -o wide

# View certificates
linkerd viz top deploy/webapp --to deploy/api-server

# Policy for specific services
kubectl apply -f - <<EOF
apiVersion: policy.linkerd.io/v1beta1
kind: Server
metadata:
  name: api-server
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: api-server
  port: 8080
  proxyProtocol: HTTP/2
---
apiVersion: policy.linkerd.io/v1beta1
kind: ServerAuthorization
metadata:
  name: api-server-policy
  namespace: default
spec:
  server:
    name: api-server
  requiredRoutes:
  - pathRegex: /api/.*
    methods: ["GET", "POST"]
  client:
    meshTLS:
      serviceAccounts:
      - name: webapp
        namespace: default
EOF
```

## Consul Connect Service Mesh

### Installation

```bash
# Install Consul using Helm
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install consul hashicorp/consul \
  --namespace consul \
  --create-namespace \
  --set global.name=consul \
  --set connectInject.enabled=true \
  --set global.tls.enabled=true \
  --set global.tls.enableAutoEncrypt=true \
  --set global.datacenter=dc1 \
  --set ui.enabled=true \
  --set ui.service.type=LoadBalancer

# Check installation
kubectl get pods -n consul
kubectl get svc -n consul
```

### Service Configuration

```yaml
# Service with Connect injection
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
      annotations:
        consul.hashicorp.com/connect-inject: "true"
        consul.hashicorp.com/connect-service: "web"
        consul.hashicorp.com/connect-service-upstreams: "api:9090"
    spec:
      containers:
      - name: web
        image: nginx
        ports:
        - containerPort: 80

---
# Service intentions (authorization)
apiVersion: consul.hashicorp.com/v1alpha1
kind: ServiceIntentions
metadata:
  name: web-to-api
spec:
  destination:
    name: api
  sources:
  - name: web
    action: allow
    permissions:
    - action: allow
      http:
        pathPrefix: /api/
        methods: ["GET", "POST"]

---
# Service resolver for load balancing
apiVersion: consul.hashicorp.com/v1alpha1
kind: ServiceResolver
metadata:
  name: api
spec:
  defaultSubset: v1
  subsets:
    v1:
      filter: "Service.Meta.version == v1"
    v2:
      filter: "Service.Meta.version == v2"
  loadBalancer:
    policy: least_request

---
# Service splitter for traffic management
apiVersion: consul.hashicorp.com/v1alpha1
kind: ServiceSplitter
metadata:
  name: api
spec:
  splits:
  - weight: 90
    serviceSubset: v1
  - weight: 10
    serviceSubset: v2
```

## AWS App Mesh

### Installation and Setup

```bash
# Install App Mesh Controller
kubectl apply -k "https://github.com/aws/eks-charts/stable/appmesh-controller/crds?ref=master"

helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm upgrade -i appmesh-controller eks/appmesh-controller \
    --namespace appmesh-system \
    --create-namespace \
    --set region=us-west-2 \
    --set serviceAccount.create=false \
    --set serviceAccount.name=appmesh-controller \
    --set log.level=debug

# Create App Mesh
aws appmesh create-mesh --mesh-name my-mesh
```

### App Mesh Configuration

```yaml
# Mesh resource
apiVersion: appmesh.k8s.aws/v1beta2
kind: Mesh
metadata:
  name: my-mesh
spec:
  namespaceSelector:
    matchLabels:
      mesh: my-mesh

---
# Virtual node
apiVersion: appmesh.k8s.aws/v1beta2
kind: VirtualNode
metadata:
  name: api-server
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: api-server
  listeners:
  - portMapping:
      port: 8080
      protocol: http
    healthCheck:
      protocol: http
      path: /health
      healthyThreshold: 2
      unhealthyThreshold: 3
      timeoutMillis: 2000
      intervalMillis: 5000
  serviceDiscovery:
    dns:
      hostname: api-server.default.svc.cluster.local

---
# Virtual service
apiVersion: appmesh.k8s.aws/v1beta2
kind: VirtualService
metadata:
  name: api-service
  namespace: default
spec:
  awsName: api-service.default.svc.cluster.local
  provider:
    virtualRouter:
      virtualRouterRef:
        name: api-router

---
# Virtual router
apiVersion: appmesh.k8s.aws/v1beta2
kind: VirtualRouter
metadata:
  name: api-router
  namespace: default
spec:
  listeners:
  - portMapping:
      port: 8080
      protocol: http
  routes:
  - name: route-to-api
    httpRoute:
      match:
        prefix: /
      action:
        weightedTargets:
        - virtualNodeRef:
            name: api-server-v1
          weight: 90
        - virtualNodeRef:
            name: api-server-v2
          weight: 10
```

## Service Mesh Best Practices

### Performance Optimization

```yaml
# Istio performance tuning
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: performance-tuned
spec:
  values:
    pilot:
      env:
        PILOT_ENABLE_WORKLOAD_ENTRY_AUTOREGISTRATION: true
        PILOT_ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY: true
        PILOT_PUSH_THROTTLE: 100
        PILOT_MAX_REQUESTS_PER_SECOND: 25
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        concurrency: 2
  meshConfig:
    defaultConfig:
      concurrency: 2
      proxyStatsMatcher:
        inclusionRegexps:
        - ".*outlier_detection.*"
        - ".*circuit_breakers.*"
        - ".*upstream_rq_retry.*"
        - ".*_cx_.*"
        exclusionRegexps:
        - ".*osconfig.*"
```

### Monitoring and Alerting

```yaml
# Prometheus monitoring for service mesh
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: istio-mesh
  namespace: istio-system
spec:
  selector:
    matchLabels:
      app: istiod
  endpoints:
  - port: http-monitoring
    interval: 30s
    path: /stats/prometheus

---
# PrometheusRule for service mesh alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: service-mesh-alerts
  namespace: istio-system
spec:
  groups:
  - name: service-mesh
    rules:
    - alert: HighErrorRate
      expr: sum(rate(istio_requests_total{response_code!~"2.."}[5m])) / sum(rate(istio_requests_total[5m])) > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate in service mesh"

    - alert: HighLatency
      expr: histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le)) > 1000
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High latency in service mesh"

    - alert: MeshControlPlaneDown
      expr: up{job="istiod"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Istio control plane is down"
```

### Debugging and Troubleshooting

```bash
#!/bin/bash
# Service mesh debugging script

SERVICE_MESH=${1:-istio}  # istio, linkerd, consul
NAMESPACE=${2:-default}

case $SERVICE_MESH in
  istio)
    echo "=== Istio Debugging ==="

    # Check Istio installation
    istioctl verify-install

    # Check proxy configuration
    kubectl get pods -n $NAMESPACE -o wide
    istioctl proxy-config cluster <pod-name> -n $NAMESPACE
    istioctl proxy-config listeners <pod-name> -n $NAMESPACE
    istioctl proxy-config routes <pod-name> -n $NAMESPACE

    # Check certificates
    istioctl proxy-config secret <pod-name> -n $NAMESPACE

    # Analyze traffic
    istioctl analyze -n $NAMESPACE

    # Check configuration
    kubectl get virtualservices,destinationrules,gateways -n $NAMESPACE
    ;;

  linkerd)
    echo "=== Linkerd Debugging ==="

    # Check Linkerd installation
    linkerd check

    # Check proxy status
    linkerd viz stat deploy -n $NAMESPACE
    linkerd viz top deploy -n $NAMESPACE
    linkerd viz edges -n $NAMESPACE

    # Check configuration
    kubectl get serviceprofiles,trafficsplits -n $NAMESPACE
    ;;

  consul)
    echo "=== Consul Connect Debugging ==="

    # Check Consul status
    kubectl get pods -n consul
    kubectl exec -n consul consul-server-0 -- consul members

    # Check service registrations
    kubectl exec -n consul consul-server-0 -- consul catalog services

    # Check intentions
    kubectl get serviceintentions -n $NAMESPACE
    ;;
esac

# Common debugging commands
echo "=== Common Service Mesh Debugging ==="

# Check service mesh injection
kubectl get pods -n $NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}'

# Check network policies
kubectl get networkpolicies -n $NAMESPACE

# Test connectivity
kubectl run debug-pod --image=curlimages/curl --rm -it -- /bin/sh
```

### Migration Strategies

```yaml
# Gradual migration with traffic splitting
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: migration-service
spec:
  hosts:
  - migration-service
  http:
  - match:
    - headers:
        x-migration:
          exact: "true"
    route:
    - destination:
        host: migration-service
        subset: v2
  - route:
    - destination:
        host: migration-service
        subset: v1
      weight: 80
    - destination:
        host: migration-service
        subset: v2
      weight: 20

---
# Feature flag based routing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: feature-flag-routing
spec:
  hosts:
  - api-service
  http:
  - match:
    - headers:
        x-feature-flag:
          exact: "new-algorithm"
    route:
    - destination:
        host: api-service
        subset: experimental
  - route:
    - destination:
        host: api-service
        subset: stable
```