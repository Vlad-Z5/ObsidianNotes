## API Authentication

### API Key Authentication

```bash
# Using API key in header
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/dashboards/home

# Using API key in query parameter (legacy)
curl "https://grafana.example.com/api/dashboards/home?api_key=${GRAFANA_API_KEY}"
```

### Basic Auth

```bash
# Using admin credentials
curl -u admin:password \
  https://grafana.example.com/api/dashboards/home

# With environment variables
curl -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  https://grafana.example.com/api/dashboards/home
```

### Service Account Token

```bash
# Create service account
SA_ID=$(curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{"name": "api-automation", "role": "Editor"}' \
  https://grafana.example.com/api/serviceaccounts | jq -r '.id')

# Create token for service account
TOKEN=$(curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -d '{"name": "automation-token"}' \
  "https://grafana.example.com/api/serviceaccounts/${SA_ID}/tokens" | jq -r '.key')

# Use service account token
curl -H "Authorization: Bearer ${TOKEN}" \
  https://grafana.example.com/api/dashboards/home
```

## Dashboard Management

### Get Dashboard by UID

```bash
# Get dashboard JSON
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid

# Get dashboard with metadata
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid | jq '.'
```

### Create Dashboard

```bash
# Create new dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d @- https://grafana.example.com/api/dashboards/db <<EOF
{
  "dashboard": {
    "id": null,
    "uid": null,
    "title": "Production Metrics",
    "tags": ["production", "metrics"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "CPU Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])",
            "refId": "A"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      }
    ]
  },
  "folderId": 0,
  "folderUid": null,
  "message": "Created via API",
  "overwrite": false
}
EOF
```

### Update Dashboard

```bash
# Update existing dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d @dashboard.json \
  https://grafana.example.com/api/dashboards/db

# Update with overwrite
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "dashboard": {...},
    "overwrite": true,
    "message": "Updated via API"
  }' \
  https://grafana.example.com/api/dashboards/db
```

### Delete Dashboard

```bash
# Delete by UID
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid

# Delete by slug (legacy)
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/dashboards/db/dashboard-slug
```

### Search Dashboards

```bash
# Search all dashboards
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/search?type=dash-db

# Search with query
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/search?query=production&type=dash-db"

# Search by tags
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/search?tag=kubernetes&tag=monitoring"

# Search in folder
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/search?folderIds=1&type=dash-db"

# Get starred dashboards
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/search?starred=true"
```

### Dashboard Versions

```bash
# Get dashboard versions
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid/versions

# Get specific version
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid/versions/5

# Compare versions
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/dashboards/uid/dashboard-uid/compare/1...5"

# Restore version
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"version": 5}' \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid/restore
```

### Export/Import Dashboards

```bash
#!/bin/bash
# export-dashboards.sh

GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"
OUTPUT_DIR="./dashboards"

mkdir -p "${OUTPUT_DIR}"

# Get all dashboard UIDs
DASHBOARDS=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/search?type=dash-db" | jq -r '.[].uid')

# Export each dashboard
for uid in ${DASHBOARDS}; do
  echo "Exporting dashboard: ${uid}"
  curl -s -H "Authorization: Bearer ${API_KEY}" \
    "${GRAFANA_URL}/api/dashboards/uid/${uid}" | \
    jq '.dashboard' > "${OUTPUT_DIR}/${uid}.json"
done

echo "Exported $(ls -1 ${OUTPUT_DIR} | wc -l) dashboards"
```

```bash
#!/bin/bash
# import-dashboards.sh

GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"
INPUT_DIR="./dashboards"

for file in "${INPUT_DIR}"/*.json; do
  echo "Importing: $(basename ${file})"

  # Create import payload
  jq -n \
    --slurpfile dashboard "${file}" \
    '{dashboard: $dashboard[0], overwrite: true, message: "Imported via API"}' | \
  curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d @- \
    "${GRAFANA_URL}/api/dashboards/db"
done
```

## Folder Management

### Create Folder

```bash
# Create folder
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "uid": "production-folder",
    "title": "Production Dashboards"
  }' \
  https://grafana.example.com/api/folders
```

### Get Folders

```bash
# Get all folders
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/folders

# Get folder by UID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/folders/production-folder

# Get folder by ID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/folders/id/1
```

### Update Folder

```bash
# Update folder
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "title": "Production Dashboards (Updated)",
    "version": 1
  }' \
  https://grafana.example.com/api/folders/production-folder
```

### Delete Folder

```bash
# Delete folder
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/folders/production-folder
```

### Folder Permissions

