# Thanos Security and Authentication

Complete security guide covering authentication mechanisms, authorization models, TLS/mTLS configuration, network security, secrets management, RBAC implementation, security hardening, compliance requirements, and threat mitigation for production Thanos deployments.

**Key Concepts:** TLS encryption, mTLS authentication, basic auth, OAuth2/OIDC, RBAC policies, network policies, secrets management, encryption at rest, security scanning, compliance frameworks, threat modeling

## Security Architecture

### Thanos Security Model

```yaml
thanos_security_layers:
  transport_security:
    description: "Encrypt data in transit"
    components:
      - "TLS for HTTP endpoints"
      - "mTLS for gRPC StoreAPI communication"
      - "Certificate management and rotation"
    threat_mitigation:
      - "Man-in-the-middle attacks"
      - "Data eavesdropping"
      - "Unauthorized component communication"

  authentication:
    description: "Verify identity of clients and components"
    methods:
      - "Basic authentication (HTTP)"
      - "Bearer token authentication"
      - "OAuth2/OIDC integration"
      - "mTLS certificate-based auth"
      - "Kubernetes ServiceAccount tokens"
    components:
      - "Thanos Query API access"
      - "Grafana to Thanos Query"
      - "Inter-component StoreAPI"

  authorization:
    description: "Control access to resources"
    mechanisms:
      - "Kubernetes RBAC"
      - "Label-based query filtering"
      - "Namespace isolation"
      - "Network policies"
    granularity:
      - "Component-level (pod access)"
      - "API-level (endpoint access)"
      - "Data-level (label selectors)"

  data_encryption:
    description: "Protect data at rest"
    implementations:
      - "Object storage encryption (S3 SSE, KMS)"
      - "Kubernetes secret encryption"
      - "Encrypted persistent volumes"
    compliance:
      - "GDPR, HIPAA, PCI-DSS requirements"

  network_security:
    description: "Control network traffic"
    controls:
      - "Kubernetes NetworkPolicies"
      - "Service mesh (Istio, Linkerd)"
      - "Cloud security groups"
      - "VPC peering and private endpoints"
```

## TLS Configuration

### TLS for HTTP Endpoints

```yaml
# Generate self-signed certificates for testing
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-tls-generator
  namespace: monitoring
data:
  generate-certs.sh: |
    #!/bin/bash
    # Generate CA
    openssl genrsa -out ca.key 4096
    openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
      -subj "/CN=Thanos CA"

    # Generate server certificate
    openssl genrsa -out server.key 2048
    openssl req -new -key server.key -out server.csr \
      -subj "/CN=thanos-query.monitoring.svc.cluster.local"

    # Sign server certificate
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
      -CAcreateserial -out server.crt -days 365 \
      -extensions v3_req -extfile <(cat <<EOF
    [v3_req]
    subjectAltName = DNS:thanos-query.monitoring.svc.cluster.local,DNS:thanos-query,DNS:localhost
    EOF
    )

    # Create Kubernetes secret
    kubectl create secret tls thanos-tls \
      --cert=server.crt \
      --key=server.key \
      -n monitoring

    kubectl create secret generic thanos-ca \
      --from-file=ca.crt=ca.crt \
      -n monitoring

---
# Thanos Query with TLS
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query
  namespace: monitoring
spec:
  template:
    spec:
      containers:
      - name: thanos-query
        image: thanosio/thanos:v0.32.5
        args:
        - query
        - --http-address=0.0.0.0:9090
        - --grpc-address=0.0.0.0:10901

        # TLS configuration
        - --http.config=/etc/thanos/http-config.yml
        - --grpc-server-tls-cert=/etc/thanos/tls/tls.crt
        - --grpc-server-tls-key=/etc/thanos/tls/tls.key
        - --grpc-server-tls-client-ca=/etc/thanos/ca/ca.crt

        # Other args...
        - --query=thanos-query.monitoring.svc.cluster.local:9090

        volumeMounts:
        - name: tls
          mountPath: /etc/thanos/tls
          readOnly: true
        - name: ca
          mountPath: /etc/thanos/ca
          readOnly: true
        - name: http-config
          mountPath: /etc/thanos
          readOnly: true

      volumes:
      - name: tls
        secret:
          secretName: thanos-tls
      - name: ca
        secret:
          secretName: thanos-ca
      - name: http-config
        configMap:
          name: thanos-http-config

---
# HTTP TLS configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-http-config
  namespace: monitoring
data:
  http-config.yml: |
    tls_server_config:
      cert_file: /etc/thanos/tls/tls.crt
      key_file: /etc/thanos/tls/tls.key
      client_ca_file: /etc/thanos/ca/ca.crt
      client_auth_type: RequestClientCert
```

