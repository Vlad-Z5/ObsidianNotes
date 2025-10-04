## OAuth2/OIDC Authentication

### Keycloak Integration

```yaml
# grafana.ini
[auth.generic_oauth]
enabled = true
name = Keycloak
allow_sign_up = true
client_id = grafana
client_secret = ${GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET}
scopes = openid profile email groups
auth_url = https://keycloak.example.com/auth/realms/master/protocol/openid-connect/auth
token_url = https://keycloak.example.com/auth/realms/master/protocol/openid-connect/token
api_url = https://keycloak.example.com/auth/realms/master/protocol/openid-connect/userinfo
role_attribute_path = contains(groups[*], 'grafana-admin') && 'Admin' || contains(groups[*], 'grafana-editor') && 'Editor' || 'Viewer'
role_attribute_strict = false
allow_assign_grafana_admin = true
```

### Google OAuth

```yaml
# grafana.ini
[auth.google]
enabled = true
client_id = ${GF_AUTH_GOOGLE_CLIENT_ID}
client_secret = ${GF_AUTH_GOOGLE_CLIENT_SECRET}
scopes = https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email
auth_url = https://accounts.google.com/o/oauth2/auth
token_url = https://oauth2.googleapis.com/token
api_url = https://www.googleapis.com/oauth2/v1/userinfo
allowed_domains = example.com
allow_sign_up = true
```

### Azure AD OAuth

```yaml
# grafana.ini
[auth.azuread]
enabled = true
name = Azure AD
allow_sign_up = true
client_id = ${GF_AUTH_AZUREAD_CLIENT_ID}
client_secret = ${GF_AUTH_AZUREAD_CLIENT_SECRET}
scopes = openid email profile
auth_url = https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/authorize
token_url = https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token
allowed_groups = ${GF_AUTH_AZUREAD_ALLOWED_GROUPS}
allowed_domains =
role_attribute_strict = false
allow_assign_grafana_admin = false
```

### GitHub OAuth

```yaml
# grafana.ini
[auth.github]
enabled = true
allow_sign_up = true
client_id = ${GF_AUTH_GITHUB_CLIENT_ID}
client_secret = ${GF_AUTH_GITHUB_CLIENT_SECRET}
scopes = user:email,read:org
auth_url = https://github.com/login/oauth/authorize
token_url = https://github.com/login/oauth/access_token
api_url = https://api.github.com/user
allowed_organizations = example-org
team_ids =
allow_assign_grafana_admin = false
```

### Okta OIDC

```yaml
# grafana.ini
[auth.generic_oauth]
enabled = true
name = Okta
allow_sign_up = true
client_id = ${GF_AUTH_OKTA_CLIENT_ID}
client_secret = ${GF_AUTH_OKTA_CLIENT_SECRET}
scopes = openid profile email groups
auth_url = https://example.okta.com/oauth2/default/v1/authorize
token_url = https://example.okta.com/oauth2/default/v1/token
api_url = https://example.okta.com/oauth2/default/v1/userinfo
role_attribute_path = contains(groups[*], 'GrafanaAdmins') && 'Admin' || contains(groups[*], 'GrafanaEditors') && 'Editor' || 'Viewer'
```

## LDAP/Active Directory Authentication

### Basic LDAP Configuration

```toml
# /etc/grafana/ldap.toml
[[servers]]
host = "ldap.example.com"
port = 389
use_ssl = false
start_tls = true
ssl_skip_verify = false
bind_dn = "cn=admin,dc=example,dc=com"
bind_password = '${LDAP_BIND_PASSWORD}'
search_filter = "(cn=%s)"
search_base_dns = ["dc=example,dc=com"]

[servers.attributes]
name = "givenName"
surname = "sn"
username = "cn"
member_of = "memberOf"
email = "email"

[[servers.group_mappings]]
group_dn = "cn=admins,ou=groups,dc=example,dc=com"
org_role = "Admin"
grafana_admin = true

[[servers.group_mappings]]
group_dn = "cn=editors,ou=groups,dc=example,dc=com"
org_role = "Editor"

[[servers.group_mappings]]
group_dn = "cn=viewers,ou=groups,dc=example,dc=com"
org_role = "Viewer"
```

### Advanced LDAP with Multiple Servers

