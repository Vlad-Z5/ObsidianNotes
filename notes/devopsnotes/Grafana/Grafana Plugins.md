## Plugin Installation

### Install via CLI

```bash
# Install plugin
grafana-cli plugins install grafana-piechart-panel

# Install specific version
grafana-cli plugins install grafana-piechart-panel 1.6.2

# Install from URL
grafana-cli --pluginUrl https://example.com/plugin.zip plugins install plugin-name

# List installed plugins
grafana-cli plugins list-remote

# Update plugin
grafana-cli plugins update grafana-piechart-panel

# Remove plugin
grafana-cli plugins remove grafana-piechart-panel
```

### Install via Environment Variable

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  template:
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.2.3
        env:
        - name: GF_INSTALL_PLUGINS
          value: "grafana-piechart-panel,grafana-clock-panel,grafana-worldmap-panel"
```

### Install via Configuration

```ini
# grafana.ini
[plugins]
enable_alpha = false
app_tls_skip_verify_insecure = false
allow_loading_unsigned_plugins =
plugin_admin_enabled = true
plugin_admin_external_manage_enabled = false
plugin_catalog_url = https://grafana.com/api/plugins
```

### Install in Kubernetes with InitContainer

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  template:
    spec:
      initContainers:
      - name: install-plugins
        image: grafana/grafana:10.2.3
        command:
        - sh
        - -c
        - |
          grafana-cli plugins install grafana-piechart-panel
          grafana-cli plugins install grafana-clock-panel
          grafana-cli plugins install grafana-worldmap-panel
          grafana-cli plugins install alexanderzobnin-zabbix-app
          grafana-cli plugins install redis-datasource
        volumeMounts:
        - name: plugins
          mountPath: /var/lib/grafana/plugins
      containers:
      - name: grafana
        image: grafana/grafana:10.2.3
        volumeMounts:
        - name: plugins
          mountPath: /var/lib/grafana/plugins
      volumes:
      - name: plugins
        emptyDir: {}
```

### Install from Private Repository

```bash
# Using custom plugin repository
grafana-cli \
  --pluginUrl https://nexus.example.com/repository/grafana-plugins/plugin.zip \
  --insecure \
  plugins install custom-plugin
```

## Popular Plugins

### Panel Plugins

#### Piechart Panel

```bash
grafana-cli plugins install grafana-piechart-panel
```

```json
{
  "type": "grafana-piechart-panel",
  "title": "Disk Usage by Mount",
  "targets": [
    {
      "expr": "node_filesystem_size_bytes{mountpoint!~\"^/run.*\"} - node_filesystem_free_bytes{mountpoint!~\"^/run.*\"}",
      "legendFormat": "{{mountpoint}}"
    }
  ],
  "pieType": "pie",
  "legend": {
    "show": true,
    "values": true,
    "percentage": true
  },
  "valueName": "current"
}
```

#### Worldmap Panel

```bash
grafana-cli plugins install grafana-worldmap-panel
```

```json
{
  "type": "grafana-worldmap-panel",
  "title": "Request Origins",
  "targets": [
    {
      "expr": "sum(rate(http_requests_total[5m])) by (country)"
    }
  ],
  "mapCenter": "Europe",
  "mapCenterLatitude": 46,
  "mapCenterLongitude": 14,
  "initialZoom": 4,
  "locationData": "countries",
  "circleMinSize": 2,
  "circleMaxSize": 30
}
```

#### Clock Panel

```bash
grafana-cli plugins install grafana-clock-panel
```

```json
{
  "type": "grafana-clock-panel",
  "title": "Current Time",
  "clockType": "24 hour",
  "dateFormat": "YYYY-MM-DD",
  "fontSize": "60px",
  "fontWeight": "normal",
  "timeZone": "UTC"
}
```

#### Status Panel

```bash
grafana-cli plugins install vonage-status-panel
```

```json
{
  "type": "vonage-status-panel",
  "title": "Service Status",
  "targets": [
    {
      "expr": "up{job=\"api-server\"}"
    }
  ],
  "namePrefix": "Service: ",
  "valueName": "current",
  "colors": {
    "cardColor": "#3E3E3E",
    "ok": "#00FF00",
    "warning": "#FFA500",
    "critical": "#FF0000"
  },
  "thresholds": [
    {"value": 0, "color": "#FF0000"},
    {"value": 1, "color": "#00FF00"}
  ]
}
```

