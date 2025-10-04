## Deployment Procedures

### Initial Deployment

```bash
#!/bin/bash
# deploy-grafana.sh

set -e

NAMESPACE="monitoring"
GRAFANA_VERSION="10.2.3"

echo "=== Deploying Grafana ${GRAFANA_VERSION} ==="

# Create namespace
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
kubectl create secret generic grafana-admin-secret \
  --from-literal=password="$(openssl rand -base64 32)" \
  --namespace=${NAMESPACE} \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic grafana-secret-key \
  --from-literal=secret_key="$(openssl rand -base64 32)" \
  --namespace=${NAMESPACE} \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations
kubectl apply -f grafana-configmap.yaml
kubectl apply -f grafana-pvc.yaml
kubectl apply -f grafana-deployment.yaml
kubectl apply -f grafana-service.yaml
kubectl apply -f grafana-ingress.yaml

# Wait for deployment
echo "Waiting for Grafana to be ready..."
kubectl rollout status deployment/grafana -n ${NAMESPACE} --timeout=5m

# Get admin password
ADMIN_PASSWORD=$(kubectl get secret grafana-admin-secret -n ${NAMESPACE} -o jsonpath='{.data.password}' | base64 -d)

echo ""
echo "=== Deployment Complete ==="
echo "Grafana URL: https://grafana.example.com"
echo "Username: admin"
echo "Password: ${ADMIN_PASSWORD}"
```

### Pre-Deployment Checklist

```markdown
## Pre-Deployment Checklist

### Infrastructure
- [ ] Kubernetes cluster available and healthy
- [ ] Namespace created
- [ ] Storage class available
- [ ] DNS configured for grafana.example.com
- [ ] TLS certificate available

### Database
- [ ] PostgreSQL/MySQL instance provisioned
- [ ] Database created
- [ ] Database user created with appropriate permissions
- [ ] Database credentials stored in secrets
- [ ] Database connection tested
- [ ] Database backup configured

### Dependencies
- [ ] Data sources available (Prometheus, Loki, Tempo)
- [ ] Redis available for caching (if using)
- [ ] Image renderer deployed (if using)
- [ ] Load balancer configured

### Security
- [ ] Admin password generated and stored securely
- [ ] Secret key generated and stored securely
- [ ] OAuth/OIDC configured (if using)
- [ ] LDAP configured (if using)
- [ ] NetworkPolicies reviewed
- [ ] RBAC configured
- [ ] TLS certificates valid

### Monitoring
- [ ] ServiceMonitor created
- [ ] Alert rules configured
- [ ] Log aggregation configured
- [ ] Backup jobs scheduled
```

### Upgrade Procedure

```bash
#!/bin/bash
# upgrade-grafana.sh

set -e

NAMESPACE="monitoring"
CURRENT_VERSION="10.1.0"
TARGET_VERSION="10.2.3"

echo "=== Upgrading Grafana from ${CURRENT_VERSION} to ${TARGET_VERSION} ==="

# Pre-upgrade backup
echo "Creating backup..."
./backup-grafana.sh

# Check current version
RUNNING_VERSION=$(kubectl get deployment grafana -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)
echo "Current version: ${RUNNING_VERSION}"

if [ "${RUNNING_VERSION}" != "${CURRENT_VERSION}" ]; then
  echo "Warning: Running version ${RUNNING_VERSION} doesn't match expected ${CURRENT_VERSION}"
  read -p "Continue? (yes/no): " CONTINUE
  if [ "${CONTINUE}" != "yes" ]; then
    exit 1
  fi
fi

# Update image
echo "Updating image to ${TARGET_VERSION}..."
kubectl set image deployment/grafana grafana=grafana/grafana:${TARGET_VERSION} -n ${NAMESPACE}

# Wait for rollout
echo "Waiting for rollout..."
kubectl rollout status deployment/grafana -n ${NAMESPACE} --timeout=10m

# Verify upgrade
NEW_VERSION=$(kubectl get deployment grafana -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)
echo "New version: ${NEW_VERSION}"

# Health check
echo "Performing health check..."
kubectl exec -n ${NAMESPACE} deployment/grafana -- wget -O- http://localhost:3000/api/health

echo ""
echo "=== Upgrade Complete ==="
echo "Verify the upgrade at https://grafana.example.com"
```

### Rollback Procedure