### mTLS for StoreAPI Communication

```yaml
# Client-side TLS configuration for Thanos Query
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query
  namespace: monitoring
spec:
  template:
    spec:
      containers:
      - name: thanos-query
        args:
        # Client TLS for connecting to stores
        - --grpc-client-tls-secure
        - --grpc-client-tls-cert=/etc/thanos/tls/tls.crt
        - --grpc-client-tls-key=/etc/thanos/tls/tls.key
        - --grpc-client-tls-ca=/etc/thanos/ca/ca.crt
        - --grpc-client-server-name=thanos-store.monitoring.svc.cluster.local

        # Store endpoints with TLS
        - --store=dnssrv+_grpc._tcp.thanos-store.monitoring.svc.cluster.local

---
# Server-side TLS for Store Gateway
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thanos-store
  namespace: monitoring
spec:
  template:
    spec:
      containers:
      - name: thanos-store
        args:
        # Server TLS configuration
        - --grpc-server-tls-cert=/etc/thanos/tls/tls.crt
        - --grpc-server-tls-key=/etc/thanos/tls/tls.key
        - --grpc-server-tls-client-ca=/etc/thanos/ca/ca.crt

        volumeMounts:
        - name: tls
          mountPath: /etc/thanos/tls
          readOnly: true
        - name: ca
          mountPath: /etc/thanos/ca
          readOnly: true

      volumes:
      - name: tls
        secret:
          secretName: thanos-store-tls
      - name: ca
        secret:
          secretName: thanos-ca
```

### Cert-Manager Integration

```yaml
# Use cert-manager for automatic certificate management
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: thanos-query-tls
  namespace: monitoring
spec:
  secretName: thanos-query-tls
  duration: 2160h  # 90 days
  renewBefore: 360h  # 15 days before expiry
  subject:
    organizations:
    - Company Name
  isCA: false
  privateKey:
    algorithm: RSA
    encoding: PKCS1
    size: 2048
  usages:
  - server auth
  - client auth
  dnsNames:
  - thanos-query.monitoring.svc.cluster.local
  - thanos-query
  - localhost
  issuerRef:
    name: thanos-ca-issuer
    kind: ClusterIssuer
    group: cert-manager.io

---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: thanos-ca-issuer
spec:
  ca:
    secretName: thanos-ca-key-pair
```

## Authentication Mechanisms

### Basic Authentication

```yaml
# HTTP Basic Auth configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-http-config
  namespace: monitoring
data:
  http-config.yml: |
    tls_server_config:
      cert_file: /etc/thanos/tls/tls.crt
      key_file: /etc/thanos/tls/tls.key

    # Basic authentication
    basic_auth_users:
      admin: $2y$10$hash_of_password_here
      grafana: $2y$10$another_hash_here
      prometheus: $2y$10$yet_another_hash

---
# Generate bcrypt password hashes
apiVersion: batch/v1
kind: Job
metadata:
  name: generate-passwords
  namespace: monitoring
spec:
  template:
    spec:
      containers:
      - name: htpasswd
        image: httpd:2.4-alpine
        command:
        - sh
        - -c
        - |
          htpasswd -nbB admin "admin_password"
          htpasswd -nbB grafana "grafana_password"
          htpasswd -nbB prometheus "prometheus_password"
      restartPolicy: Never
```