```toml
# /etc/grafana/ldap.toml
verbose_logging = true

[[servers]]
host = "ldap-primary.example.com"
port = 636
use_ssl = true
start_tls = false
ssl_skip_verify = false
root_ca_cert = "/etc/grafana/ssl/ca.crt"
client_cert = "/etc/grafana/ssl/client.crt"
client_key = "/etc/grafana/ssl/client.key"

bind_dn = "cn=grafana-svc,ou=service-accounts,dc=example,dc=com"
bind_password = '${LDAP_BIND_PASSWORD}'

timeout = 10
search_filter = "(uid=%s)"
search_base_dns = ["ou=users,dc=example,dc=com"]

[servers.attributes]
name = "givenName"
surname = "sn"
username = "uid"
member_of = "memberOf"
email = "mail"

[[servers.group_mappings]]
group_dn = "cn=grafana-superadmins,ou=groups,dc=example,dc=com"
org_role = "Admin"
grafana_admin = true
org_id = 1

[[servers.group_mappings]]
group_dn = "cn=grafana-devops,ou=groups,dc=example,dc=com"
org_role = "Editor"
org_id = 1

[[servers.group_mappings]]
group_dn = "cn=grafana-developers,ou=groups,dc=example,dc=com"
org_role = "Editor"
org_id = 2

[[servers.group_mappings]]
group_dn = "*"
org_role = "Viewer"

# Fallback LDAP server
[[servers]]
host = "ldap-secondary.example.com"
port = 636
use_ssl = true
bind_dn = "cn=grafana-svc,ou=service-accounts,dc=example,dc=com"
bind_password = '${LDAP_BIND_PASSWORD_SECONDARY}'
search_filter = "(uid=%s)"
search_base_dns = ["ou=users,dc=example,dc=com"]
```

### LDAP Configuration in grafana.ini

```ini
[auth.ldap]
enabled = true
config_file = /etc/grafana/ldap.toml
allow_sign_up = true
sync_cron = "0 0 1 * * *"
active_sync_enabled = true
```

## SAML Authentication

### SAML Configuration

```ini
[auth.saml]
enabled = true
certificate_path = /etc/grafana/saml/cert.pem
private_key_path = /etc/grafana/saml/key.pem
signature_algorithm = rsa-sha256
idp_metadata_url = https://idp.example.com/metadata
idp_metadata_path = /etc/grafana/saml/metadata.xml
max_issue_delay = 90s
metadata_valid_duration = 48h
assertion_attribute_name = displayName
assertion_attribute_login = email
assertion_attribute_email = email
assertion_attribute_groups = groups
assertion_attribute_role = role
assertion_attribute_org = org
allowed_organizations =
org_mapping =
role_values_admin = Admin
role_values_editor = Editor
role_values_viewer = Viewer
role_values_grafana_admin = GrafanaAdmin
allow_sign_up = true
allow_idp_initiated = false
name_id_format = urn:oasis:names:tc:SAML:2.0:nameid-format:persistent
```

### SAML with Azure AD

```ini
[auth.saml]
enabled = true
certificate_path = /etc/grafana/saml/azure-ad.crt
private_key_path = /etc/grafana/saml/azure-ad.key
idp_metadata_url = https://login.microsoftonline.com/${TENANT_ID}/federationmetadata/2007-06/federationmetadata.xml
assertion_attribute_name = http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name
assertion_attribute_login = http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress
assertion_attribute_email = http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress
assertion_attribute_groups = http://schemas.microsoft.com/ws/2008/06/identity/claims/groups
assertion_attribute_role = http://schemas.microsoft.com/ws/2008/06/identity/claims/role
role_values_admin = grafana-admin
role_values_editor = grafana-editor
allow_sign_up = true
```

## API Key Management

### Creating API Keys via UI

```bash
# Via Grafana UI:
# 1. Configuration → API Keys
# 2. Click "New API Key"
# 3. Set name, role (Admin/Editor/Viewer), time to live
# 4. Copy key immediately (shown only once)
```

### Creating API Keys via API

```bash
# Create API key
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{
    "name": "deployment-key",
    "role": "Admin",
    "secondsToLive": 86400
  }' \
  https://grafana.example.com/api/auth/keys

# List API keys
curl -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  https://grafana.example.com/api/auth/keys

# Delete API key
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  https://grafana.example.com/api/auth/keys/1
```

### Service Account Tokens (Preferred)

```bash
# Create service account
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{
    "name": "monitoring-automation",
    "role": "Editor",
    "isDisabled": false
  }' \
  https://grafana.example.com/api/serviceaccounts

# Create service account token
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{
    "name": "automation-token",
    "role": "Editor",
    "secondsToLive": 0
  }' \
  https://grafana.example.com/api/serviceaccounts/1/tokens

# List service account tokens
curl -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  https://grafana.example.com/api/serviceaccounts/1/tokens

# Delete service account token
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  https://grafana.example.com/api/serviceaccounts/1/tokens/1
```