```bash
# Get folder permissions
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/folders/production-folder/permissions

# Update folder permissions
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "items": [
      {"role": "Viewer", "permission": 1},
      {"role": "Editor", "permission": 2},
      {"teamId": 1, "permission": 2},
      {"userId": 5, "permission": 4}
    ]
  }' \
  https://grafana.example.com/api/folders/production-folder/permissions
```

## Data Source Management

### Get Data Sources

```bash
# Get all data sources
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/datasources

# Get data source by ID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/datasources/1

# Get data source by UID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/datasources/uid/prometheus-uid

# Get data source by name
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/datasources/name/Prometheus"
```

### Create Data Source

```bash
# Create Prometheus data source
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "name": "Prometheus-Production",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "basicAuth": false,
    "isDefault": true,
    "jsonData": {
      "httpMethod": "POST",
      "queryTimeout": "60s",
      "timeInterval": "30s"
    }
  }' \
  https://grafana.example.com/api/datasources

# Create data source with authentication
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "name": "Prometheus-Secure",
    "type": "prometheus",
    "url": "https://prometheus.example.com",
    "access": "proxy",
    "basicAuth": true,
    "basicAuthUser": "admin",
    "secureJsonData": {
      "basicAuthPassword": "password"
    },
    "jsonData": {
      "tlsAuth": true,
      "tlsAuthWithCACert": true
    }
  }' \
  https://grafana.example.com/api/datasources
```

### Update Data Source

```bash
# Update data source
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "id": 1,
    "name": "Prometheus-Production",
    "type": "prometheus",
    "url": "http://prometheus-new:9090",
    "access": "proxy",
    "isDefault": true,
    "jsonData": {
      "httpMethod": "POST",
      "queryTimeout": "120s"
    }
  }' \
  https://grafana.example.com/api/datasources/1
```

### Delete Data Source

```bash
# Delete by ID
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/datasources/1

# Delete by UID
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/datasources/uid/prometheus-uid

# Delete by name
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/datasources/name/Prometheus"
```

### Test Data Source

```bash
# Test data source connection
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/datasources/1/health
```

### Query Data Source

```bash
# Query Prometheus data source
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "queries": [
      {
        "refId": "A",
        "datasource": {"type": "prometheus", "uid": "prometheus-uid"},
        "expr": "up",
        "instant": false,
        "range": true,
        "intervalMs": 1000,
        "maxDataPoints": 100
      }
    ],
    "from": "now-1h",
    "to": "now"
  }' \
  https://grafana.example.com/api/ds/query
```

## User Management

### Get Users

```bash
# Get all users
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/users

# Get user by ID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/users/1

# Get user by login/email
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/users/lookup?loginOrEmail=admin"

# Get current user
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/user
```

### Create User

```bash
# Create user
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "login": "john",
    "password": "SecurePassword123!",
    "orgId": 1
  }' \
  https://grafana.example.com/api/admin/users
```

### Update User

```bash
# Update user
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "email": "john.new@example.com",
    "name": "John Updated",
    "login": "john"
  }' \
  https://grafana.example.com/api/users/2

# Change user password
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"password": "NewPassword123!"}' \
  https://grafana.example.com/api/admin/users/2/password

# Update user permissions
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"isGrafanaAdmin": true}' \
  https://grafana.example.com/api/admin/users/2/permissions
```

### Delete User

```bash
# Delete user
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/admin/users/2
```

## Organization Management

### Get Organizations

```bash
# Get all organizations
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/orgs

# Get organization by ID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/orgs/1

# Get current organization
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/org
```

### Create Organization

```bash
# Create organization
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"name": "New Org"}' \
  https://grafana.example.com/api/orgs
```

### Organization Users

```bash
# Get organization users
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/orgs/1/users

# Add user to organization
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "loginOrEmail": "user@example.com",
    "role": "Editor"
  }' \
  https://grafana.example.com/api/orgs/1/users

# Update user role in organization
curl -X PATCH \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"role": "Admin"}' \
  https://grafana.example.com/api/orgs/1/users/2

# Remove user from organization
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/orgs/1/users/2
```

## Team Management

### Get Teams

```bash
# Get all teams
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/teams/search

# Get team by ID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/teams/1
```

### Create Team

```bash
# Create team
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "name": "DevOps Team",
    "email": "devops@example.com"
  }' \
  https://grafana.example.com/api/teams
```

### Team Members

```bash
# Get team members
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/teams/1/members

# Add user to team
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"userId": 5}' \
  https://grafana.example.com/api/teams/1/members

# Remove user from team
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/teams/1/members/5
```

