## Production Secrets Management

### Secrets Management Principles

#### 1. Zero-Trust Security Model
```bash
# Never store secrets in plaintext
# ❌ BAD
export DB_PASSWORD="supersecret123"
kubectl create secret generic db-secret --from-literal=password=supersecret123

# ✅ GOOD - Use sealed secrets or external secret management
kubectl create secret generic db-secret --dry-run=client -o yaml | \
    kubeseal -o yaml > db-secret-sealed.yaml
```

#### 2. Secret Lifecycle Management
```yaml
# secrets/lifecycle/secret-policy.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: secret-management-policy
  namespace: security
data:
  policy.yaml: |
    secrets:
      rotation:
        database_passwords: 90d    # Rotate every 90 days
        api_keys: 180d            # Rotate every 6 months
        certificates: 365d        # Rotate yearly
        service_accounts: 30d     # Rotate monthly
      
      classification:
        critical:                 # Production database, encryption keys
          encryption: required
          access_logging: enabled
          approval_required: true
        
        sensitive:                # API keys, OAuth tokens
          encryption: required
          access_logging: enabled
          approval_required: false
        
        internal:                 # Service-to-service tokens
          encryption: recommended
          access_logging: basic
          approval_required: false
      
      access_controls:
        minimum_approvers: 2
        break_glass_access: enabled
        audit_retention: 2y
        mfa_required: true
```

### HashiCorp Vault Integration

