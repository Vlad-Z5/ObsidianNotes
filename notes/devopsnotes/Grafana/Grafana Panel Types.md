## Production Panel Types Runbook

### 1. Logs Panel (Loki) - Most Critical for DevOps

#### Basic Logs Panel Configuration
```json
{
  "type": "logs",
  "datasource": "Loki",
  "targets": [{
    "expr": "{job=\"webapp\", environment=\"prod\"} |= \"ERROR\"",
    "refId": "A"
  }],
  "options": {
    "showTime": true,
    "showLabels": false,
    "showCommonLabels": true,
    "wrapLogMessage": true,
    "prettifyLogMessage": true,
    "enableLogDetails": true,
    "dedupe": true,
    "sortOrder": "Descending"
  },
  "fieldConfig": {
    "defaults": {
      "custom": {
        "displayMode": "json"
      }
    }
  }
}
```

#### Advanced Logs Panel - Incident Response
```json
{
  "type": "logs",
  "title": "Critical Application Errors",
  "datasource": "Loki",
  "targets": [
    {
      "expr": "{service=\"api\"} |= \"CRITICAL\" | json | line_format \"{{.timestamp}} [{{.level}}] {{.message}} (user={{.user_id}})\"",
      "refId": "A",
      "legendFormat": "API Critical"
    },
    {
      "expr": "{service=\"database\"} |= \"deadlock\" or |= \"connection timeout\"",
      "refId": "B", 
      "legendFormat": "DB Issues"
    }
  ],
  "options": {
    "showTime": true,
    "showLabels": true,
    "showCommonLabels": false,
    "wrapLogMessage": false,
    "prettifyLogMessage": true,
    "enableLogDetails": true,
    "dedupe": true,
    "sortOrder": "Descending"
  }
}
```

#### Log Pattern Analysis Panel
```json
{
  "type": "logs",
  "title": "Error Patterns (Last Hour)",
  "datasource": "Loki",
  "targets": [{
    "expr": "topk(10, sum by (error_type) (count_over_time({job=\"webapp\"} | json | __error__=\"\" | error_type!=\"\" [1h])))",
    "refId": "A"
  }],
  "transformations": [{
    "id": "organize",
    "options": {
      "excludeByName": {},
      "indexByName": {},
      "renameByName": {
        "error_type": "Error Type",
        "Value": "Count"
      }
    }
  }]
}
```

### 2. Table Panel - Log Aggregation

#### Error Summary Table (Production Essential)
```json
{
  "type": "table",
  "title": "Top Errors by Service (Last Hour)",
  "datasource": "Loki",
  "targets": [{
    "expr": "topk(10, sum by (service, error_message) (count_over_time({environment=\"prod\"} |= \"ERROR\" | json [1h])))",
    "refId": "A",
    "format": "table"
  }],
  "fieldConfig": {
    "defaults": {
      "custom": {
        "align": "left",
        "width": 200
      },
      "mappings": [],
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "red", "value": 10}
        ]
      }
    },
    "overrides": [
      {
        "matcher": {"id": "byName", "options": "Value"},
        "properties": [
          {"id": "displayName", "value": "Error Count"},
          {"id": "custom.width", "value": 100}
        ]
      }
    ]
  },
  "options": {
    "showHeader": true,
    "sortBy": [{"desc": true, "displayName": "Error Count"}]
  }
}
```

#### User Impact Analysis Table
```json
{
  "type": "table", 
  "title": "Affected Users by Error Type",
  "datasource": "Loki",
  "targets": [{
    "expr": "sum by (error_type) (count by (user_id, error_type) (({service=\"webapp\"} |= \"ERROR\" | json | user_id!=\"\" | error_type!=\"\") [1h]))",
    "refId": "A",
    "format": "table"
  }],
  "transformations": [
    {
      "id": "organize",
      "options": {
        "renameByName": {
          "error_type": "Error Type",
          "Value": "Unique Users Affected"
        }
      }
    },
    {
      "id": "sortBy", 
      "options": {
        "fields": {},
        "sort": [{"desc": true, "field": "Unique Users Affected"}]
      }
    }
  ]
}
```

### 3. Stat Panel - KPI Monitoring

