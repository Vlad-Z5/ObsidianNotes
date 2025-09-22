# Kubernetes Ingress & Load Balancing

Comprehensive guide to Kubernetes ingress controllers, load balancing strategies, and traffic management for production workloads.

## Ingress Controllers Overview

### NGINX Ingress Controller

**Best For**: General-purpose HTTP/HTTPS ingress with rich feature set and community support.

#### Installation

```bash
# Install using Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.replicaCount=2 \
  --set controller.nodeSelector."kubernetes\.io/arch"=amd64 \
  --set controller.admissionWebhooks.enabled=false

# Install using kubectl
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Check installation
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

#### Basic Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: basic-ingress
  namespace: default
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
  - host: api.example.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: api-v1-service
            port:
              number: 80
      - path: /v2
        pathType: Prefix
        backend:
          service:
            name: api-v2-service
            port:
              number: 80
```

#### Advanced NGINX Ingress Features

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: advanced-nginx-ingress
  namespace: production
  annotations:
    # Traffic routing
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/use-regex: "true"

    # SSL/TLS
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"

    # Rate limiting
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"

    # Authentication
    nginx.ingress.kubernetes.io/auth-basic: "Authentication Required"
    nginx.ingress.kubernetes.io/auth-basic-realm: "Protected Area"
    nginx.ingress.kubernetes.io/auth-secret: basic-auth-secret

    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://frontend.example.com"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
    nginx.ingress.kubernetes.io/cors-allow-headers: "Authorization, Content-Type"

    # Upstream configuration
    nginx.ingress.kubernetes.io/upstream-max-fails: "3"
    nginx.ingress.kubernetes.io/upstream-fail-timeout: "30s"

    # Custom error pages
    nginx.ingress.kubernetes.io/custom-http-errors: "404,503"
    nginx.ingress.kubernetes.io/default-backend: error-pages

    # WebSocket support
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"

    # Session affinity
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "INGRESSCOOKIE"
    nginx.ingress.kubernetes.io/session-cookie-max-age: "86400"