### API Key Rotation Script

```bash
#!/bin/bash
# rotate-grafana-api-keys.sh

GRAFANA_URL="https://grafana.example.com"
ADMIN_TOKEN="${GRAFANA_ADMIN_TOKEN}"
MAX_KEY_AGE_DAYS=90

# Get all API keys
keys=$(curl -s -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  "${GRAFANA_URL}/api/auth/keys")

# Parse and check age
echo "${keys}" | jq -r '.[] | select(.created < (now - (86400 * '"${MAX_KEY_AGE_DAYS}"'))) | .id' | while read key_id; do
  echo "Deleting old API key: ${key_id}"
  curl -X DELETE \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    "${GRAFANA_URL}/api/auth/keys/${key_id}"
done
```

## User Roles and Permissions

### Organization Roles

```yaml
# Viewer
- View dashboards
- Cannot edit or create

# Editor
- View dashboards
- Create and edit dashboards
- Create and edit data sources
- Cannot modify organization settings

# Admin
- All Editor permissions
- Manage users and teams
- Manage organization settings
- Manage API keys
```

### Folder Permissions

```bash
# Set folder permissions
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{
    "items": [
      {
        "role": "Viewer",
        "permission": 1
      },
      {
        "role": "Editor",
        "permission": 2
      },
      {
        "teamId": 1,
        "permission": 2
      },
      {
        "userId": 10,
        "permission": 4
      }
    ]
  }' \
  https://grafana.example.com/api/folders/uid/permissions
```

### Dashboard Permissions

```bash
# Get dashboard permissions
curl -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid/permissions

# Update dashboard permissions
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{
    "items": [
      {
        "role": "Viewer",
        "permission": 1
      },
      {
        "teamId": 2,
        "permission": 2
      },
      {
        "userId": 5,
        "permission": 4
      }
    ]
  }' \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid/permissions
```

### Team Management

```bash
# Create team
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{
    "name": "DevOps Team",
    "email": "devops@example.com"
  }' \
  https://grafana.example.com/api/teams

# Add user to team
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{
    "userId": 10
  }' \
  https://grafana.example.com/api/teams/1/members

# Assign team permissions
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{
    "permission": 2
  }' \
  https://grafana.example.com/api/teams/1/members/10
```

## Network Security

### TLS Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-config
  namespace: monitoring
data:
  grafana.ini: |
    [server]
    protocol = https
    http_port = 3000
    domain = grafana.example.com
    root_url = https://grafana.example.com
    cert_file = /etc/grafana/ssl/tls.crt
    cert_key = /etc/grafana/ssl/tls.key

    [security]
    admin_user = admin
    admin_password = ${GF_SECURITY_ADMIN_PASSWORD}
    secret_key = ${GF_SECURITY_SECRET_KEY}
    disable_gravatar = true
    cookie_secure = true
    cookie_samesite = strict
    strict_transport_security = true
    strict_transport_security_max_age_seconds = 31536000
    strict_transport_security_preload = true
    strict_transport_security_subdomains = true
    x_content_type_options = true
    x_xss_protection = true
    content_security_policy = true
```

### Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana
  namespace: monitoring
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - grafana.example.com
    secretName: grafana-tls
  rules:
  - host: grafana.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: grafana
            port:
              number: 3000
```

### NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: grafana
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: grafana
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 3000
  egress:
  # Allow DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
  # Allow Prometheus
  - to:
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 9090
  # Allow Loki
  - to:
    - podSelector:
        matchLabels:
          app: loki
    ports:
    - protocol: TCP
      port: 3100
  # Allow Tempo
  - to:
    - podSelector:
        matchLabels:
          app: tempo
    ports:
    - protocol: TCP
      port: 3200
  # Allow LDAP
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 389
    - protocol: TCP
      port: 636
  # Allow external OAuth/OIDC providers
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

## Kubernetes RBAC Integration

### ServiceAccount and RBAC

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: grafana
  namespace: monitoring
  labels:
    app: grafana
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: grafana
  labels:
    app: grafana
rules:
- apiGroups: [""]
  resources:
  - nodes
  - nodes/proxy
  - services
  - endpoints
  - pods
  - events
  - namespaces
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources:
  - deployments
  - daemonsets
  - statefulsets
  - replicasets
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources:
  - jobs
  - cronjobs
  verbs: ["get", "list", "watch"]