## Annotations

### Create Annotation

```bash
# Create dashboard annotation
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "dashboardUID": "dashboard-uid",
    "panelId": 1,
    "time": '$(date +%s000)',
    "timeEnd": '$(date -d "+1 hour" +%s000)',
    "tags": ["deployment", "production"],
    "text": "Deployed version 2.0"
  }' \
  https://grafana.example.com/api/annotations

# Create organization annotation
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "time": '$(date +%s000)',
    "tags": ["maintenance"],
    "text": "Database maintenance window"
  }' \
  https://grafana.example.com/api/annotations
```

### Query Annotations

```bash
# Get annotations for dashboard
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/annotations?dashboardUID=dashboard-uid&from=$(date -d '7 days ago' +%s000)&to=$(date +%s000)"

# Get annotations by tags
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/annotations?tags=deployment&tags=production"

# Get annotation by ID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/annotations/1
```

### Update Annotation

```bash
# Update annotation
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "time": '$(date +%s000)',
    "text": "Updated deployment annotation",
    "tags": ["deployment", "production", "v2.1"]
  }' \
  https://grafana.example.com/api/annotations/1
```

### Delete Annotation

```bash
# Delete annotation
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/annotations/1
```

## Alerts

### Get Alerts

```bash
# Get all alerts
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/alerts

# Get alert by ID
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/alerts/1

# Get alerts for dashboard
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "https://grafana.example.com/api/alerts?dashboardId=1"
```

### Pause/Unpause Alert

```bash
# Pause alert
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"paused": true}' \
  https://grafana.example.com/api/alerts/1/pause

# Unpause alert
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"paused": false}' \
  https://grafana.example.com/api/alerts/1/pause
```

### Alert Notifications (Legacy)

```bash
# Get notification channels
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/alert-notifications

# Create notification channel
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "name": "Slack Notifications",
    "type": "slack",
    "isDefault": false,
    "sendReminder": false,
    "settings": {
      "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "recipient": "#alerts",
      "username": "Grafana"
    }
  }' \
  https://grafana.example.com/api/alert-notifications
```

### Unified Alerting (Grafana 8+)

```bash
# Get alert rules
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/ruler/grafana/api/v1/rules

# Create alert rule
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "name": "High CPU Alert",
    "interval": "1m",
    "rules": [
      {
        "uid": "alert-rule-uid",
        "title": "CPU > 80%",
        "condition": "A",
        "data": [
          {
            "refId": "A",
            "queryType": "",
            "relativeTimeRange": {"from": 600, "to": 0},
            "datasourceUid": "prometheus-uid",
            "model": {
              "expr": "avg(rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])) > 0.8"
            }
          }
        ],
        "noDataState": "NoData",
        "execErrState": "Alerting",
        "for": "5m",
        "annotations": {
          "description": "CPU usage is above 80%"
        },
        "labels": {
          "severity": "warning"
        }
      }
    ]
  }' \
  https://grafana.example.com/api/ruler/grafana/api/v1/rules/namespace

# Get contact points
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/v1/provisioning/contact-points

# Create contact point
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "name": "slack-critical",
    "type": "slack",
    "settings": {
      "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "text": "{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}"
    },
    "disableResolveMessage": false
  }' \
  https://grafana.example.com/api/v1/provisioning/contact-points
```

## Snapshots

### Create Snapshot

```bash
# Create snapshot
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "dashboard": {...},
    "name": "Dashboard Snapshot",
    "expires": 3600
  }' \
  https://grafana.example.com/api/snapshots
```

### Get Snapshots

```bash
# Get all snapshots
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/dashboard/snapshots
```

### Delete Snapshot

```bash
# Delete snapshot
curl -X DELETE \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/snapshots/snapshot-key
```

## Health and Admin

### Health Check

```bash
# Basic health check
curl https://grafana.example.com/api/health

# Detailed health
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/health
```

### Admin Stats

```bash
# Get stats
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/admin/stats

# Get settings
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/admin/settings
```

### Preferences

```bash
# Get user preferences
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/user/preferences

# Update user preferences
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "theme": "dark",
    "homeDashboardUID": "dashboard-uid",
    "timezone": "utc"
  }' \
  https://grafana.example.com/api/user/preferences

# Get organization preferences
curl -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  https://grafana.example.com/api/org/preferences

# Update organization preferences
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{
    "theme": "dark",
    "homeDashboardUID": "dashboard-uid",
    "timezone": "utc"
  }' \
  https://grafana.example.com/api/org/preferences
```