spec:
  tls:
  - hosts:
    - secure.example.com
    secretName: tls-secret
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /api(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: websocket-service
            port:
              number: 8080
```

#### Custom Error Pages

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-error-pages
  namespace: ingress-nginx
data:
  404.html: |
    <!DOCTYPE html>
    <html>
    <head><title>404 Not Found</title></head>
    <body>
      <h1>Page Not Found</h1>
      <p>The requested page could not be found.</p>
    </body>
    </html>
  503.html: |
    <!DOCTYPE html>
    <html>
    <head><title>503 Service Unavailable</title></head>
    <body>
      <h1>Service Unavailable</h1>
      <p>The service is temporarily unavailable. Please try again later.</p>
    </body>
    </html>

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: error-pages
  namespace: ingress-nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: error-pages
  template:
    metadata:
      labels:
        app: error-pages
    spec:
      containers:
      - name: error-pages
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: error-pages
          mountPath: /usr/share/nginx/html
      volumes:
      - name: error-pages
        configMap:
          name: custom-error-pages

---
apiVersion: v1
kind: Service
metadata:
  name: error-pages
  namespace: ingress-nginx
spec:
  selector:
    app: error-pages
  ports:
  - port: 80
    targetPort: 80
```

### Traefik Ingress Controller

**Best For**: Dynamic service discovery, automatic Let's Encrypt certificates, and modern cloud-native features.

#### Installation

```bash
# Install using Helm
helm repo add traefik https://helm.traefik.io/traefik
helm repo update
helm install traefik traefik/traefik \
  --namespace traefik-system \
  --create-namespace \
  --set "ports.websecure.tls.enabled=true" \
  --set "certificatesResolvers.letsencrypt.acme.email=admin@example.com" \
  --set "certificatesResolvers.letsencrypt.acme.storage=/data/acme.json" \
  --set "certificatesResolvers.letsencrypt.acme.httpChallenge.entryPoint=web"

# Check installation
kubectl get pods -n traefik-system
kubectl get svc -n traefik-system
```

#### Traefik Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: traefik-ingress
  namespace: default
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.rule: Host(`app.example.com`)
    traefik.ingress.kubernetes.io/router.tls: "true"
    traefik.ingress.kubernetes.io/router.tls.certresolver: letsencrypt
    traefik.ingress.kubernetes.io/router.middlewares: default-auth@kubernetescrd,default-ratelimit@kubernetescrd
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: app-tls # Auto-generated by Let's Encrypt
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
```

#### Traefik Middleware

```yaml
# Rate limiting middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: ratelimit
  namespace: default
spec:
  rateLimit:
    burst: 100
    average: 50

---
# Authentication middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: auth
  namespace: default
spec:
  basicAuth:
    secret: basic-auth-secret

---
# Headers middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: security-headers
  namespace: default
spec:
  headers:
    customRequestHeaders:
      X-Forwarded-Proto: https
    customResponseHeaders:
      X-Frame-Options: DENY
      X-Content-Type-Options: nosniff
    sslRedirect: true
    stsSeconds: 31536000
    stsIncludeSubdomains: true

---
# Circuit breaker middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: circuit-breaker
  namespace: default
spec:
  circuitBreaker:
    expression: LatencyAtQuantileMS(50.0) > 100
```

### AWS Load Balancer Controller

**Best For**: AWS-native integration with Application Load Balancer (ALB) and Network Load Balancer (NLB).

#### Installation

```bash
# Install AWS Load Balancer Controller
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.5.4/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=my-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::ACCOUNT-ID:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve

# Install controller using Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=my-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

#### ALB Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: alb-ingress
  namespace: default
  annotations:
    # ALB configuration
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/subnets: subnet-12345,subnet-67890

    # SSL/TLS
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012
    alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS-1-2-2017-01
    alb.ingress.kubernetes.io/ssl-redirect: '443'

    # Health checks
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: '5'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '2'

    # Load balancing
    alb.ingress.kubernetes.io/load-balancer-attributes: routing.http2.enabled=true,idle_timeout.timeout_seconds=60

    # Security groups
    alb.ingress.kubernetes.io/security-groups: sg-12345678

    # WAF
    alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:us-west-2:123456789012:regional/webacl/my-web-acl/12345678-1234-1234-1234-123456789012

    # Logging
    alb.ingress.kubernetes.io/load-balancer-attributes: access_logs.s3.enabled=true,access_logs.s3.bucket=my-access-logs-bucket
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

#### Network Load Balancer (NLB) Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nlb-service
  namespace: default
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
    service.beta.kubernetes.io/aws-load-balancer-connection-idle-timeout: "60"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
    service.beta.kubernetes.io/aws-load-balancer-ssl-negotiation-policy: "ELBSecurityPolicy-TLS-1-2-2017-01"
spec:
  type: LoadBalancer
  selector:
    app: high-performance-app
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  - port: 443
    targetPort: 8080
    protocol: TCP
    name: https
```

## Advanced Load Balancing Strategies

### Blue-Green Deployments with Ingress

```yaml
# Blue deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    app: myapp
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: blue
  template:
    metadata:
      labels:
        app: myapp
        version: blue
    spec:
      containers:
      - name: app
        image: myapp:v1.0
        ports:
        - containerPort: 8080

---
# Green deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  labels:
    app: myapp
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: green
  template:
    metadata:
      labels:
        app: myapp
        version: green
    spec:
      containers:
      - name: app
        image: myapp:v2.0
        ports:
        - containerPort: 8080

---
# Services for blue and green
apiVersion: v1
kind: Service
metadata:
  name: app-blue-service
spec:
  selector:
    app: myapp
    version: blue
  ports:
  - port: 80
    targetPort: 8080

---
apiVersion: v1
kind: Service
metadata:
  name: app-green-service
spec:
  selector:
    app: myapp
    version: green
  ports:
  - port: 80
    targetPort: 8080

---
# Ingress for traffic switching
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: blue-green-ingress
  annotations:
    nginx.ingress.kubernetes.io/canary: "false"  # Set to "true" for green
    nginx.ingress.kubernetes.io/canary-weight: "0"  # 0-100 for traffic split
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-blue-service  # Switch to app-green-service
            port:
              number: 80
```

### Canary Deployments

```yaml
# Main service (stable)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: production-ingress
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-stable-service
            port:
              number: 80

---
# Canary service (testing)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: canary-ingress
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% of traffic
    nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    nginx.ingress.kubernetes.io/canary-by-header-value: "enabled"
    nginx.ingress.kubernetes.io/canary-by-cookie: "canary"
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-canary-service
            port:
              number: 80
```

### A/B Testing with Header-based Routing

```yaml
# A/B testing ingress configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ab-testing-ingress
  annotations:
    nginx.ingress.kubernetes.io/server-snippet: |
      set $service_name "app-a-service";
      if ($http_x_experiment = "b") {
        set $service_name "app-b-service";
      }
    nginx.ingress.kubernetes.io/upstream-vhost: $service_name
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-a-service  # Default to version A
            port:
              number: 80

---
# Alternative using Traefik
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: ab-testing-route
spec:
  entryPoints:
  - websecure
  routes:
  - match: Host(`app.example.com`) && Headers(`X-Experiment`, `b`)
    kind: Rule
    services:
    - name: app-b-service
      port: 80
  - match: Host(`app.example.com`)
    kind: Rule
    services:
    - name: app-a-service
      port: 80
```

## SSL/TLS Management

### Certificate Management with cert-manager

#### Installation

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
kubectl wait --for=condition=ready pod -l app=cainjector -n cert-manager --timeout=300s
kubectl wait --for=condition=ready pod -l app=webhook -n cert-manager --timeout=300s
```

#### Let's Encrypt ClusterIssuer

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
    - dns01:
        cloudflare:
          email: admin@example.com
          apiTokenSecretRef:
            name: cloudflare-api-token-secret
            key: api-token

---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
```

#### Automatic Certificate Generation

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: auto-tls-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - app.example.com
    - api.example.com
    secretName: app-tls-secret  # Auto-generated by cert-manager
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

#### Wildcard Certificate

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard-cert
  namespace: default
spec:
  secretName: wildcard-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - "*.example.com"
  - "example.com"

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wildcard-ingress
spec:
  tls:
  - hosts:
    - "*.example.com"
    secretName: wildcard-tls-secret
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

## Performance and Monitoring

### Ingress Metrics and Monitoring

#### NGINX Ingress Metrics

```yaml
# Enable metrics in NGINX ingress
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-configuration
  namespace: ingress-nginx
data:
  enable-vts-status: "true"
  server-tokens: "false"
  ssl-protocols: "TLSv1.2 TLSv1.3"
  proxy-body-size: "100m"
  proxy-read-timeout: "3600"
  proxy-send-timeout: "3600"

---
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: nginx-ingress
  namespace: ingress-nginx
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
  endpoints:
  - port: prometheus
    interval: 30s
    path: /metrics
```

#### Performance Tuning

```yaml
# High-performance NGINX configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-configuration
  namespace: ingress-nginx
data:
  # Worker configuration
  worker-processes: "auto"
  worker-connections: "16384"
  worker-rlimit-nofile: "65536"

  # Keepalive
  upstream-keepalive-connections: "32"
  upstream-keepalive-requests: "100"
  upstream-keepalive-timeout: "60"

  # Buffering
  proxy-buffering: "on"
  proxy-buffer-size: "8k"
  proxy-buffers: "8 8k"
  proxy-busy-buffers-size: "16k"

  # Compression
  enable-brotli: "true"
  brotli-level: "6"
  gzip-level: "6"
  gzip-types: "application/atom+xml application/javascript application/json application/rss+xml application/vnd.ms-fontobject application/x-font-ttf application/x-web-app-manifest+json application/xhtml+xml application/xml font/opentype image/svg+xml image/x-icon text/css text/javascript text/plain text/x-component"

  # Rate limiting
  limit-req-status-code: "429"
  limit-rps: "100"

  # Client settings
  client-header-buffer-size: "64k"
  large-client-header-buffers: "4 64k"
  client-body-buffer-size: "128k"

  # SSL optimization
  ssl-session-cache: "shared:SSL:10m"
  ssl-session-timeout: "10m"
  ssl-buffer-size: "4k"
```

### Load Testing and Benchmarking

```bash
#!/bin/bash
# Load testing script for ingress

INGRESS_HOST="app.example.com"
CONCURRENT_USERS=100
DURATION=300  # 5 minutes
REQUEST_RATE=50

# Using wrk
echo "Starting load test with wrk..."
wrk -t12 -c${CONCURRENT_USERS} -d${DURATION}s --timeout=10s \
    -H "Host: ${INGRESS_HOST}" \
    -H "User-Agent: LoadTest/1.0" \
    --latency \
    https://${INGRESS_HOST}/

# Using Apache Bench
echo "Starting load test with ab..."
ab -n 10000 -c ${CONCURRENT_USERS} \
   -H "Host: ${INGRESS_HOST}" \
   https://${INGRESS_HOST}/

# Using siege
echo "Starting load test with siege..."
siege -c ${CONCURRENT_USERS} -t ${DURATION}S \
      -H "Host: ${INGRESS_HOST}" \
      https://${INGRESS_HOST}/

# Using curl for specific endpoint testing
echo "Testing API endpoints..."
for endpoint in /api/health /api/users /api/orders; do
    echo "Testing ${endpoint}..."
    curl -w "@curl-format.txt" \
         -H "Host: ${INGRESS_HOST}" \
         -s -o /dev/null \
         https://${INGRESS_HOST}${endpoint}
done
```

```bash
# curl-format.txt
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
           http_code:  %{http_code}\n
        size_download:  %{size_download}\n
```

## Production Best Practices

### High Availability Setup

```yaml
# High availability NGINX ingress
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
spec:
  replicas: 3  # Multiple replicas for HA
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: nginx-ingress
  template:
    metadata:
      labels:
        app: nginx-ingress
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
                  - nginx-ingress
              topologyKey: kubernetes.io/hostname
      containers:
      - name: nginx-ingress-controller
        image: k8s.gcr.io/ingress-nginx/controller:v1.8.1
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        readinessProbe:
          httpGet:
            path: /healthz
            port: 10254
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /healthz
            port: 10254
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Security Best Practices

```yaml
# Security-focused ingress configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secure-ingress
  annotations:
    # Force HTTPS
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"

    # Security headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "X-XSS-Protection: 1; mode=block";
      more_set_headers "Strict-Transport-Security: max-age=31536000; includeSubDomains";
      more_set_headers "Content-Security-Policy: default-src 'self'";
      more_set_headers "Referrer-Policy: strict-origin-when-cross-origin";

    # Hide server information
    nginx.ingress.kubernetes.io/server-tokens: "false"

    # Rate limiting
    nginx.ingress.kubernetes.io/rate-limit: "10"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"

    # IP whitelist (if needed)
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

    # Client certificate authentication
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    nginx.ingress.kubernetes.io/auth-tls-secret: "client-ca-secret"
spec:
  tls:
  - hosts:
    - secure.example.com
    secretName: secure-tls-secret
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-service
            port:
              number: 80
```

### Troubleshooting Commands

```bash
# NGINX Ingress troubleshooting
echo "=== NGINX Ingress Troubleshooting ==="

# Check ingress controller pods
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Check ingress resources
kubectl get ingress --all-namespaces
kubectl describe ingress <ingress-name>

# Check generated NGINX configuration
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- cat /etc/nginx/nginx.conf

# Check backend endpoints
kubectl get endpoints
kubectl describe endpoints <service-name>

# Test connectivity
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
# From inside test pod:
# nslookup <service-name>
# wget -O- http://<service-name>:<port>/

# Check SSL certificates
kubectl get certificates
kubectl describe certificate <cert-name>
kubectl get certificaterequests

# Debug DNS resolution
kubectl run dns-test --image=busybox --rm -it -- nslookup <ingress-host>

# Check NGINX ingress metrics
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller-metrics 10254:10254
curl localhost:10254/metrics

# Validate ingress configuration
kubectl apply --dry-run=client -f ingress.yaml
```