#### Real-time Error Rate
```json
{
  "type": "stat",
  "title": "Current Error Rate",
  "datasource": "Loki",
  "targets": [{
    "expr": "sum(rate({environment=\"prod\"} |= \"ERROR\" [1m]))",
    "refId": "A"
  }],
  "fieldConfig": {
    "defaults": {
      "color": {"mode": "thresholds"},
      "mappings": [],
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 1},
          {"color": "red", "value": 5}
        ]
      },
      "unit": "reqps",
      "custom": {
        "displayMode": "basic",
        "orientation": "horizontal"
      }
    }
  },
  "options": {
    "colorMode": "background",
    "graphMode": "area",
    "justifyMode": "center",
    "orientation": "horizontal",
    "reduceOptions": {
      "calcs": ["lastNotNull"],
      "fields": "",
      "values": false
    },
    "text": {},
    "textMode": "value_and_name"
  }
}
```

#### Service Availability
```json
{
  "type": "stat",
  "title": "Services Health",
  "datasource": "Loki", 
  "targets": [{
    "expr": "count by (service) (count_over_time({job=\"healthcheck\"} |= \"healthy\" [5m]))",
    "refId": "A"
  }],
  "fieldConfig": {
    "defaults": {
      "color": {"mode": "thresholds"},
      "thresholds": {
        "steps": [
          {"color": "red", "value": null},
          {"color": "yellow", "value": 1},  
          {"color": "green", "value": 5}
        ]
      },
      "unit": "short"
    }
  },
  "options": {
    "colorMode": "background",
    "reduceOptions": {
      "calcs": ["lastNotNull"]
    }
  }
}
```

### 4. Time Series Panel - Trend Analysis

#### Log Volume Monitoring
```json
{
  "type": "timeseries",
  "title": "Log Ingestion Rate by Service",
  "datasource": "Loki",
  "targets": [{
    "expr": "sum by (service) (rate(({environment=\"prod\"} [5m])))",
    "refId": "A",
    "legendFormat": "{{service}}"
  }],
  "fieldConfig": {
    "defaults": {
      "color": {"mode": "palette-classic"},
      "custom": {
        "axisLabel": "Logs/sec",
        "axisPlacement": "auto",
        "barAlignment": 0,
        "drawStyle": "line",
        "fillOpacity": 10,
        "gradientMode": "none",
        "hideFrom": {"legend": false, "tooltip": false, "vis": false},
        "lineInterpolation": "linear",
        "lineWidth": 1,
        "pointSize": 5,
        "scaleDistribution": {"type": "linear"},
        "showPoints": "never",
        "spanNulls": false,
        "stacking": {"group": "A", "mode": "none"},
        "thresholdsStyle": {"mode": "off"}
      },
      "unit": "logs/sec"
    }
  }
}
```

#### Error Trend Analysis
```json
{
  "type": "timeseries",
  "title": "Error Rate Trend (5min intervals)",
  "datasource": "Loki",
  "targets": [
    {
      "expr": "sum by (service) (rate({environment=\"prod\"} |= \"ERROR\" [5m]))",
      "refId": "A",
      "legendFormat": "{{service}} errors"
    },
    {
      "expr": "sum by (service) (rate({environment=\"prod\"} |= \"WARN\" [5m]))",
      "refId": "B", 
      "legendFormat": "{{service}} warnings"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "custom": {
        "drawStyle": "line",
        "fillOpacity": 20,
        "lineWidth": 2,
        "pointSize": 4,
        "showPoints": "auto"
      },
      "unit": "reqps"
    },
    "overrides": [
      {
        "matcher": {"id": "byRegexp", "options": ".*errors.*"},
        "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}}]
      },
      {
        "matcher": {"id": "byRegexp", "options": ".*warnings.*"},
        "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "yellow"}}]
      }
    ]
  }
}
```

### 5. Heatmap Panel - Performance Analysis

#### Response Time Distribution
```json
{
  "type": "heatmap",
  "title": "Request Duration Distribution",
  "datasource": "Loki",
  "targets": [{
    "expr": "sum by (le) (rate({service=\"api\"} | json | __error__=\"\" | unwrap duration | histogram_over_time(duration [5m])))",
    "refId": "A",
    "format": "heatmap",
    "legendFormat": "{{le}}"
  }],
  "fieldConfig": {
    "defaults": {
      "custom": {
        "hideFrom": {"legend": false, "tooltip": false, "vis": false},
        "scaleDistribution": {"type": "linear"}
      }
    }
  },
  "options": {
    "calculate": false,
    "cellGap": 1,
    "cellValues": {},
    "color": {
      "exponent": 0.5,
      "fill": "dark-orange",
      "mode": "spectrum",
      "reverse": false,
      "scale": "exponential",
      "scheme": "Oranges",
      "steps": 64
    },
    "exemplars": {"color": "rgba(255,0,255,0.7)"},
    "filterValues": {"le": 1e-9},
    "legend": {"show": true},
    "rowsFrame": {"layout": "auto"},
    "tooltip": {"show": true, "yHistogram": false},
    "yAxis": {
      "axisPlacement": "left",
      "reverse": false,
      "unit": "ms"
    }
  }
}
```