### OAuth2 Proxy Integration

```yaml
# OAuth2 Proxy in front of Thanos Query
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth2-proxy
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: oauth2-proxy
  template:
    metadata:
      labels:
        app: oauth2-proxy
    spec:
      containers:
      - name: oauth2-proxy
        image: quay.io/oauth2-proxy/oauth2-proxy:v7.4.0
        args:
        - --provider=oidc
        - --provider-display-name="Company SSO"
        - --oidc-issuer-url=https://sso.company.com
        - --client-id=$(OAUTH2_CLIENT_ID)
        - --client-secret=$(OAUTH2_CLIENT_SECRET)
        - --cookie-secret=$(OAUTH2_COOKIE_SECRET)
        - --email-domain=company.com
        - --upstream=http://thanos-query:9090
        - --http-address=0.0.0.0:4180
        - --redirect-url=https://thanos.company.com/oauth2/callback
        - --cookie-secure=true
        - --cookie-httponly=true
        - --set-xauthrequest=true
        - --pass-access-token=true
        - --skip-auth-regex=^/api/v1/query  # Public queries

        env:
        - name: OAUTH2_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secrets
              key: client-id
        - name: OAUTH2_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secrets
              key: client-secret
        - name: OAUTH2_COOKIE_SECRET
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secrets
              key: cookie-secret

        ports:
        - containerPort: 4180
          name: http

        resources:
          requests:
            memory: 128Mi
            cpu: 100m
          limits:
            memory: 256Mi
            cpu: 200m

---
apiVersion: v1
kind: Service
metadata:
  name: oauth2-proxy
  namespace: monitoring
spec:
  ports:
  - port: 4180
    targetPort: 4180
  selector:
    app: oauth2-proxy

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: thanos-query-ingress
  namespace: monitoring
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - thanos.company.com
    secretName: thanos-tls
  rules:
  - host: thanos.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: oauth2-proxy
            port:
              number: 4180
```

## Kubernetes RBAC

### Service Account and RBAC Configuration

```yaml
# Thanos Query ServiceAccount and RBAC
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thanos-query
  namespace: monitoring
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/thanos-query-role

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: thanos-query
rules:
# Required for DNS service discovery
- apiGroups: [""]
  resources: ["endpoints", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: thanos-query
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: thanos-query
subjects:
- kind: ServiceAccount
  name: thanos-query
  namespace: monitoring

---
# Thanos Store ServiceAccount (object storage access)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thanos-store
  namespace: monitoring
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/thanos-store-role

---
# Thanos Compactor ServiceAccount (read/write object storage)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thanos-compactor
  namespace: monitoring
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/thanos-compactor-role

---
# Thanos Ruler ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thanos-ruler
  namespace: monitoring
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/thanos-ruler-role

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: thanos-ruler
rules:
# For querying Thanos Query
- apiGroups: [""]
  resources: ["services", "endpoints"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: thanos-ruler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: thanos-ruler
subjects:
- kind: ServiceAccount
  name: thanos-ruler
  namespace: monitoring
```

### IAM Roles for Service Accounts (IRSA)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ThanosQueryReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::thanos-metrics-production",
        "arn:aws:s3:::thanos-metrics-production/*"
      ]
    },
    {
      "Sid": "ThanosKMSDecrypt",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"
    }
  ]
}
```

## Network Security

### Kubernetes Network Policies

```yaml
# Network policy for Thanos Query
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: thanos-query-netpol
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: thanos-query
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow from Grafana
  - from:
    - namespaceSelector:
        matchLabels:
          name: grafana
    ports:
    - protocol: TCP
      port: 9090
  # Allow from other Thanos Query instances
  - from:
    - podSelector:
        matchLabels:
          app: thanos-query
    ports:
    - protocol: TCP
      port: 9090
    - protocol: TCP
      port: 10901
  # Allow from ingress controller
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 9090
  egress:
  # Allow to Store Gateway
  - to:
    - podSelector:
        matchLabels:
          app: thanos-store
    ports:
    - protocol: TCP
      port: 10901
  # Allow to Ruler
  - to:
    - podSelector:
        matchLabels:
          app: thanos-ruler
    ports:
    - protocol: TCP
      port: 10901
  # Allow to Sidecar
  - to:
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 10901
  # Allow DNS
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53