#### Polystat Panel

```bash
grafana-cli plugins install grafana-polystat-panel
```

```json
{
  "type": "grafana-polystat-panel",
  "title": "Pod Health",
  "targets": [
    {
      "expr": "kube_pod_status_phase{phase=\"Running\"}"
    }
  ],
  "polystat": {
    "columnAutoSize": true,
    "columns": 5,
    "displayLimit": 100,
    "fontAutoScale": true,
    "shape": "hexagon_pointed_top"
  },
  "thresholds": [
    {"value": 0, "state": 2, "color": "#F2495C"},
    {"value": 1, "state": 0, "color": "#73BF69"}
  ]
}
```

#### Boom Table

```bash
grafana-cli plugins install yesoreyeram-boomtable-panel
```

#### Plotly Panel

```bash
grafana-cli plugins install ae3e-plotly-panel
```

### Data Source Plugins

#### Redis Data Source

```bash
grafana-cli plugins install redis-datasource
```

```json
{
  "name": "Redis",
  "type": "redis-datasource",
  "url": "redis://redis:6379",
  "access": "proxy",
  "jsonData": {
    "client": "standalone",
    "poolSize": 5,
    "timeout": 10,
    "pingInterval": 0,
    "pipelineWindow": 0
  },
  "secureJsonData": {
    "password": "redis-password"
  }
}
```

#### MongoDB Data Source

```bash
grafana-cli plugins install grafana-mongodb-datasource
```

```json
{
  "name": "MongoDB",
  "type": "grafana-mongodb-datasource",
  "url": "mongodb://mongodb:27017",
  "database": "metrics",
  "jsonData": {
    "authSource": "admin",
    "ssl": false
  },
  "secureJsonData": {
    "user": "grafana",
    "password": "password"
  }
}
```

#### JSON API Data Source

```bash
grafana-cli plugins install marcusolsson-json-datasource
```

```json
{
  "name": "JSON API",
  "type": "marcusolsson-json-datasource",
  "url": "https://api.example.com",
  "access": "proxy",
  "jsonData": {
    "timeout": 60
  },
  "secureJsonData": {
    "apiKey": "your-api-key"
  }
}
```

#### SimpleJson Data Source

```bash
grafana-cli plugins install grafana-simple-json-datasource
```

```json
{
  "name": "SimpleJson",
  "type": "grafana-simple-json-datasource",
  "url": "http://backend-service:3000",
  "access": "proxy",
  "basicAuth": true,
  "basicAuthUser": "user",
  "secureJsonData": {
    "basicAuthPassword": "password"
  }
}
```

#### CSV Data Source

```bash
grafana-cli plugins install marcusolsson-csv-datasource
```

#### Zabbix Data Source

```bash
grafana-cli plugins install alexanderzobnin-zabbix-app
```

```json
{
  "name": "Zabbix",
  "type": "alexanderzobnin-zabbix-datasource",
  "url": "http://zabbix-server/api_jsonrpc.php",
  "access": "proxy",
  "jsonData": {
    "username": "Admin",
    "trends": true,
    "trendsFrom": "7d",
    "trendsRange": "4d",
    "cacheTTL": "1h"
  },
  "secureJsonData": {
    "password": "zabbix"
  }
}
```

### App Plugins

#### Kubernetes App

```bash
grafana-cli plugins install grafana-kubernetes-app
```

```bash
# Enable plugin
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d '{"enabled": true}' \
  https://grafana.example.com/api/plugins/grafana-kubernetes-app/settings
```

#### Azure Monitor App

```bash
grafana-cli plugins install grafana-azure-monitor-datasource
```

#### Synthetic Monitoring

```bash
grafana-cli plugins install grafana-synthetic-monitoring-app
```

## Custom Plugin Development

### Plugin Structure

```
my-custom-panel/
├── src/
│   ├── module.ts
│   ├── plugin.json
│   ├── types.ts
│   └── components/
│       └── Panel.tsx
├── package.json
├── tsconfig.json
└── README.md
```