#### Production Vault Setup
```bash
#!/bin/bash
# scripts/vault-production-setup.sh

set -euo pipefail

readonly VAULT_NAMESPACE="vault"
readonly VAULT_RELEASE="vault"

# Install Vault with HA configuration
install_vault_ha() {
    log_info "Installing Vault in HA mode..."
    
    # Create values file for production
    cat > vault-values.yaml <<EOF
global:
  enabled: true
  tlsDisable: false

server:
  image:
    repository: "hashicorp/vault"
    tag: "1.15.2"
  
  # High Availability configuration
  ha:
    enabled: true
    replicas: 3
    raft:
      enabled: true
      setNodeId: true
      config: |
        ui = true
        listener "tcp" {
          tls_disable = 0
          address = "[::]:8200"
          cluster_address = "[::]:8201"
          tls_cert_file = "/vault/userconfig/vault-tls/tls.crt"
          tls_key_file = "/vault/userconfig/vault-tls/tls.key"
        }
        
        storage "raft" {
          path = "/vault/data"
          
          retry_join {
            leader_api_addr = "https://vault-0.vault-internal.vault.svc.cluster.local:8200"
            leader_ca_cert_file = "/vault/userconfig/vault-tls/ca.crt"
          }
          retry_join {
            leader_api_addr = "https://vault-1.vault-internal.vault.svc.cluster.local:8200"
            leader_ca_cert_file = "/vault/userconfig/vault-tls/ca.crt"
          }
          retry_join {
            leader_api_addr = "https://vault-2.vault-internal.vault.svc.cluster.local:8200"
            leader_ca_cert_file = "/vault/userconfig/vault-tls/ca.crt"
          }
        }
        
        service_registration "kubernetes" {}
        
        # Enable Prometheus metrics
        telemetry {
          prometheus_retention_time = "30s"
          disable_hostname = true
        }
  
  # Resource limits
  resources:
    requests:
      memory: 256Mi
      cpu: 250m
    limits:
      memory: 1Gi
      cpu: 1000m
  
  # Volume configuration
  volumes:
  - name: vault-tls
    secret:
      secretName: vault-tls
  
  volumeMounts:
  - mountPath: /vault/userconfig/vault-tls
    name: vault-tls
    readOnly: true
  
  # Security context
  securityContext:
    runAsNonRoot: true
    runAsUser: 100
    fsGroup: 1000

# UI Configuration
ui:
  enabled: true
  serviceType: "ClusterIP"

# Injector for automatic secret injection
injector:
  enabled: true
  replicas: 2
  resources:
    requests:
      memory: 128Mi
      cpu: 125m
    limits:
      memory: 256Mi
      cpu: 250m
EOF
    
    # Install Vault
    helm repo add hashicorp https://helm.releases.hashicorp.com
    helm repo update
    
    kubectl create namespace "$VAULT_NAMESPACE" || true
    
    helm upgrade --install "$VAULT_RELEASE" hashicorp/vault \
        --namespace "$VAULT_NAMESPACE" \
        --values vault-values.yaml \
        --wait --timeout 300s
    
    log_success "Vault installed successfully"
}

# Initialize Vault cluster
initialize_vault() {
    log_info "Initializing Vault cluster..."
    
    # Wait for Vault to be ready
    kubectl wait --for=condition=Ready pod/vault-0 -n "$VAULT_NAMESPACE" --timeout=300s
    
    # Initialize Vault
    local init_output
    init_output=$(kubectl exec -n "$VAULT_NAMESPACE" vault-0 -- vault operator init \
                 -key-shares=5 -key-threshold=3 -format=json)
    
    # Save keys securely (in production, use proper key management)
    echo "$init_output" | jq -r '.unseal_keys_b64[]' > /tmp/vault-unseal-keys.txt
    echo "$init_output" | jq -r '.root_token' > /tmp/vault-root-token.txt
    
    log_warn "IMPORTANT: Unseal keys and root token saved to /tmp/"
    log_warn "Move these to secure storage immediately!"
    
    # Unseal Vault instances
    local unseal_keys
    mapfile -t unseal_keys < <(echo "$init_output" | jq -r '.unseal_keys_b64[]' | head -3)
    
    for i in 0 1 2; do
        for key in "${unseal_keys[@]}"; do
            kubectl exec -n "$VAULT_NAMESPACE" "vault-$i" -- vault operator unseal "$key" || true
        done
    done
    
    log_success "Vault cluster initialized and unsealed"
}

# Configure Vault authentication
configure_vault_auth() {
    local root_token="$1"
    
    log_info "Configuring Vault authentication methods..."
    
    # Set Vault address and token
    export VAULT_ADDR="https://vault.vault.svc.cluster.local:8200"
    export VAULT_TOKEN="$root_token"
    
    # Port forward for configuration
    kubectl port-forward -n "$VAULT_NAMESPACE" svc/vault 8200:8200 &
    local port_forward_pid=$!
    
    sleep 5
    export VAULT_ADDR="https://localhost:8200"
    export VAULT_SKIP_VERIFY=true
    
    # Enable Kubernetes authentication
    vault auth enable kubernetes
    
    # Configure Kubernetes auth
    vault write auth/kubernetes/config \
        token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
        kubernetes_host=https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT \
        kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    
    # Enable LDAP authentication for humans
    vault auth enable ldap
    
    vault write auth/ldap/config \
        url="ldap://ldap.company.com" \
        userattr=uid \
        userdn="ou=users,dc=company,dc=com" \
        groupdn="ou=groups,dc=company,dc=com" \
        groupattr=cn \
        binddn="cn=vault,ou=service,dc=company,dc=com" \
        bindpass="$LDAP_BIND_PASSWORD" \
        insecure_tls=false \
        starttls=true
    
    # Enable AppRole for applications
    vault auth enable approle
    
    # Clean up port forward
    kill $port_forward_pid
    
    log_success "Vault authentication configured"
}

# Setup secret engines
setup_secret_engines() {
    log_info "Setting up Vault secret engines..."
    
    # Key-Value secrets v2
    vault secrets enable -path=secrets kv-v2
    vault secrets enable -path=app-secrets kv-v2
    
    # Database secrets engine
    vault secrets enable database
    
    # PKI for certificate management
    vault secrets enable pki
    vault secrets tune -max-lease-ttl=87600h pki
    
    # Configure PKI root CA
    vault write pki/root/generate/internal \
        common_name="company.com" \
        ttl=87600h
    
    vault write pki/config/urls \
        issuing_certificates="$VAULT_ADDR/v1/pki/ca" \
        crl_distribution_points="$VAULT_ADDR/v1/pki/crl"
    
    # Intermediate CA
    vault secrets enable -path=pki_int pki
    vault secrets tune -max-lease-ttl=43800h pki_int
    
    vault write -format=json pki_int/intermediate/generate/internal \
        common_name="company.com Intermediate Authority" \
        | jq -r '.data.csr' > pki_intermediate.csr
    
    vault write -format=json pki/root/sign-intermediate csr=@pki_intermediate.csr \
        format=pem_bundle ttl="43800h" \
        | jq -r '.data.certificate' > intermediate.cert.pem
    
    vault write pki_int/intermediate/set-signed certificate=@intermediate.cert.pem
    
    log_success "Secret engines configured"
}

main() {
    case "${1:-install}" in
        "install")
            install_vault_ha
            ;;
        "init")
            initialize_vault
            ;;
        "auth")
            configure_vault_auth "$2"
            ;;
        "engines")
            setup_secret_engines
            ;;
        "all")
            install_vault_ha
            initialize_vault
            local root_token
            root_token=$(cat /tmp/vault-root-token.txt)
            configure_vault_auth "$root_token"
            setup_secret_engines
            ;;
        *)
            echo "Usage: $0 {install|init|auth <token>|engines|all}"
            exit 1
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

#### Vault Policy Management
```bash
#!/bin/bash
# scripts/vault-policy-management.sh