---
# Network policy for Store Gateway
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: thanos-store-netpol
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: thanos-store
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow from Query
  - from:
    - podSelector:
        matchLabels:
          app: thanos-query
    ports:
    - protocol: TCP
      port: 10901
  # Allow from other Store instances
  - from:
    - podSelector:
        matchLabels:
          app: thanos-store
    ports:
    - protocol: TCP
      port: 10901
  egress:
  # Allow to object storage (S3, GCS, Azure)
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS for cloud storage
  # Allow DNS
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53

---
# Network policy for Compactor
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: thanos-compactor-netpol
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: thanos-compactor
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow Prometheus scraping
  - from:
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 10902
  egress:
  # Allow to object storage
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443
  # Allow DNS
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

## Secrets Management

### External Secrets Operator

```yaml
# External Secrets Operator for object storage credentials
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: monitoring
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: thanos-external-secrets

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: thanos-objstore-config
  namespace: monitoring
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: thanos-objstore-config
    creationPolicy: Owner
    template:
      data:
        objstore.yml: |
          type: S3
          config:
            bucket: "thanos-metrics-production"
            endpoint: "s3.us-east-1.amazonaws.com"
            region: "us-east-1"
            access_key: "{{ .AWS_ACCESS_KEY_ID }}"
            secret_key: "{{ .AWS_SECRET_ACCESS_KEY }}"
  data:
  - secretKey: AWS_ACCESS_KEY_ID
    remoteRef:
      key: thanos/storage-credentials
      property: access_key_id
  - secretKey: AWS_SECRET_ACCESS_KEY
    remoteRef:
      key: thanos/storage-credentials
      property: secret_access_key
```

### Sealed Secrets

```yaml
# Using Sealed Secrets for GitOps
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: thanos-objstore-config
  namespace: monitoring
spec:
  encryptedData:
    objstore.yml: AgBH7x8k...  # Encrypted data
  template:
    metadata:
      name: thanos-objstore-config
      namespace: monitoring
    type: Opaque
```

## Security Hardening

### Pod Security Standards

```yaml
# Pod Security Context
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query
  namespace: monitoring
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        fsGroup: 65534
        seccompProfile:
          type: RuntimeDefault

      containers:
      - name: thanos-query
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 65534
          capabilities:
            drop:
            - ALL

        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /var/cache

      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
```

### Image Security Scanning

```yaml
# Scan Thanos images for vulnerabilities
scan_process:
  tools:
    - "Trivy"
    - "Clair"
    - "Anchore"

  cicd_integration: |
    # GitLab CI example
    scan_image:
      stage: security
      image: aquasec/trivy:latest
      script:
        - trivy image --severity HIGH,CRITICAL thanosio/thanos:v0.32.5
      allow_failure: false

  automated_updates:
    renovate: "Automatic PR for new versions"
    dependabot: "GitHub dependency updates"
```

### AppArmor and Seccomp Profiles

```yaml
# AppArmor profile annotation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query
spec:
  template:
    metadata:
      annotations:
        container.apparmor.security.beta.kubernetes.io/thanos-query: runtime/default
    spec:
      securityContext:
        seccompProfile:
          type: RuntimeDefault
```

## Compliance and Auditing

### Audit Logging

```yaml
audit_configuration:
  kubernetes_audit:
    description: "Log all API access to Thanos components"
    configuration: |
      # Kubernetes audit policy
      apiVersion: audit.k8s.io/v1
      kind: Policy
      rules:
      - level: RequestResponse
        resources:
        - group: ""
          resources: ["secrets"]
        namespaces: ["monitoring"]
      - level: Metadata
        resources:
        - group: "apps"
          resources: ["deployments", "statefulsets"]
        namespaces: ["monitoring"]

  thanos_query_logging:
    request_logging:
      enabled: true
      flag: "--log.level=info"
      format: "logfmt"

  alertmanager_audit:
    notification_log: "Track all alert notifications"
    silence_log: "Track alert silences"
```