- nonResourceURLs:
  - /metrics
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: grafana
  labels:
    app: grafana
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: grafana
subjects:
- kind: ServiceAccount
  name: grafana
  namespace: monitoring
```

### Grafana Deployment with ServiceAccount

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      serviceAccountName: grafana
      securityContext:
        runAsNonRoot: true
        runAsUser: 472
        fsGroup: 472
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: grafana
        image: grafana/grafana:10.2.3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        ports:
        - containerPort: 3000
          name: http
          protocol: TCP
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-admin-secret
              key: password
        - name: GF_SECURITY_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: grafana-secret-key
              key: secret_key
        - name: GF_INSTALL_PLUGINS
          value: ""
        volumeMounts:
        - name: config
          mountPath: /etc/grafana
        - name: storage
          mountPath: /var/lib/grafana
        - name: tmp
          mountPath: /tmp
        - name: dashboards
          mountPath: /etc/grafana/provisioning/dashboards
        - name: datasources
          mountPath: /etc/grafana/provisioning/datasources
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
      volumes:
      - name: config
        configMap:
          name: grafana-config
      - name: storage
        persistentVolumeClaim:
          claimName: grafana-pvc
      - name: tmp
        emptyDir: {}
      - name: dashboards
        configMap:
          name: grafana-dashboards
      - name: datasources
        configMap:
          name: grafana-datasources
```

## Secrets Management

### External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: monitoring
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "grafana"
          serviceAccountRef:
            name: grafana
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: grafana-secrets
  namespace: monitoring
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: grafana-admin-secret
    creationPolicy: Owner
  data:
  - secretKey: password
    remoteRef:
      key: grafana/admin
      property: password
  - secretKey: secret_key
    remoteRef:
      key: grafana/encryption
      property: secret_key
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: grafana-oauth-secrets
  namespace: monitoring
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: grafana-oauth
    creationPolicy: Owner
  data:
  - secretKey: client_id
    remoteRef:
      key: grafana/oauth
      property: client_id
  - secretKey: client_secret
    remoteRef:
      key: grafana/oauth
      property: client_secret
```

### Sealed Secrets

```bash
# Install kubeseal
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-0.24.0-linux-amd64.tar.gz
tar xfz kubeseal-0.24.0-linux-amd64.tar.gz
sudo install -m 755 kubeseal /usr/local/bin/kubeseal

# Create sealed secret
kubectl create secret generic grafana-admin-secret \
  --from-literal=password='super-secret-password' \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > grafana-admin-sealed-secret.yaml