### plugin.json

```json
{
  "type": "panel",
  "name": "Custom Panel",
  "id": "myorg-custom-panel",
  "info": {
    "description": "Custom panel plugin",
    "author": {
      "name": "Your Name",
      "url": "https://example.com"
    },
    "keywords": ["panel"],
    "version": "1.0.0",
    "updated": "2024-01-01"
  },
  "dependencies": {
    "grafanaDependency": ">=9.0.0",
    "grafanaVersion": "9.0.0",
    "plugins": []
  }
}
```

### module.ts (Panel Plugin)

```typescript
import { PanelPlugin } from '@grafana/data';
import { SimpleOptions } from './types';
import { SimplePanel } from './components/Panel';

export const plugin = new PanelPlugin<SimpleOptions>(SimplePanel).setPanelOptions((builder) => {
  return builder
    .addTextInput({
      path: 'title',
      name: 'Title',
      description: 'Panel title',
      defaultValue: 'Default Title',
    })
    .addNumberInput({
      path: 'threshold',
      name: 'Threshold',
      description: 'Alert threshold',
      defaultValue: 80,
    })
    .addColorPicker({
      path: 'color',
      name: 'Color',
      description: 'Panel color',
      defaultValue: 'green',
    })
    .addBooleanSwitch({
      path: 'showLegend',
      name: 'Show Legend',
      defaultValue: true,
    });
});
```

### Panel Component (React)

```typescript
import React from 'react';
import { PanelProps } from '@grafana/data';
import { SimpleOptions } from '../types';
import { css, cx } from '@emotion/css';
import { useStyles2, useTheme2 } from '@grafana/ui';

interface Props extends PanelProps<SimpleOptions> {}

export const SimplePanel: React.FC<Props> = ({ options, data, width, height }) => {
  const theme = useTheme2();
  const styles = useStyles2(getStyles);

  const value = data.series[0]?.fields[1]?.values.get(0) || 0;
  const isAlert = value > options.threshold;

  return (
    <div
      className={cx(
        styles.wrapper,
        css`
          width: ${width}px;
          height: ${height}px;
        `
      )}
    >
      <div className={styles.title}>{options.title}</div>
      <div
        className={styles.value}
        style={{
          color: isAlert ? theme.colors.error.main : options.color,
        }}
      >
        {value.toFixed(2)}
      </div>
      {options.showLegend && (
        <div className={styles.legend}>
          Threshold: {options.threshold}
        </div>
      )}
    </div>
  );
};

const getStyles = () => {
  return {
    wrapper: css`
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    `,
    title: css`
      font-size: 24px;
      font-weight: bold;
      margin-bottom: 10px;
    `,
    value: css`
      font-size: 48px;
      font-weight: bold;
    `,
    legend: css`
      font-size: 14px;
      margin-top: 10px;
      opacity: 0.7;
    `,
  };
};
```

### Data Source Plugin

```typescript
import {
  DataQueryRequest,
  DataQueryResponse,
  DataSourceApi,
  DataSourceInstanceSettings,
  MutableDataFrame,
  FieldType,
} from '@grafana/data';
import { getBackendSrv } from '@grafana/runtime';
import { MyQuery, MyDataSourceOptions } from './types';

export class DataSource extends DataSourceApi<MyQuery, MyDataSourceOptions> {
  url?: string;

  constructor(instanceSettings: DataSourceInstanceSettings<MyDataSourceOptions>) {
    super(instanceSettings);
    this.url = instanceSettings.url;
  }

  async query(options: DataQueryRequest<MyQuery>): Promise<DataQueryResponse> {
    const { range } = options;
    const from = range!.from.valueOf();
    const to = range!.to.valueOf();

    const promises = options.targets.map(async (target) => {
      const response = await getBackendSrv().datasourceRequest({
        url: `${this.url}/query`,
        method: 'POST',
        data: {
          query: target.queryText,
          from,
          to,
        },
      });

      const frame = new MutableDataFrame({
        refId: target.refId,
        fields: [
          { name: 'Time', type: FieldType.time },
          { name: 'Value', type: FieldType.number },
        ],
      });

      response.data.forEach((point: any) => {
        frame.add({
          Time: point.timestamp,
          Value: point.value,
        });
      });

      return frame;
    });

    return Promise.all(promises).then((data) => ({ data }));
  }

  async testDatasource() {
    try {
      await getBackendSrv().datasourceRequest({
        url: `${this.url}/health`,
        method: 'GET',
      });
      return {
        status: 'success',
        message: 'Data source is working',
      };
    } catch (error) {
      return {
        status: 'error',
        message: 'Cannot connect to data source',
      };
    }
  }
}
```