### Compliance Frameworks

```yaml
compliance_requirements:
  gdpr:
    data_retention: "Configurable retention policies"
    data_deletion: "Compactor enforces retention"
    encryption: "TLS and object storage encryption"
    audit_trail: "Kubernetes audit logs"

  hipaa:
    encryption_transit: "mTLS for all communication"
    encryption_rest: "S3 SSE-KMS encryption"
    access_control: "RBAC and network policies"
    audit_logging: "Comprehensive audit trails"

  pci_dss:
    network_segmentation: "NetworkPolicies"
    encryption: "TLS 1.2+ required"
    access_control: "Principle of least privilege"
    logging_monitoring: "Centralized logging"

  soc2:
    availability: "High availability configuration"
    confidentiality: "Encryption and access control"
    integrity: "Checksums and verification"
    monitoring: "Comprehensive observability"
```

## Security Best Practices

### Security Checklist

```yaml
security_checklist:
  transport_security:
    - "✓ Enable TLS for all HTTP endpoints"
    - "✓ Enable mTLS for gRPC StoreAPI"
    - "✓ Use cert-manager for certificate management"
    - "✓ Enforce TLS 1.2+ only"

  authentication:
    - "✓ Implement OAuth2/OIDC for user access"
    - "✓ Use ServiceAccount tokens for component auth"
    - "✓ Rotate credentials regularly"
    - "✓ Use strong password policies for basic auth"

  authorization:
    - "✓ Implement Kubernetes RBAC"
    - "✓ Use least privilege principle"
    - "✓ Apply NetworkPolicies"
    - "✓ Restrict namespace access"

  secrets_management:
    - "✓ Never commit secrets to Git"
    - "✓ Use External Secrets Operator or Sealed Secrets"
    - "✓ Enable Kubernetes secret encryption at rest"
    - "✓ Use IAM roles instead of static credentials"

  container_security:
    - "✓ Run as non-root user"
    - "✓ Use read-only root filesystem"
    - "✓ Drop all capabilities"
    - "✓ Apply Pod Security Standards"
    - "✓ Scan images for vulnerabilities"

  object_storage_security:
    - "✓ Enable server-side encryption"
    - "✓ Use private buckets (no public access)"
    - "✓ Enable versioning for backup"
    - "✓ Apply bucket policies for access control"
    - "✓ Enable access logging"

  network_security:
    - "✓ Apply NetworkPolicies to all components"
    - "✓ Use private networking for cross-cluster"
    - "✓ Implement ingress authentication"
    - "✓ Use service mesh for advanced security"

  monitoring_auditing:
    - "✓ Enable audit logging"
    - "✓ Monitor authentication failures"
    - "✓ Alert on security events"
    - "✓ Regular security reviews"
```

### Incident Response

```yaml
security_incident_response:
  credential_compromise:
    immediate_actions:
      - "Rotate compromised credentials"
      - "Review access logs for unauthorized activity"
      - "Revoke API tokens"
      - "Update Kubernetes secrets"
    recovery:
      - "Deploy new certificates"
      - "Restart affected components"
      - "Verify no unauthorized data access"

  unauthorized_access:
    detection:
      - "Monitor failed authentication attempts"
      - "Alert on unusual query patterns"
      - "Track object storage access logs"
    response:
      - "Block suspicious IP addresses"
      - "Enable additional authentication"
      - "Review and tighten RBAC policies"

  data_breach:
    containment:
      - "Identify compromised data"
      - "Revoke access immediately"
      - "Enable MFA if not already"
    notification:
      - "Follow compliance requirements"
      - "Notify affected parties"
      - "Document incident details"
```

This comprehensive security guide provides all necessary configurations and procedures for securing Thanos infrastructure in production environments, meeting compliance requirements and industry best practices.