# Apply sealed secret
kubectl apply -f grafana-admin-sealed-secret.yaml
```

### HashiCorp Vault Integration

```ini
[database]
type = postgres
host = postgres.example.com:5432
name = grafana
user = grafana
password = ${VAULT:secret/data/grafana/db#password}

[auth.generic_oauth]
client_id = ${VAULT:secret/data/grafana/oauth#client_id}
client_secret = ${VAULT:secret/data/grafana/oauth#client_secret}
```

## Security Hardening

### grafana.ini Security Settings

```ini
[security]
# Admin credentials
admin_user = admin
admin_password = ${GF_SECURITY_ADMIN_PASSWORD}
secret_key = ${GF_SECURITY_SECRET_KEY}

# Disable user signup
disable_initial_admin_creation = false
allow_embedding = false
cookie_secure = true
cookie_samesite = strict
login_cookie_name = grafana_session
login_maximum_inactive_lifetime_duration = 1h
login_maximum_lifetime_duration = 24h

# Security headers
strict_transport_security = true
strict_transport_security_max_age_seconds = 31536000
strict_transport_security_preload = true
strict_transport_security_subdomains = true
x_content_type_options = true
x_xss_protection = true
content_security_policy = true
content_security_policy_template = """script-src 'self' 'unsafe-eval' 'unsafe-inline' 'strict-dynamic' $NONCE;object-src 'none';font-src 'self';style-src 'self' 'unsafe-inline' blob:;img-src * data:;base-uri 'self';connect-src 'self' grafana.com ws://$ROOT_PATH wss://$ROOT_PATH;manifest-src 'self';media-src 'none';form-action 'self';"""

# Disable features
disable_gravatar = true
data_proxy_logging = false
data_proxy_timeout = 30
data_proxy_keep_alive_seconds = 30

# Password policy
password_min_length = 16
password_max_length = 256

[auth]
disable_login_form = false
disable_signout_menu = false
oauth_auto_login = false
oauth_allow_insecure_email_lookup = false
signout_redirect_url =
login_maximum_inactive_lifetime_days = 1
login_maximum_lifetime_days = 7
token_rotation_interval_minutes = 10
```

### Pod Security Policy

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: grafana-psp
  annotations:
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: 'runtime/default'
    apparmor.security.beta.kubernetes.io/allowedProfileNames: 'runtime/default'
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: grafana-psp
  namespace: monitoring
rules:
- apiGroups: ['policy']
  resources: ['podsecuritypolicies']
  verbs: ['use']
  resourceNames:
  - grafana-psp
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: grafana-psp
  namespace: monitoring
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: grafana-psp
subjects:
- kind: ServiceAccount
  name: grafana
  namespace: monitoring
```

## Audit Logging

### Enable Audit Logging

```ini
[log]
mode = console file
level = info
filters = oauth:debug

[log.console]
level = info
format = json

[audit]
enabled = true
logger = file
log_dashboard_content = true

[auditing]
enabled = true
verbosity = 1
max_age_days = 30
```

### Audit Log Analysis Script

```bash
#!/bin/bash
# analyze-grafana-audit.sh

AUDIT_LOG="/var/log/grafana/audit.log"
DAYS=${1:-7}

echo "=== Failed Login Attempts (last ${DAYS} days) ==="
jq -r 'select(.action == "login" and .result == "failure") | "\(.timestamp) \(.user) from \(.ip)"' \
  <(tail -n 10000 "${AUDIT_LOG}") | \
  grep -A "${DAYS}" "$(date -d "${DAYS} days ago" +%Y-%m-%d)" | \
  sort | uniq -c | sort -rn | head -20

echo ""
echo "=== Dashboard Modifications ==="
jq -r 'select(.action | contains("dashboard")) | "\(.timestamp) \(.action) \(.dashboard) by \(.user)"' \
  <(tail -n 10000 "${AUDIT_LOG}") | \
  grep -A "${DAYS}" "$(date -d "${DAYS} days ago" +%Y-%m-%d)" | head -20

echo ""
echo "=== Data Source Changes ==="
jq -r 'select(.action | contains("datasource")) | "\(.timestamp) \(.action) \(.datasource) by \(.user)"' \
  <(tail -n 10000 "${AUDIT_LOG}") | \
  grep -A "${DAYS}" "$(date -d "${DAYS} days ago" +%Y-%m-%d)" | head -20

echo ""
echo "=== API Key Usage ==="
jq -r 'select(.authType == "api_key") | "\(.timestamp) \(.action) by key:\(.keyName)"' \
  <(tail -n 10000 "${AUDIT_LOG}") | \
  grep -A "${DAYS}" "$(date -d "${DAYS} days ago" +%Y-%m-%d)" | \
  awk '{print $4}' | sort | uniq -c | sort -rn | head -10
```

## Compliance and Best Practices

### GDPR Compliance

```ini
[analytics]
reporting_enabled = false
check_for_updates = false
google_analytics_ua_id =

[security]
disable_gravatar = true

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_role = Viewer
viewers_can_edit = false
editors_can_admin = false

[auth.anonymous]
enabled = false

[snapshots]
external_enabled = false
```

### CIS Kubernetes Benchmark

```yaml
# Grafana deployment following CIS benchmarks
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  template:
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 472
        fsGroup: 472
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: grafana
        image: grafana/grafana:10.2.3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 472
          capabilities:
            drop:
            - ALL
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
```

### Security Checklist

```markdown
## Pre-Production Security Checklist

- [ ] Change default admin password
- [ ] Enable and configure OAuth/OIDC authentication
- [ ] Disable anonymous access
- [ ] Enable TLS/HTTPS
- [ ] Configure strict security headers
- [ ] Implement NetworkPolicies
- [ ] Use read-only root filesystem
- [ ] Run as non-root user (UID 472)
- [ ] Drop ALL capabilities
- [ ] Enable audit logging
- [ ] Configure backup for dashboards and datasources
- [ ] Set up API key rotation policy
- [ ] Configure password policy (min 16 characters)
- [ ] Disable user signup
- [ ] Enable cookie security (secure, samesite)
- [ ] Configure session timeout (1h inactive, 24h max)
- [ ] Use External Secrets Operator or Sealed Secrets
- [ ] Implement RBAC with least privilege
- [ ] Configure resource limits
- [ ] Enable Pod Security Standards
- [ ] Disable external snapshots
- [ ] Disable Gravatar
- [ ] Disable analytics and update checks
- [ ] Configure CORS if needed
- [ ] Set up monitoring for failed logins
- [ ] Document incident response procedures
- [ ] Regular security updates
```