```bash
#!/bin/bash
# rollback-grafana.sh

set -e

NAMESPACE="monitoring"

echo "=== Grafana Rollback ==="

# Show rollout history
echo "Rollout history:"
kubectl rollout history deployment/grafana -n ${NAMESPACE}

# Get previous revision
PREVIOUS_REVISION=$(kubectl rollout history deployment/grafana -n ${NAMESPACE} | tail -2 | head -1 | awk '{print $1}')

read -p "Rollback to revision ${PREVIOUS_REVISION}? (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
  echo "Rollback cancelled"
  exit 0
fi

# Perform rollback
echo "Rolling back to revision ${PREVIOUS_REVISION}..."
kubectl rollout undo deployment/grafana -n ${NAMESPACE} --to-revision=${PREVIOUS_REVISION}

# Wait for rollback
echo "Waiting for rollback to complete..."
kubectl rollout status deployment/grafana -n ${NAMESPACE} --timeout=5m

# Verify
CURRENT_VERSION=$(kubectl get deployment grafana -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].image}')
echo "Current version: ${CURRENT_VERSION}"

# Health check
kubectl exec -n ${NAMESPACE} deployment/grafana -- wget -O- http://localhost:3000/api/health

echo ""
echo "=== Rollback Complete ==="
```

## Backup and Restore

### Full Backup

```bash
#!/bin/bash
# backup-grafana-full.sh

set -e

NAMESPACE="monitoring"
BACKUP_DIR="./grafana-backup-$(date +%Y%m%d-%H%M%S)"
GRAFANA_URL="http://localhost:3000"
API_KEY="${GRAFANA_API_KEY}"

echo "=== Full Grafana Backup ==="
echo "Backup directory: ${BACKUP_DIR}"

mkdir -p "${BACKUP_DIR}"/{dashboards,datasources,folders,alerts,database}

# Port forward to Grafana
kubectl port-forward -n ${NAMESPACE} svc/grafana 3000:3000 &
PF_PID=$!
sleep 5

# Backup data sources
echo "Backing up data sources..."
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/datasources" \
  > "${BACKUP_DIR}/datasources/datasources.json"

# Backup folders
echo "Backing up folders..."
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/folders" \
  > "${BACKUP_DIR}/folders/folders.json"

# Backup dashboards
echo "Backing up dashboards..."
DASHBOARD_UIDS=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/search?type=dash-db" | jq -r '.[].uid')

for uid in ${DASHBOARD_UIDS}; do
  echo "  ${uid}"
  curl -s -H "Authorization: Bearer ${API_KEY}" \
    "${GRAFANA_URL}/api/dashboards/uid/${uid}" \
    > "${BACKUP_DIR}/dashboards/${uid}.json"
done

# Backup alert rules
echo "Backing up alert rules..."
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/ruler/grafana/api/v1/rules" \
  > "${BACKUP_DIR}/alerts/rules.json"

# Backup contact points
echo "Backing up contact points..."
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/v1/provisioning/contact-points" \
  > "${BACKUP_DIR}/alerts/contact-points.json"

# Backup notification policies
echo "Backing up notification policies..."
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/v1/provisioning/policies" \
  > "${BACKUP_DIR}/alerts/notification-policies.json"

# Stop port forward
kill ${PF_PID}

# Backup database
echo "Backing up database..."
POD=$(kubectl get pods -n ${NAMESPACE} -l app=grafana -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n ${NAMESPACE} ${POD} -- sh -c \
  "PGPASSWORD=\${GF_DATABASE_PASSWORD} pg_dump -h \${GF_DATABASE_HOST} -U \${GF_DATABASE_USER} \${GF_DATABASE_NAME}" \
  > "${BACKUP_DIR}/database/grafana.sql"

# Create archive
echo "Creating archive..."
tar czf "${BACKUP_DIR}.tar.gz" "${BACKUP_DIR}"

# Cleanup
rm -rf "${BACKUP_DIR}"

echo ""
echo "=== Backup Complete ==="
echo "Backup file: ${BACKUP_DIR}.tar.gz"
echo "Size: $(du -h ${BACKUP_DIR}.tar.gz | cut -f1)"
```