### 6. Bar Gauge Panel - Service Comparison

#### Service Error Comparison
```json
{
  "type": "bargauge",
  "title": "Error Count by Service (Last Hour)",
  "datasource": "Loki",
  "targets": [{
    "expr": "sum by (service) (count_over_time({environment=\"prod\"} |= \"ERROR\" [1h]))",
    "refId": "A",
    "legendFormat": "{{service}}"
  }],
  "fieldConfig": {
    "defaults": {
      "color": {"mode": "continuous-GrYlRd"},
      "custom": {
        "displayMode": "basic",
        "orientation": "horizontal"
      },
      "mappings": [],
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 50},
          {"color": "red", "value": 200}
        ]
      },
      "unit": "short"
    }
  },
  "options": {
    "displayMode": "basic",
    "orientation": "horizontal",
    "reduceOptions": {
      "calcs": ["lastNotNull"],
      "fields": "",
      "values": false
    },
    "showUnfilled": true
  }
}
```

### 7. Gauge Panel - SLA Monitoring

#### SLA Compliance Gauge
```json
{
  "type": "gauge",
  "title": "Service SLA (99.9% target)",
  "datasource": "Loki",
  "targets": [{
    "expr": "(1 - (sum(rate({service=\"webapp\"} |= \"ERROR\" [24h])) / sum(rate({service=\"webapp\"} [24h])))) * 100",
    "refId": "A"
  }],
  "fieldConfig": {
    "defaults": {
      "color": {"mode": "thresholds"},
      "custom": {
        "hideFrom": {"legend": false, "tooltip": false, "vis": false},
        "neutral": 0
      },
      "mappings": [],
      "max": 100,
      "min": 95,
      "thresholds": {
        "steps": [
          {"color": "red", "value": null},
          {"color": "yellow", "value": 99},
          {"color": "green", "value": 99.9}
        ]
      },
      "unit": "percent"
    }
  },
  "options": {
    "orientation": "auto",
    "reduceOptions": {
      "calcs": ["lastNotNull"],
      "fields": "",
      "values": false
    },
    "showThresholdLabels": false,
    "showThresholdMarkers": true,
    "text": {}
  }
}
```

## Panel Layout Best Practices

### Production Dashboard Layout
```bash
# Row 1: Critical KPIs (4 stat panels)
[Error Rate] [Response Time] [Throughput] [SLA %]
Width: 6, 6, 6, 6 | Height: 4

# Row 2: Real-time logs (1 logs panel)  
[Critical Error Logs - Last 15 minutes]
Width: 24 | Height: 8

# Row 3: Trends (2 timeseries panels)
[Error Rate Trend] [Log Volume Trend] 
Width: 12, 12 | Height: 8

# Row 4: Analysis (2 table panels)
[Top Errors] [Affected Users]
Width: 12, 12 | Height: 8
```

### Alert Dashboard Layout
```bash
# Row 1: Alert Status (3 stat panels)
[Firing Alerts] [Pending Alerts] [Resolved Today]
Width: 8, 8, 8 | Height: 4

# Row 2: Alert History (1 logs panel)
[Recent Alert Events]
Width: 24 | Height: 6

# Row 3: Service Health (1 bar gauge)
[Service Status Overview] 
Width: 24 | Height: 6
```

## Panel Troubleshooting

### No Data in Logs Panel
```bash
# 1. Check LogQL syntax
{job="webapp"} |= "ERROR"  # Good
{job="webapp"} |= ERROR    # Bad - missing quotes

# 2. Verify time range
# Ensure time range includes data
# Check if logs exist: curl "http://loki:3100/loki/api/v1/labels"

# 3. Test query in Loki directly
logcli query '{job="webapp"}' --limit=10
```

### Performance Issues
```bash
# 1. Optimize LogQL queries
{service="api", environment="prod"} |= "ERROR"  # Specific labels first
{} |= "ERROR"  # Avoid - too broad

# 2. Reduce time range for expensive operations
sum by (service) (count_over_time({job="webapp"} [5m]))  # Good
sum by (service) (count_over_time({job="webapp"} [24h])) # Slow

# 3. Use recording rules for complex aggregations
```

### Panel Display Issues
```bash
# 1. Check field configuration
- Ensure proper units (bytes, seconds, percent)
- Set appropriate thresholds
- Configure color schemes

# 2. Verify data format
- Table panels need "table" format
- Time series need "time_series" format
- Logs panels use default format
```