## Automation Scripts

### Bulk Dashboard Operations

```bash
#!/bin/bash
# bulk-dashboard-operations.sh

GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"
TAG="production"

# Get all dashboards with specific tag
DASHBOARDS=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/search?tag=${TAG}&type=dash-db" | jq -r '.[] | @base64')

for dashboard in ${DASHBOARDS}; do
  _jq() {
    echo ${dashboard} | base64 --decode | jq -r ${1}
  }

  uid=$(_jq '.uid')
  title=$(_jq '.title')

  echo "Processing: ${title} (${uid})"

  # Get dashboard JSON
  dash=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
    "${GRAFANA_URL}/api/dashboards/uid/${uid}")

  # Modify dashboard (example: add tag)
  modified=$(echo "${dash}" | jq '.dashboard.tags += ["automated"]')

  # Update dashboard
  echo "${modified}" | curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d @- \
    "${GRAFANA_URL}/api/dashboards/db"
done
```

### Monitor Data Source Health

```bash
#!/bin/bash
# monitor-datasources.sh

GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"

# Get all data sources
datasources=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/datasources" | jq -r '.[] | @base64')

for ds in ${datasources}; do
  _jq() {
    echo ${ds} | base64 --decode | jq -r ${1}
  }

  id=$(_jq '.id')
  name=$(_jq '.name')
  type=$(_jq '.type')

  echo "Testing: ${name} (${type})"

  # Test data source
  result=$(curl -s -X POST \
    -H "Authorization: Bearer ${API_KEY}" \
    "${GRAFANA_URL}/api/datasources/${id}/health")

  status=$(echo "${result}" | jq -r '.status')

  if [ "${status}" = "OK" ]; then
    echo "  ✓ ${name}: Healthy"
  else
    echo "  ✗ ${name}: Failed"
    echo "  Error: $(echo ${result} | jq -r '.message')"
  fi
done
```

### Backup All Resources

```bash
#!/bin/bash
# backup-grafana.sh

GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"
BACKUP_DIR="./grafana-backup-$(date +%Y%m%d-%H%M%S)"

mkdir -p "${BACKUP_DIR}"/{dashboards,datasources,folders,alerts}

echo "Backing up to: ${BACKUP_DIR}"

# Backup data sources
echo "Backing up data sources..."
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/datasources" > "${BACKUP_DIR}/datasources/datasources.json"

# Backup folders
echo "Backing up folders..."
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/folders" > "${BACKUP_DIR}/folders/folders.json"

# Backup dashboards
echo "Backing up dashboards..."
DASHBOARDS=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/search?type=dash-db" | jq -r '.[].uid')

for uid in ${DASHBOARDS}; do
  curl -s -H "Authorization: Bearer ${API_KEY}" \
    "${GRAFANA_URL}/api/dashboards/uid/${uid}" > "${BACKUP_DIR}/dashboards/${uid}.json"
done

# Backup alert rules (unified alerting)
echo "Backing up alert rules..."
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/ruler/grafana/api/v1/rules" > "${BACKUP_DIR}/alerts/rules.json"

# Backup contact points
curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/v1/provisioning/contact-points" > "${BACKUP_DIR}/alerts/contact-points.json"

# Create archive
tar czf "${BACKUP_DIR}.tar.gz" "${BACKUP_DIR}"
echo "Backup completed: ${BACKUP_DIR}.tar.gz"
```

### Restore from Backup

```bash
#!/bin/bash
# restore-grafana.sh

GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"
BACKUP_DIR="${1}"

if [ -z "${BACKUP_DIR}" ]; then
  echo "Usage: $0 <backup-directory>"
  exit 1
fi

# Restore data sources
echo "Restoring data sources..."
jq -c '.[]' "${BACKUP_DIR}/datasources/datasources.json" | while read ds; do
  echo "${ds}" | curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d @- \
    "${GRAFANA_URL}/api/datasources"
done

# Restore folders
echo "Restoring folders..."
jq -c '.[]' "${BACKUP_DIR}/folders/folders.json" | while read folder; do
  echo "${folder}" | curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d @- \
    "${GRAFANA_URL}/api/folders"
done

# Restore dashboards
echo "Restoring dashboards..."
for file in "${BACKUP_DIR}"/dashboards/*.json; do
  jq '{dashboard: .dashboard, overwrite: true}' "${file}" | \
    curl -X POST \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${API_KEY}" \
      -d @- \
      "${GRAFANA_URL}/api/dashboards/db"
done

echo "Restore completed"
```