### package.json

```json
{
  "name": "myorg-custom-panel",
  "version": "1.0.0",
  "description": "Custom Grafana panel plugin",
  "scripts": {
    "build": "grafana-toolkit plugin:build",
    "test": "grafana-toolkit plugin:test",
    "dev": "grafana-toolkit plugin:dev",
    "watch": "grafana-toolkit plugin:dev --watch",
    "sign": "grafana-toolkit plugin:sign"
  },
  "author": "Your Name",
  "license": "Apache-2.0",
  "devDependencies": {
    "@grafana/data": "latest",
    "@grafana/toolkit": "latest",
    "@grafana/ui": "latest",
    "@grafana/runtime": "latest"
  }
}
```

### Building Plugin

```bash
# Install dependencies
npm install

# Development build with watch
npm run watch

# Production build
npm run build

# Run tests
npm run test

# Sign plugin (for private plugins)
npm run sign
```

## Plugin Configuration

### Configure Plugin Settings

```yaml
# /etc/grafana/provisioning/plugins/plugins.yml
apiVersion: 1

apps:
  - type: grafana-kubernetes-app
    name: Kubernetes
    enabled: true
    jsonData:
      clusterUrl: https://kubernetes.default.svc
```

### Plugin Permissions

```ini
# grafana.ini
[plugins]
enable_alpha = false
app_tls_skip_verify_insecure = false

# Allow unsigned plugins (comma-separated list)
allow_loading_unsigned_plugins = myorg-custom-panel,myorg-custom-datasource

# External plugin management
plugin_admin_enabled = true
plugin_admin_external_manage_enabled = false
```

### Plugin Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-plugin-secrets
  namespace: monitoring
type: Opaque
stringData:
  plugin-api-key: "secret-api-key-value"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  template:
    spec:
      containers:
      - name: grafana
        env:
        - name: GF_PLUGIN_API_KEY
          valueFrom:
            secretKeyRef:
              name: grafana-plugin-secrets
              key: plugin-api-key
```

## Plugin Management in Production

### Version Pinning

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  template:
    spec:
      initContainers:
      - name: install-plugins
        image: grafana/grafana:10.2.3
        command:
        - sh
        - -c
        - |
          grafana-cli plugins install grafana-piechart-panel 1.6.2
          grafana-cli plugins install grafana-clock-panel 2.1.3
          grafana-cli plugins install redis-datasource 2.0.0
        volumeMounts:
        - name: plugins
          mountPath: /var/lib/grafana/plugins
```

### Plugin Update Strategy

```bash
#!/bin/bash
# update-plugins.sh

PLUGINS=(
  "grafana-piechart-panel"
  "grafana-clock-panel"
  "redis-datasource"
)

for plugin in "${PLUGINS[@]}"; do
  echo "Checking updates for: ${plugin}"

  # Get current version
  current=$(grafana-cli plugins ls | grep "${plugin}" | awk '{print $2}')

  # Get latest version
  latest=$(grafana-cli plugins list-remote | grep "^id: ${plugin}" -A 1 | grep version | awk '{print $2}')

  if [ "${current}" != "${latest}" ]; then
    echo "Updating ${plugin} from ${current} to ${latest}"
    grafana-cli plugins update "${plugin}"
  else
    echo "${plugin} is up to date (${current})"
  fi
done

# Restart Grafana
systemctl restart grafana-server
```

### Automated Plugin Testing

