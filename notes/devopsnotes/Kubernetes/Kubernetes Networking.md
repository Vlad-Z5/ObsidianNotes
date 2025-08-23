## Networking Comprehensive Deep Dive

### Service Types Detailed Analysis

#### ClusterIP Services

Default service type providing internal cluster communication.

**Use Cases:**

- **Internal APIs**: Backend services accessed only by other cluster components
- **Databases**: Database services accessed by application pods
- **Caching**: Redis, Memcached services for internal use
- **Message Queues**: RabbitMQ, Kafka for internal messaging

**Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
  - port: 80        # Service port
    targetPort: 8080 # Pod port
    protocol: TCP
    name: http
  - port: 443
    targetPort: 8443
    protocol: TCP
    name: https
```

**Advanced ClusterIP Features:**

```yaml
spec:
  clusterIP: 10.96.240.10  # Static IP assignment
  clusterIPs:
  - 10.96.240.10  # IPv4
  - fd00::1       # IPv6 (dual-stack)
  ipFamilies:
  - IPv4
  - IPv6
  ipFamilyPolicy: PreferDualStack
```

#### NodePort Services

Exposes services on each node's IP at a static port (30000-32767 range).

**Use Cases:**

- **Development/Testing**: Direct access to services during development
- **Legacy Integration**: Systems that can't use load balancers
- **On-Premises**: Environments without cloud load balancer integration
- **Debugging**: Direct access to specific pods for troubleshooting

**Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080  # Optional: specific port (30000-32767)
    protocol: TCP
```

**DevOps Considerations:**

- Security implications: NodePort exposes services on all nodes
- Firewall configuration required for external access
- Load balancing needs external solution (e.g., external load balancer)
- Port conflicts possible in multi-service environments

#### LoadBalancer Services

Integrates with cloud provider load balancers.

**Use Cases:**

- **Public Web Applications**: Frontend applications requiring external access
- **APIs**: REST/GraphQL APIs for external consumption
- **Mobile Backends**: Services for mobile applications
- **Third-party Integrations**: Services requiring external partner access

**AWS LoadBalancer Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:region:account:certificate/cert-id"
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
  - port: 443
    targetPort: 8080
    protocol: TCP
```

**Azure LoadBalancer Configuration:**

```yaml
metadata:
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"
    service.beta.kubernetes.io/azure-load-balancer-internal-subnet: "apps-subnet"
    service.beta.kubernetes.io/azure-load-balancer-resource-group: "myResourceGroup"
```

**GCP LoadBalancer Configuration:**

```yaml
metadata:
  annotations:
    cloud.google.com/load-balancer-type: "Internal"
    networking.gke.io/load-balancer-type: "Internal"
```

#### ExternalName Services

Provides DNS alias for external services.

**Use Cases:**

- **Database Migration**: Gradual migration from external to internal databases
- **Service Abstraction**: Abstract external dependencies
- **Environment Consistency**: Same service names across environments
- **Legacy Integration**: Integrate external services into Kubernetes DNS

**Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-database
spec:
  type: ExternalName
  externalName: db.example.com
  ports:
  - port: 5432
    protocol: TCP
```

#### Headless Services

Services without cluster IP for direct pod access.

**Use Cases:**

- **StatefulSets**: Direct access to individual pods
- **Service Discovery**: Applications that need to discover all pod IPs
- **Load Balancing**: Custom load balancing algorithms
- **Peer-to-Peer Applications**: Applications requiring direct pod communication

**Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: headless-service
spec:
  clusterIP: None  # This makes it headless
  selector:
    app: stateful-app
  ports:
  - port: 80
    targetPort: 8080
```

### Ingress Deep Dive

Ingress manages external HTTP/HTTPS access with advanced routing capabilities.

**Ingress Controllers Comparison:**

#### nginx-ingress-controller

**Best For**: General-purpose HTTP/HTTPS ingress with advanced features

**Features**:
- SSL/TLS termination and certificate management
- URL rewriting and redirects
- Rate limiting and authentication
- WebSocket and gRPC support
- Custom error pages and maintenance mode

**Configuration:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/auth-basic: "Authentication Required"
    nginx.ingress.kubernetes.io/auth-basic-realm: "Protected Area"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls-secret
  rules:
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

#### traefik-ingress-controller

**Best For**: Dynamic service discovery and automatic SSL

**Features**:
- Automatic Let's Encrypt certificate generation
- Dynamic configuration updates
- Multiple protocol support (HTTP, HTTPS, TCP, UDP)
- Built-in metrics and tracing
- Advanced middleware support

**Configuration:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: traefik-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.middlewares: "default-auth@kubernetescrd"
    traefik.ingress.kubernetes.io/router.tls.certresolver: "letsencrypt"
spec:
  tls:
  - hosts:
    - app.example.com
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

#### aws-load-balancer-controller

**Best For**: AWS-native integration with ALB/NLB

**Features**:
- AWS Application Load Balancer integration
- Network Load Balancer support
- AWS WAF integration
- Target group binding
- SSL certificate integration with ACM

**Configuration:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aws-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:account:certificate/cert-id
    alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS-1-2-2017-01
    alb.ingress.kubernetes.io/backend-protocol: HTTP
spec:
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

### Network Policies Deep Dive

Network policies provide micro-segmentation and security for pod communication.

**Default Deny All Policy:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}  # Applies to all pods in namespace
  policyTypes:
  - Ingress
  - Egress
```

**Allow from Specific Namespace:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
  namespace: backend
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: frontend
    - podSelector:
        matchLabels:
          app: web-server
    ports:
    - protocol: TCP
      port: 5432
```

**Egress Policy for External Access:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external-egress
spec:
  podSelector:
    matchLabels:
      app: web-app
  policyTypes:
  - Egress
  egress:
  - to: []  # Allow all egress
    ports:
    - protocol: TCP
      port: 443  # HTTPS only
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```
        backend:
          service:
            name: app-service
            port:
              number: 80
```

### Network Policies

Control traffic between pods

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-db
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
    ports:
    - protocol: TCP
      port: 5432
```