### Automated Backup CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: grafana-backup
  namespace: monitoring
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: grafana-backup
          containers:
          - name: backup
            image: alpine/k8s:1.28.0
            command:
            - /bin/sh
            - -c
            - |
              set -e

              apk add --no-cache curl jq postgresql-client

              BACKUP_DIR="/backup/grafana-$(date +%Y%m%d-%H%M%S)"
              mkdir -p ${BACKUP_DIR}/{dashboards,datasources,folders,alerts}

              # Use service account token
              TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)

              # Port forward and backup
              kubectl port-forward -n monitoring svc/grafana 3000:3000 &
              sleep 5

              # Backup resources
              curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
                http://localhost:3000/api/datasources > ${BACKUP_DIR}/datasources/datasources.json

              # ... more backup commands ...

              # Upload to S3
              tar czf ${BACKUP_DIR}.tar.gz ${BACKUP_DIR}
              aws s3 cp ${BACKUP_DIR}.tar.gz s3://backups/grafana/

              # Cleanup old backups (keep last 30 days)
              find /backup -name "grafana-*.tar.gz" -mtime +30 -delete
            env:
            - name: GRAFANA_API_KEY
              valueFrom:
                secretKeyRef:
                  name: grafana-backup-api-key
                  key: api-key
            volumeMounts:
            - name: backup
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: grafana-backup-pvc
```

### Restore from Backup

```bash
#!/bin/bash
# restore-grafana.sh

set -e

BACKUP_FILE="${1}"
NAMESPACE="monitoring"
GRAFANA_URL="http://localhost:3000"
API_KEY="${GRAFANA_API_KEY}"

if [ -z "${BACKUP_FILE}" ]; then
  echo "Usage: $0 <backup.tar.gz>"
  exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

echo "=== Restoring Grafana from ${BACKUP_FILE} ==="

# Extract backup
TEMP_DIR=$(mktemp -d)
tar xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"
BACKUP_DIR=$(ls -d ${TEMP_DIR}/grafana-*)

# Port forward to Grafana
kubectl port-forward -n ${NAMESPACE} svc/grafana 3000:3000 &
PF_PID=$!
sleep 5

# Restore data sources
echo "Restoring data sources..."
if [ -f "${BACKUP_DIR}/datasources/datasources.json" ]; then
  jq -c '.[]' "${BACKUP_DIR}/datasources/datasources.json" | while read ds; do
    echo "  $(echo ${ds} | jq -r '.name')"
    echo "${ds}" | curl -X POST \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${API_KEY}" \
      -d @- \
      "${GRAFANA_URL}/api/datasources" || true
  done
fi

# Restore folders
echo "Restoring folders..."
if [ -f "${BACKUP_DIR}/folders/folders.json" ]; then
  jq -c '.[]' "${BACKUP_DIR}/folders/folders.json" | while read folder; do
    echo "  $(echo ${folder} | jq -r '.title')"
    echo "${folder}" | curl -X POST \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${API_KEY}" \
      -d @- \
      "${GRAFANA_URL}/api/folders" || true
  done
fi