```bash
#!/bin/bash
# test-plugins.sh

GRAFANA_URL="http://localhost:3000"
ADMIN_USER="admin"
ADMIN_PASS="admin"

# Get installed plugins
plugins=$(curl -s -u "${ADMIN_USER}:${ADMIN_PASS}" \
  "${GRAFANA_URL}/api/plugins" | jq -r '.[].id')

for plugin in ${plugins}; do
  echo "Testing plugin: ${plugin}"

  # Get plugin details
  details=$(curl -s -u "${ADMIN_USER}:${ADMIN_PASS}" \
    "${GRAFANA_URL}/api/plugins/${plugin}")

  enabled=$(echo "${details}" | jq -r '.enabled')

  if [ "${enabled}" = "true" ]; then
    echo "  ✓ ${plugin}: Enabled"
  else
    echo "  ✗ ${plugin}: Disabled"
  fi
done
```

### Plugin Monitoring

```yaml
# Prometheus alert for plugin errors
groups:
- name: grafana-plugins
  interval: 1m
  rules:
  - alert: GrafanaPluginError
    expr: increase(grafana_plugin_request_duration_seconds_count{status_code!~"2.."}[5m]) > 0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Grafana plugin {{ $labels.plugin_id }} errors"
      description: "Plugin {{ $labels.plugin_id }} has {{ $value }} errors in the last 5 minutes"

  - alert: GrafanaPluginSlow
    expr: histogram_quantile(0.99, rate(grafana_plugin_request_duration_seconds_bucket[5m])) > 5
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Grafana plugin {{ $labels.plugin_id }} slow"
      description: "Plugin {{ $labels.plugin_id }} p99 latency is {{ $value }}s"
```

## Plugin Security

### Signing Plugins

```bash
# Generate private key
openssl genrsa -out private.pem 2048

# Sign plugin
npx @grafana/toolkit plugin:sign \
  --rootUrls https://grafana.example.com

# Verify signature
npx @grafana/toolkit plugin:sign:verify
```

### Plugin Manifest Security

```json
{
  "id": "myorg-custom-panel",
  "type": "panel",
  "name": "Custom Panel",
  "info": {
    "version": "1.0.0",
    "updated": "2024-01-01"
  },
  "dependencies": {
    "grafanaDependency": ">=9.0.0"
  },
  "includes": [
    {
      "type": "panel",
      "name": "Custom Panel"
    }
  ],
  "signature": {
    "status": "valid",
    "type": "private",
    "signedBy": "MyOrg",
    "signatureType": "private"
  }
}
```

### Security Best Practices

```yaml
# Restrict plugin installation
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-config
  namespace: monitoring
data:
  grafana.ini: |
    [plugins]
    enable_alpha = false
    app_tls_skip_verify_insecure = false
    allow_loading_unsigned_plugins =
    plugin_admin_enabled = false
    plugin_admin_external_manage_enabled = false

    # Only allow specific plugin sources
    plugin_catalog_url = https://internal-plugin-repo.example.com/plugins
```

## Plugin Troubleshooting

### Debug Plugin Issues

```ini
# grafana.ini
[log]
mode = console file
level = debug
filters = plugins:debug
```

```bash
# Check plugin logs
tail -f /var/log/grafana/grafana.log | grep plugin

# List loaded plugins
curl -u admin:password http://localhost:3000/api/plugins

# Check plugin health
curl -u admin:password http://localhost:3000/api/plugins/{plugin-id}/health

# Inspect plugin files
ls -la /var/lib/grafana/plugins/

# Validate plugin.json
cat /var/lib/grafana/plugins/my-plugin/plugin.json | jq .
```

### Common Plugin Issues

```markdown
## Plugin Not Loading

1. Check plugin directory permissions
   chmod -R 755 /var/lib/grafana/plugins/

2. Verify plugin.json exists and is valid
   cat plugin.json | jq .

3. Check Grafana logs for errors
   tail -f /var/log/grafana/grafana.log | grep -i error

4. Restart Grafana
   systemctl restart grafana-server

## Plugin Unsigned Error

1. Add plugin to allow_loading_unsigned_plugins in grafana.ini
   [plugins]
   allow_loading_unsigned_plugins = myorg-custom-panel

2. Or sign the plugin properly
   npx @grafana/toolkit plugin:sign

## Plugin Performance Issues

1. Enable profiling
   [profiling]
   enabled = true

2. Check plugin metrics
   curl http://localhost:3000/metrics | grep plugin

3. Review plugin query performance
   Check "Query inspector" in Grafana UI
```