# Create application-specific policies
create_app_policies() {
    log_info "Creating application policies..."
    
    # Web application policy
    vault policy write web-app-policy - <<EOF
# Read application secrets
path "app-secrets/data/web-app/*" {
  capabilities = ["read"]
}

# Read database credentials
path "database/creds/web-app-role" {
  capabilities = ["read"]
}

# Read certificates
path "pki_int/issue/web-app-role" {
  capabilities = ["create", "update"]
}
EOF
    
    # API service policy
    vault policy write api-service-policy - <<EOF
# Read/write API secrets
path "app-secrets/data/api-service/*" {
  capabilities = ["read", "create", "update", "delete"]
}

# Database access
path "database/creds/api-service-role" {
  capabilities = ["read"]
}

# Transit encryption
path "transit/encrypt/api-service" {
  capabilities = ["update"]
}

path "transit/decrypt/api-service" {
  capabilities = ["update"]
}
EOF
    
    # Backup service policy (minimal access)
    vault policy write backup-service-policy - <<EOF
# Read-only access to specific secrets
path "app-secrets/data/backup/*" {
  capabilities = ["read"]
}

# No database access for backup service
EOF
    
    log_success "Application policies created"
}

# Create role-based policies for humans
create_human_policies() {
    log_info "Creating human access policies..."
    
    # SRE team policy
    vault policy write sre-policy - <<EOF
# Full access to application secrets
path "app-secrets/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Database credential management
path "database/creds/*" {
  capabilities = ["read"]
}

path "database/config/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# PKI management
path "pki_int/issue/*" {
  capabilities = ["create", "update"]
}

# Policy management (limited)
path "sys/policies/acl/*" {
  capabilities = ["read", "list"]
}

# Auth method configuration
path "auth/kubernetes/role/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF
    
    # Developer policy (limited access)
    vault policy write developer-policy - <<EOF
# Read-only access to non-production secrets
path "app-secrets/data/development/*" {
  capabilities = ["read", "list"]
}

path "app-secrets/data/staging/*" {
  capabilities = ["read", "list"]
}

# No production access
path "app-secrets/data/production/*" {
  capabilities = ["deny"]
}

# Limited database access
path "database/creds/dev-*" {
  capabilities = ["read"]
}
EOF
    
    # Security team policy
    vault policy write security-policy - <<EOF
# Full audit access
path "sys/audit/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Policy management
path "sys/policies/acl/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Auth method management
path "sys/auth/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Secret engine management
path "sys/mounts/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Read all secrets for security audits
path "app-secrets/metadata/*" {
  capabilities = ["read", "list"]
}
EOF
    
    log_success "Human policies created"
}

# Configure Kubernetes roles
configure_k8s_roles() {
    log_info "Configuring Kubernetes authentication roles..."
    
    # Web application role
    vault write auth/kubernetes/role/web-app \
        bound_service_account_names=web-app \
        bound_service_account_namespaces=production \
        policies=web-app-policy \
        ttl=1h \
        max_ttl=4h
    
    # API service role
    vault write auth/kubernetes/role/api-service \
        bound_service_account_names=api-service \
        bound_service_account_namespaces=production \
        policies=api-service-policy \
        ttl=30m \
        max_ttl=2h
    
    # Backup service role
    vault write auth/kubernetes/role/backup-service \
        bound_service_account_names=backup-service \
        bound_service_account_namespaces=production \
        policies=backup-service-policy \
        ttl=2h \
        max_ttl=8h
    
    log_success "Kubernetes roles configured"
}

# Configure LDAP group mappings
configure_ldap_groups() {
    log_info "Configuring LDAP group mappings..."
    
    # Map LDAP groups to Vault policies
    vault write auth/ldap/groups/sre-team policies=sre-policy
    vault write auth/ldap/groups/developers policies=developer-policy
    vault write auth/ldap/groups/security-team policies=security-policy
    vault write auth/ldap/groups/platform-team policies=sre-policy
    
    log_success "LDAP groups configured"
}