# Restore dashboards
echo "Restoring dashboards..."
for dash_file in "${BACKUP_DIR}"/dashboards/*.json; do
  if [ -f "${dash_file}" ]; then
    title=$(jq -r '.dashboard.title' "${dash_file}")
    echo "  ${title}"
    jq '{dashboard: .dashboard, overwrite: true, message: "Restored from backup"}' "${dash_file}" | \
      curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d @- \
        "${GRAFANA_URL}/api/dashboards/db" || true
  fi
done

# Stop port forward
kill ${PF_PID}

# Cleanup
rm -rf "${TEMP_DIR}"

echo ""
echo "=== Restore Complete ==="
```

## Incident Response

### High CPU Usage

```bash
#!/bin/bash
# troubleshoot-high-cpu.sh

NAMESPACE="monitoring"
POD=$(kubectl get pods -n ${NAMESPACE} -l app=grafana -o jsonpath='{.items[0].metadata.name}')

echo "=== Troubleshooting High CPU Usage ==="

# Check CPU usage
echo "Current CPU usage:"
kubectl top pod -n ${NAMESPACE} ${POD}

# Check metrics
echo ""
echo "Grafana metrics:"
kubectl exec -n ${NAMESPACE} ${POD} -- wget -qO- http://localhost:3000/metrics | grep -E "process_cpu|grafana_http_request"

# Check for expensive queries
echo ""
echo "Recent query durations:"
kubectl logs -n ${NAMESPACE} ${POD} --tail=1000 | grep -i "duration" | sort -t= -k2 -nr | head -20

# Check database connections
echo ""
echo "Database connections:"
kubectl logs -n ${NAMESPACE} ${POD} --tail=1000 | grep -i "database\|sql" | tail -20

# Recommendations
cat <<EOF

=== Recommendations ===
1. Check for dashboards with short refresh intervals
2. Review expensive queries using Query Inspector
3. Implement query caching if not already enabled
4. Consider scaling horizontally
5. Review data source timeout settings

EOF
```

### Database Connection Issues

```bash
#!/bin/bash
# troubleshoot-database.sh

NAMESPACE="monitoring"
POD=$(kubectl get pods -n ${NAMESPACE} -l app=grafana -o jsonpath='{.items[0].metadata.name}')

echo "=== Troubleshooting Database Connection ==="

# Get database config
echo "Database configuration:"
kubectl exec -n ${NAMESPACE} ${POD} -- sh -c 'echo "Host: ${GF_DATABASE_HOST}"'
kubectl exec -n ${NAMESPACE} ${POD} -- sh -c 'echo "Database: ${GF_DATABASE_NAME}"'
kubectl exec -n ${NAMESPACE} ${POD} -- sh -c 'echo "User: ${GF_DATABASE_USER}"'

# Test connection from pod
echo ""
echo "Testing database connection..."
kubectl exec -n ${NAMESPACE} ${POD} -- sh -c \
  'PGPASSWORD=${GF_DATABASE_PASSWORD} psql -h ${GF_DATABASE_HOST} -U ${GF_DATABASE_USER} -d ${GF_DATABASE_NAME} -c "SELECT version();"'

# Check Grafana logs for database errors
echo ""
echo "Recent database errors:"
kubectl logs -n ${NAMESPACE} ${POD} --tail=1000 | grep -i "database\|sql\|connection" | grep -i error | tail -20

# Check database pod
DB_POD=$(kubectl get pods -n ${NAMESPACE} -l app=postgresql -o jsonpath='{.items[0].metadata.name}')
if [ -n "${DB_POD}" ]; then
  echo ""
  echo "Database pod status:"
  kubectl get pod -n ${NAMESPACE} ${DB_POD}

  echo ""
  echo "Database logs:"
  kubectl logs -n ${NAMESPACE} ${DB_POD} --tail=20
fi
```

### Dashboard Loading Issues

```bash
#!/bin/bash
# troubleshoot-dashboard.sh

DASHBOARD_UID="${1}"

if [ -z "${DASHBOARD_UID}" ]; then
  echo "Usage: $0 <dashboard-uid>"
  exit 1
fi

echo "=== Troubleshooting Dashboard ${DASHBOARD_UID} ==="

# Get dashboard JSON
echo "Fetching dashboard..."
curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/dashboards/uid/${DASHBOARD_UID}" \
  > /tmp/dashboard.json

# Validate JSON
echo "Validating JSON..."
jq . /tmp/dashboard.json > /dev/null && echo "JSON is valid" || echo "JSON is invalid"

# Check panel count
PANEL_COUNT=$(jq '.dashboard.panels | length' /tmp/dashboard.json)
echo "Panel count: ${PANEL_COUNT}"

if [ ${PANEL_COUNT} -gt 20 ]; then
  echo "Warning: Dashboard has ${PANEL_COUNT} panels (recommended: < 20)"
fi

# Check refresh interval
REFRESH=$(jq -r '.dashboard.refresh' /tmp/dashboard.json)
echo "Refresh interval: ${REFRESH}"

# Check time range
TIME_FROM=$(jq -r '.dashboard.time.from' /tmp/dashboard.json)
TIME_TO=$(jq -r '.dashboard.time.to' /tmp/dashboard.json)
echo "Time range: ${TIME_FROM} to ${TIME_TO}"

# Check data source references
echo ""
echo "Data sources used:"
jq -r '.dashboard.panels[].datasource.uid' /tmp/dashboard.json 2>/dev/null | sort | uniq

# Test each data source
echo ""
echo "Testing data sources..."
for ds_uid in $(jq -r '.dashboard.panels[].datasource.uid' /tmp/dashboard.json 2>/dev/null | sort | uniq); do
  DS_ID=$(curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
    "https://grafana.example.com/api/datasources/uid/${ds_uid}" | jq -r '.id')

  if [ "${DS_ID}" != "null" ]; then
    STATUS=$(curl -s -X POST -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
      "https://grafana.example.com/api/datasources/${DS_ID}/health" | jq -r '.status')
    echo "  ${ds_uid}: ${STATUS}"
  fi
done

rm /tmp/dashboard.json
```

### Alert Not Firing

```bash
#!/bin/bash
# troubleshoot-alert.sh

ALERT_NAME="${1}"

if [ -z "${ALERT_NAME}" ]; then
  echo "Usage: $0 <alert-name>"
  exit 1
fi

echo "=== Troubleshooting Alert: ${ALERT_NAME} ==="

# Get alert rule
echo "Fetching alert rule..."
curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/ruler/grafana/api/v1/rules" \
  > /tmp/rules.json

# Find specific alert
jq --arg name "${ALERT_NAME}" \
  '.[] | .[] | .rules[] | select(.grafana_alert.title == $name)' \
  /tmp/rules.json > /tmp/alert.json

if [ ! -s /tmp/alert.json ]; then
  echo "Alert not found: ${ALERT_NAME}"
  exit 1
fi

# Show alert details
echo ""
echo "Alert condition:"
jq -r '.grafana_alert.condition' /tmp/alert.json

echo ""
echo "Evaluation interval:"
jq -r '.. | .interval? // empty' /tmp/rules.json | head -1

echo ""
echo "For duration:"
jq -r '.for' /tmp/alert.json

# Test alert query
echo ""
echo "Testing alert query..."
QUERY=$(jq '.grafana_alert.data[0].model' /tmp/alert.json)
echo "Query: ${QUERY}"

# Check alert state
echo ""
echo "Current alert state:"
curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/v1/rules" | \
  jq --arg name "${ALERT_NAME}" '.[] | .[] | .rules[] | select(.name == $name) | {state: .state, health: .health}'

# Check Grafana alerting logs
NAMESPACE="monitoring"
POD=$(kubectl get pods -n ${NAMESPACE} -l app=grafana -o jsonpath='{.items[0].metadata.name}')

echo ""
echo "Recent alerting logs:"
kubectl logs -n ${NAMESPACE} ${POD} --tail=1000 | grep -i alert | grep "${ALERT_NAME}" | tail -20

rm /tmp/rules.json /tmp/alert.json
```

## Maintenance Tasks

### Cleanup Old Dashboards

```bash
#!/bin/bash
# cleanup-old-dashboards.sh

DAYS_OLD=90
DRY_RUN=true

echo "=== Cleanup Old Dashboards ==="
echo "Removing dashboards not modified in ${DAYS_OLD} days"
echo "Dry run: ${DRY_RUN}"

# Get all dashboards
DASHBOARDS=$(curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/search?type=dash-db" | jq -r '.[] | @base64')

CUTOFF_DATE=$(date -d "${DAYS_OLD} days ago" +%s)

for dashboard in ${DASHBOARDS}; do
  _jq() {
    echo ${dashboard} | base64 --decode | jq -r ${1}
  }

  uid=$(_jq '.uid')
  title=$(_jq '.title')

  # Get dashboard details
  UPDATED=$(curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
    "https://grafana.example.com/api/dashboards/uid/${uid}" | \
    jq -r '.meta.updated')

  UPDATED_TIMESTAMP=$(date -d "${UPDATED}" +%s)

  if [ ${UPDATED_TIMESTAMP} -lt ${CUTOFF_DATE} ]; then
    echo "Would delete: ${title} (${uid}) - Last updated: ${UPDATED}"

    if [ "${DRY_RUN}" != "true" ]; then
      curl -X DELETE \
        -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
        "https://grafana.example.com/api/dashboards/uid/${uid}"
    fi
  fi
done
```

### Database Maintenance

```bash
#!/bin/bash
# database-maintenance.sh

NAMESPACE="monitoring"
DB_POD=$(kubectl get pods -n ${NAMESPACE} -l app=postgresql -o jsonpath='{.items[0].metadata.name}')

echo "=== Database Maintenance ==="

# Vacuum and analyze
echo "Running VACUUM ANALYZE..."
kubectl exec -n ${NAMESPACE} ${DB_POD} -- psql -U grafana grafana -c "VACUUM ANALYZE;"

# Reindex
echo "Reindexing database..."
kubectl exec -n ${NAMESPACE} ${DB_POD} -- psql -U grafana grafana -c "REINDEX DATABASE grafana;"

# Check table sizes
echo ""
echo "Table sizes:"
kubectl exec -n ${NAMESPACE} ${DB_POD} -- psql -U grafana grafana -c \
  "SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Clean up old annotations
echo ""
echo "Cleaning up old annotations (> 90 days)..."
kubectl exec -n ${NAMESPACE} ${DB_POD} -- psql -U grafana grafana -c \
  "DELETE FROM annotation WHERE epoch < EXTRACT(EPOCH FROM NOW() - INTERVAL '90 days') * 1000;"

# Clean up old dashboard versions (keep last 20)
echo ""
echo "Cleaning up old dashboard versions..."
kubectl exec -n ${NAMESPACE} ${DB_POD} -- psql -U grafana grafana -c \
  "DELETE FROM dashboard_version WHERE id NOT IN (
    SELECT id FROM (
      SELECT id, ROW_NUMBER() OVER (PARTITION BY dashboard_id ORDER BY version DESC) as rn
      FROM dashboard_version
    ) t WHERE rn <= 20
  );"

echo ""
echo "=== Maintenance Complete ==="
```

### Certificate Renewal

```bash
#!/bin/bash
# renew-certificate.sh

NAMESPACE="monitoring"

echo "=== Certificate Renewal ==="

# Check current certificate expiry
echo "Current certificate expiry:"
kubectl get certificate -n ${NAMESPACE} grafana-tls -o jsonpath='{.status.notAfter}'

# Force renewal
echo ""
echo "Forcing certificate renewal..."
kubectl delete certificaterequest -n ${NAMESPACE} -l cert-manager.io/certificate-name=grafana-tls

# Wait for new certificate
echo "Waiting for new certificate..."
kubectl wait --for=condition=Ready certificate/grafana-tls -n ${NAMESPACE} --timeout=5m

# Verify new certificate
echo ""
echo "New certificate expiry:"
kubectl get certificate -n ${NAMESPACE} grafana-tls -o jsonpath='{.status.notAfter}'

# Restart Grafana to pick up new certificate
echo ""
echo "Restarting Grafana..."
kubectl rollout restart deployment/grafana -n ${NAMESPACE}
kubectl rollout status deployment/grafana -n ${NAMESPACE} --timeout=5m

echo ""
echo "=== Certificate Renewal Complete ==="
```

### Performance Tuning

```bash
#!/bin/bash
# performance-tuning.sh

NAMESPACE="monitoring"

echo "=== Performance Tuning ==="

# Analyze query performance
echo "Analyzing query performance..."
kubectl logs -n ${NAMESPACE} deployment/grafana --tail=10000 | \
  grep "duration=" | \
  awk '{for(i=1;i<=NF;i++) if($i~/duration=/) print $i}' | \
  sort -t= -k2 -rn | \
  head -20

# Check for high cardinality
echo ""
echo "Checking for high cardinality queries..."
kubectl logs -n ${NAMESPACE} deployment/grafana --tail=10000 | \
  grep -i "cardinality" | \
  tail -20

# Resource recommendations
echo ""
echo "Current resource usage:"
kubectl top pod -n ${NAMESPACE} -l app=grafana

echo ""
echo "=== Recommendations ==="
cat <<EOF
1. Review queries with duration > 1s
2. Implement query caching for expensive queries
3. Use recording rules for frequently accessed data
4. Adjust HPA thresholds if needed
5. Consider adding more replicas if CPU > 70%
6. Review dashboard refresh intervals
EOF
```

## Monitoring and Health Checks

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"
NAMESPACE="monitoring"

echo "=== Grafana Health Check ==="

# Basic health
echo "1. Basic health check..."
HEALTH=$(curl -s "${GRAFANA_URL}/api/health" | jq -r '.database')
echo "   Database: ${HEALTH}"

# API health
echo "2. API health check..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/org")
echo "   API Status: ${API_STATUS}"

# Data source health
echo "3. Data source health..."
DS_COUNT=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/datasources" | jq 'length')
echo "   Total data sources: ${DS_COUNT}"

curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/datasources" | \
  jq -r '.[].id' | while read ds_id; do
  DS_NAME=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
    "${GRAFANA_URL}/api/datasources/${ds_id}" | jq -r '.name')
  DS_STATUS=$(curl -s -X POST -H "Authorization: Bearer ${API_KEY}" \
    "${GRAFANA_URL}/api/datasources/${ds_id}/health" | jq -r '.status')
  echo "   ${DS_NAME}: ${DS_STATUS}"
done

# Pod health
echo "4. Pod health..."
kubectl get pods -n ${NAMESPACE} -l app=grafana

# Resource usage
echo "5. Resource usage..."
kubectl top pod -n ${NAMESPACE} -l app=grafana

echo ""
echo "=== Health Check Complete ==="
```