# Configure database secrets engine
configure_database_engine() {
    log_info "Configuring database secrets engine..."
    
    # PostgreSQL connection
    vault write database/config/postgresql \
        plugin_name=postgresql-database-plugin \
        connection_url="postgresql://{{username}}:{{password}}@postgres.production.svc.cluster.local:5432/postgres?sslmode=require" \
        allowed_roles="web-app-role,api-service-role" \
        username="vault" \
        password="$POSTGRES_VAULT_PASSWORD"
    
    # Web application database role
    vault write database/roles/web-app-role \
        db_name=postgresql \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
                            GRANT CONNECT ON DATABASE webapp TO \"{{name}}\"; \
                            GRANT USAGE ON SCHEMA public TO \"{{name}}\"; \
                            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
        default_ttl="1h" \
        max_ttl="24h"
    
    # API service database role (more privileges)
    vault write database/roles/api-service-role \
        db_name=postgresql \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
                            GRANT CONNECT ON DATABASE apidb TO \"{{name}}\"; \
                            GRANT USAGE ON SCHEMA public TO \"{{name}}\"; \
                            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; \
                            GRANT CREATE ON SCHEMA public TO \"{{name}}\";" \
        default_ttl="30m" \
        max_ttl="4h"
    
    # MySQL connection for legacy apps
    vault write database/config/mysql \
        plugin_name=mysql-database-plugin \
        connection_url="{{username}}:{{password}}@tcp(mysql.production.svc.cluster.local:3306)/" \
        allowed_roles="legacy-app-role" \
        username="vault" \
        password="$MYSQL_VAULT_PASSWORD"
    
    vault write database/roles/legacy-app-role \
        db_name=mysql \
        creation_statements="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}'; GRANT SELECT, INSERT, UPDATE, DELETE ON legacy_db.* TO '{{name}}'@'%';" \
        default_ttl="2h" \
        max_ttl="8h"
    
    log_success "Database secrets engine configured"
}

main() {
    case "${1:-all}" in
        "app-policies")
            create_app_policies
            ;;
        "human-policies")
            create_human_policies
            ;;
        "k8s-roles")
            configure_k8s_roles
            ;;
        "ldap-groups")
            configure_ldap_groups
            ;;
        "database")
            configure_database_engine
            ;;
        "all")
            create_app_policies
            create_human_policies
            configure_k8s_roles
            configure_ldap_groups
            configure_database_engine
            ;;
        *)
            echo "Usage: $0 {app-policies|human-policies|k8s-roles|ldap-groups|database|all}"
            exit 1
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Kubernetes Secret Management

#### Sealed Secrets Implementation
```yaml
# sealed-secrets/controller.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sealed-secrets-system
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sealed-secrets-controller
  namespace: sealed-secrets-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sealed-secrets-controller
  template:
    metadata:
      labels:
        app: sealed-secrets-controller
    spec:
      serviceAccountName: sealed-secrets-controller
      containers:
      - name: sealed-secrets-controller
        image: quay.io/bitnami/sealed-secrets-controller:v0.24.0
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 8081
          name: metrics
        env:
        - name: SEALED_SECRETS_UPDATE_STATUS
          value: "true"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
        livenessProbe:
          httpGet:
            path: /healthz
            port: http
        readinessProbe:
          httpGet:
            path: /healthz
            port: http
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sealed-secrets-controller
  namespace: sealed-secrets-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: sealed-secrets-controller
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "create", "update", "delete", "watch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create", "patch"]
- apiGroups: ["bitnami.com"]
  resources: ["sealedsecrets"]
  verbs: ["get", "list", "watch", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: sealed-secrets-controller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: sealed-secrets-controller
subjects:
- kind: ServiceAccount
  name: sealed-secrets-controller
  namespace: sealed-secrets-system
```

#### External Secrets Operator
```yaml
# external-secrets/installation.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: external-secrets-system
---
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.vault.svc.cluster.local:8200"
      path: "app-secrets"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
          serviceAccountRef:
            name: "external-secrets"
            namespace: "external-secrets-system"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: web-app-secrets
  namespace: production
spec:
  refreshInterval: 300s  # 5 minutes
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: web-app-secrets
    creationPolicy: Owner
    template:
      type: Opaque
      metadata:
        annotations:
          reloader.stakater.com/match: "true"
      data:
        database_url: "postgresql://{{ .username }}:{{ .password }}@postgres.production.svc.cluster.local:5432/webapp"
        redis_url: "redis://{{ .redis_password }}@redis.production.svc.cluster.local:6379"
  data:
  - secretKey: username
    remoteRef:
      key: web-app/database
      property: username
  - secretKey: password
    remoteRef:
      key: web-app/database
      property: password
  - secretKey: redis_password
    remoteRef:
      key: web-app/redis
      property: password
---
# Database credential rotation
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: api-service-db-creds
  namespace: production
spec:
  refreshInterval: 1800s  # 30 minutes - for dynamic credentials
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: api-service-db-creds
    creationPolicy: Owner
  data:
  - secretKey: username
    remoteRef:
      key: database/creds/api-service-role
      property: username
  - secretKey: password
    remoteRef:
      key: database/creds/api-service-role
      property: password
```

This provides comprehensive production secrets management with Vault integration, proper policies, and Kubernetes secret management patterns.