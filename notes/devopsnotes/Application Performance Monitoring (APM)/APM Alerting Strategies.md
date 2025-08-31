# APM Alerting Strategies

APM alerting strategies define how to proactively notify teams of performance issues, errors, and anomalies in applications. Effective alerting reduces mean time to detection (MTTD) and mean time to resolution (MTTR) while minimizing alert fatigue through intelligent alert management.

## Alerting Framework Components

### 1. Alert Types and Severity Levels
```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import logging

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertType(Enum):
    PERFORMANCE = "performance"
    ERROR = "error"
    AVAILABILITY = "availability"
    CAPACITY = "capacity"
    SECURITY = "security"
    BUSINESS = "business"

@dataclass
class AlertRule:
    name: str
    description: str
    alert_type: AlertType
    severity: AlertSeverity
    metric_name: str
    threshold: float
    comparison: str  # gt, lt, eq, gte, lte
    duration: int  # seconds
    evaluation_window: int  # seconds
    tags: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    
    def evaluate(self, value: float) -> bool:
        """Evaluate if alert condition is met"""
        comparisons = {
            'gt': lambda x, y: x > y,
            'lt': lambda x, y: x < y,
            'eq': lambda x, y: x == y,
            'gte': lambda x, y: x >= y,
            'lte': lambda x, y: x <= y
        }
        return comparisons.get(self.comparison, lambda x, y: False)(value, self.threshold)

@dataclass
class Alert:
    id: str
    rule: AlertRule
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    current_value: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "firing"  # firing, resolved, suppressed
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.rule.name,
            'severity': self.rule.severity.value,
            'type': self.rule.alert_type.value,
            'status': self.status,
            'triggered_at': self.triggered_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'current_value': self.current_value,
            'threshold': self.rule.threshold,
            'context': self.context
        }
```

### 2. Alert Manager Implementation
```python
import asyncio
import uuid
from collections import defaultdict
from typing import Set, Callable, Awaitable

class AlertManager:
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable[[Alert], Awaitable[None]]] = []
        self.suppression_rules: List[Dict] = []
        self.escalation_policies: Dict[str, Dict] = {}
        
    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules[rule.name] = rule
        logging.info(f"Added alert rule: {rule.name}")
    
    def add_notification_handler(self, handler: Callable[[Alert], Awaitable[None]]):
        """Add notification handler"""
        self.notification_handlers.append(handler)
    
    async def evaluate_metrics(self, metrics: Dict[str, float]):
        """Evaluate all rules against current metrics"""
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
                
            if rule.metric_name in metrics:
                value = metrics[rule.metric_name]
                await self._evaluate_rule(rule, value)
    
    async def _evaluate_rule(self, rule: AlertRule, value: float):
        """Evaluate single rule"""
        alert_key = f"{rule.name}_{hash(str(rule.tags))}"
        
        if rule.evaluate(value):
            # Condition met
            if alert_key not in self.active_alerts:
                # New alert
                alert = Alert(
                    id=str(uuid.uuid4()),
                    rule=rule,
                    triggered_at=datetime.utcnow(),
                    current_value=value,
                    context={"tags": rule.tags}
                )
                
                if not self._is_suppressed(alert):
                    self.active_alerts[alert_key] = alert
                    self.alert_history.append(alert)
                    await self._notify(alert)
                    logging.warning(f"Alert fired: {rule.name} - {value}")
            else:
                # Update existing alert
                self.active_alerts[alert_key].current_value = value
        else:
            # Condition not met - resolve if active
            if alert_key in self.active_alerts:
                alert = self.active_alerts[alert_key]
                alert.status = "resolved"
                alert.resolved_at = datetime.utcnow()
                del self.active_alerts[alert_key]
                await self._notify(alert)
                logging.info(f"Alert resolved: {rule.name}")
    
    def _is_suppressed(self, alert: Alert) -> bool:
        """Check if alert should be suppressed"""
        for suppression in self.suppression_rules:
            if self._matches_suppression(alert, suppression):
                return True
        return False
    
    def _matches_suppression(self, alert: Alert, suppression: Dict) -> bool:
        """Check if alert matches suppression rule"""
        for key, value in suppression.get('matchers', {}).items():
            if key == 'severity' and alert.rule.severity.value != value:
                return False
            elif key == 'type' and alert.rule.alert_type.value != value:
                return False
            elif key in alert.rule.tags and alert.rule.tags[key] != value:
                return False
        return True
    
    async def _notify(self, alert: Alert):
        """Send notifications for alert"""
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logging.error(f"Notification handler failed: {e}")
```

### 3. Smart Alerting Features
```python
from sklearn.ensemble import IsolationForest
import numpy as np
from collections import deque
import time

class SmartAlerting:
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        self.baseline_models: Dict[str, Dict] = {}
        
    def update_metric(self, metric_name: str, value: float, timestamp: float = None):
        """Update metric history for anomaly detection"""
        if timestamp is None:
            timestamp = time.time()
            
        self.metric_history[metric_name].append((timestamp, value))
        
        # Update anomaly detector
        if len(self.metric_history[metric_name]) >= 20:
            self._update_anomaly_detector(metric_name)
    
    def _update_anomaly_detector(self, metric_name: str):
        """Update anomaly detection model"""
        history = self.metric_history[metric_name]
        values = np.array([value for _, value in history]).reshape(-1, 1)
        
        if metric_name not in self.anomaly_detectors:
            self.anomaly_detectors[metric_name] = IsolationForest(
                contamination=0.1, random_state=42
            )
        
        self.anomaly_detectors[metric_name].fit(values)
    
    def is_anomalous(self, metric_name: str, value: float) -> tuple[bool, float]:
        """Check if value is anomalous"""
        if metric_name not in self.anomaly_detectors:
            return False, 0.0
        
        detector = self.anomaly_detectors[metric_name]
        anomaly_score = detector.decision_function([[value]])[0]
        is_anomaly = detector.predict([[value]])[0] == -1
        
        return is_anomaly, abs(anomaly_score)
    
    def calculate_dynamic_threshold(self, metric_name: str, percentile: float = 95) -> float:
        """Calculate dynamic threshold based on historical data"""
        if metric_name not in self.metric_history:
            return 0.0
        
        values = [value for _, value in self.metric_history[metric_name]]
        if len(values) < 10:
            return 0.0
        
        return np.percentile(values, percentile)
    
    def predict_next_value(self, metric_name: str) -> Optional[float]:
        """Simple trend-based prediction"""
        if metric_name not in self.metric_history:
            return None
        
        history = list(self.metric_history[metric_name])
        if len(history) < 5:
            return None
        
        # Simple linear trend
        recent_values = [value for _, value in history[-5:]]
        trend = (recent_values[-1] - recent_values[0]) / 4
        return recent_values[-1] + trend
```

### 4. Multi-Channel Notification System
```python
import smtplib
import aiohttp
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationChannel:
    async def send(self, alert: Alert) -> bool:
        raise NotImplementedError

class EmailNotificationChannel(NotificationChannel):
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send(self, alert: Alert) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = alert.rule.tags.get('email', 'admin@company.com')
            msg['Subject'] = f"[{alert.rule.severity.value.upper()}] {alert.rule.name}"
            
            body = self._format_email_body(alert)
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            logging.error(f"Email notification failed: {e}")
            return False
    
    def _format_email_body(self, alert: Alert) -> str:
        status_color = "#FF4444" if alert.status == "firing" else "#44AA44"
        return f"""
        <html>
        <body>
            <h2 style="color: {status_color};">Alert {alert.status.title()}</h2>
            <p><strong>Name:</strong> {alert.rule.name}</p>
            <p><strong>Severity:</strong> {alert.rule.severity.value.upper()}</p>
            <p><strong>Type:</strong> {alert.rule.alert_type.value}</p>
            <p><strong>Current Value:</strong> {alert.current_value}</p>
            <p><strong>Threshold:</strong> {alert.rule.threshold}</p>
            <p><strong>Description:</strong> {alert.rule.description}</p>
            <p><strong>Triggered At:</strong> {alert.triggered_at}</p>
            {f"<p><strong>Resolved At:</strong> {alert.resolved_at}</p>" if alert.resolved_at else ""}
        </body>
        </html>
        """

class SlackNotificationChannel(NotificationChannel):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(self, alert: Alert) -> bool:
        try:
            color = "#FF4444" if alert.status == "firing" else "#44AA44"
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"Alert {alert.status.title()}: {alert.rule.name}",
                    "fields": [
                        {"title": "Severity", "value": alert.rule.severity.value.upper(), "short": True},
                        {"title": "Type", "value": alert.rule.alert_type.value, "short": True},
                        {"title": "Current Value", "value": str(alert.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert.rule.threshold), "short": True},
                        {"title": "Triggered", "value": alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S UTC"), "short": False}
                    ],
                    "footer": "APM Alerting System"
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            logging.error(f"Slack notification failed: {e}")
            return False

class PagerDutyNotificationChannel(NotificationChannel):
    def __init__(self, integration_key: str):
        self.integration_key = integration_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"
    
    async def send(self, alert: Alert) -> bool:
        try:
            event_action = "trigger" if alert.status == "firing" else "resolve"
            
            payload = {
                "routing_key": self.integration_key,
                "event_action": event_action,
                "dedup_key": alert.id,
                "payload": {
                    "summary": f"{alert.rule.name} - {alert.rule.description}",
                    "severity": self._map_severity(alert.rule.severity),
                    "source": "APM System",
                    "component": alert.rule.tags.get('service', 'unknown'),
                    "group": alert.rule.alert_type.value,
                    "custom_details": {
                        "current_value": alert.current_value,
                        "threshold": alert.rule.threshold,
                        "tags": alert.rule.tags
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    return response.status == 202
                    
        except Exception as e:
            logging.error(f"PagerDuty notification failed: {e}")
            return False
    
    def _map_severity(self, severity: AlertSeverity) -> str:
        mapping = {
            AlertSeverity.CRITICAL: "critical",
            AlertSeverity.HIGH: "error",
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.LOW: "info",
            AlertSeverity.INFO: "info"
        }
        return mapping.get(severity, "info")
```

### 5. Alert Correlation and Grouping
```python
from datetime import timedelta
import networkx as nx

class AlertCorrelator:
    def __init__(self):
        self.correlation_rules: List[Dict] = []
        self.alert_graph = nx.DiGraph()
        self.correlation_window = timedelta(minutes=5)
    
    def add_correlation_rule(self, rule: Dict):
        """Add correlation rule
        
        Example rule:
        {
            'name': 'service_dependency',
            'conditions': [
                {'service': 'api', 'type': 'error'},
                {'service': 'database', 'type': 'performance'}
            ],
            'correlation_type': 'causal'
        }
        """
        self.correlation_rules.append(rule)
    
    def correlate_alerts(self, alerts: List[Alert]) -> List[List[Alert]]:
        """Group correlated alerts"""
        correlated_groups = []
        processed_alerts = set()
        
        for alert in alerts:
            if alert.id in processed_alerts:
                continue
            
            group = self._find_correlated_group(alert, alerts)
            if len(group) > 1:
                correlated_groups.append(group)
                processed_alerts.update(a.id for a in group)
        
        return correlated_groups
    
    def _find_correlated_group(self, base_alert: Alert, all_alerts: List[Alert]) -> List[Alert]:
        """Find alerts correlated with base alert"""
        group = [base_alert]
        
        for alert in all_alerts:
            if alert.id == base_alert.id:
                continue
            
            if self._are_correlated(base_alert, alert):
                group.append(alert)
        
        return group
    
    def _are_correlated(self, alert1: Alert, alert2: Alert) -> bool:
        """Check if two alerts are correlated"""
        # Time-based correlation
        time_diff = abs((alert1.triggered_at - alert2.triggered_at).total_seconds())
        if time_diff > self.correlation_window.total_seconds():
            return False
        
        # Rule-based correlation
        for rule in self.correlation_rules:
            if self._matches_correlation_rule(alert1, alert2, rule):
                return True
        
        # Service dependency correlation
        if self._are_service_dependent(alert1, alert2):
            return True
        
        return False
    
    def _matches_correlation_rule(self, alert1: Alert, alert2: Alert, rule: Dict) -> bool:
        """Check if alerts match correlation rule"""
        conditions = rule.get('conditions', [])
        if len(conditions) < 2:
            return False
        
        alerts = [alert1, alert2]
        matched_conditions = 0
        
        for condition in conditions:
            for alert in alerts:
                if all(
                    alert.rule.tags.get(k) == v or 
                    (k == 'type' and alert.rule.alert_type.value == v)
                    for k, v in condition.items()
                ):
                    matched_conditions += 1
                    break
        
        return matched_conditions >= 2
    
    def _are_service_dependent(self, alert1: Alert, alert2: Alert) -> bool:
        """Check service dependency correlation"""
        service1 = alert1.rule.tags.get('service')
        service2 = alert2.rule.tags.get('service')
        
        if not service1 or not service2:
            return False
        
        # Check if services are connected in dependency graph
        if self.alert_graph.has_edge(service1, service2) or self.alert_graph.has_edge(service2, service1):
            return True
        
        return False

    def build_service_graph(self, service_dependencies: List[tuple]):
        """Build service dependency graph"""
        self.alert_graph.clear()
        self.alert_graph.add_edges_from(service_dependencies)
```

## Alert Lifecycle Management

### 1. Alert States and Transitions
```python
class AlertLifecycleManager:
    def __init__(self):
        self.state_transitions = {
            'firing': ['acknowledged', 'resolved', 'suppressed'],
            'acknowledged': ['resolved', 'escalated'],
            'resolved': [],
            'suppressed': ['firing'],
            'escalated': ['resolved', 'acknowledged']
        }
    
    async def acknowledge_alert(self, alert_id: str, user: str, note: str = "") -> bool:
        """Acknowledge an alert"""
        alert = self.get_alert(alert_id)
        if not alert or alert.status not in ['firing']:
            return False
        
        alert.status = 'acknowledged'
        alert.context.update({
            'acknowledged_by': user,
            'acknowledged_at': datetime.utcnow().isoformat(),
            'acknowledgment_note': note
        })
        
        await self._log_state_change(alert, 'acknowledged', user)
        return True
    
    async def escalate_alert(self, alert_id: str, escalation_level: int) -> bool:
        """Escalate an alert to higher severity"""
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        # Increase severity
        severity_order = [AlertSeverity.INFO, AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        current_index = severity_order.index(alert.rule.severity)
        new_index = min(current_index + escalation_level, len(severity_order) - 1)
        
        alert.rule.severity = severity_order[new_index]
        alert.status = 'escalated'
        alert.context.update({
            'escalated_at': datetime.utcnow().isoformat(),
            'escalation_level': escalation_level
        })
        
        await self._log_state_change(alert, 'escalated', 'system')
        await self._notify(alert)  # Re-notify with higher severity
        return True
```

### 2. Alert Configuration Templates
```yaml
# alert_rules.yaml
alert_rules:
  # Performance Alerts
  - name: "high_response_time"
    description: "Application response time exceeds threshold"
    type: "performance"
    severity: "high"
    metric_name: "response_time_p95"
    threshold: 2.0
    comparison: "gt"
    duration: 300
    evaluation_window: 60
    tags:
      service: "api"
      team: "backend"
      runbook: "https://wiki.company.com/runbooks/high_response_time"

  - name: "error_rate_spike"
    description: "Error rate spike detected"
    type: "error"
    severity: "critical"
    metric_name: "error_rate"
    threshold: 5.0
    comparison: "gt"
    duration: 60
    evaluation_window: 60
    tags:
      service: "web"
      team: "frontend"

  # Capacity Alerts
  - name: "high_cpu_utilization"
    description: "CPU utilization exceeds 80%"
    type: "capacity"
    severity: "medium"
    metric_name: "cpu_utilization"
    threshold: 80.0
    comparison: "gt"
    duration: 600
    evaluation_window: 300
    tags:
      infrastructure: "compute"
      team: "platform"

  # Business Metric Alerts
  - name: "revenue_drop"
    description: "Revenue dropped below expected threshold"
    type: "business"
    severity: "critical"
    metric_name: "hourly_revenue"
    threshold: 10000.0
    comparison: "lt"
    duration: 300
    evaluation_window: 3600
    tags:
      business_unit: "sales"
      team: "business"

# Notification Configuration
notification_channels:
  - type: "email"
    name: "team_backend"
    config:
      recipients: ["backend-team@company.com"]
      escalation_delay: 900  # 15 minutes
      
  - type: "slack"
    name: "alerts_channel"
    config:
      webhook_url: "https://hooks.slack.com/services/..."
      channel: "#alerts"
      
  - type: "pagerduty"
    name: "oncall_critical"
    config:
      integration_key: "your-pd-integration-key"
      escalation_policy: "critical-alerts"

# Alert Routing
alert_routing:
  - match:
      severity: "critical"
    route:
      channels: ["pagerduty/oncall_critical", "slack/alerts_channel"]
      
  - match:
      team: "backend"
    route:
      channels: ["email/team_backend", "slack/alerts_channel"]
      
  - match:
      type: "business"
    route:
      channels: ["email/business_team", "slack/business_alerts"]
```

### 3. Alert Testing and Validation
```python
import pytest
from unittest.mock import AsyncMock, patch

class AlertTestSuite:
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
    
    async def test_alert_rule_evaluation(self):
        """Test alert rule evaluation logic"""
        rule = AlertRule(
            name="test_rule",
            description="Test rule",
            alert_type=AlertType.PERFORMANCE,
            severity=AlertSeverity.HIGH,
            metric_name="response_time",
            threshold=1.0,
            comparison="gt",
            duration=60,
            evaluation_window=60
        )
        
        self.alert_manager.add_rule(rule)
        
        # Test firing condition
        await self.alert_manager.evaluate_metrics({"response_time": 1.5})
        assert len(self.alert_manager.active_alerts) == 1
        
        # Test resolution condition
        await self.alert_manager.evaluate_metrics({"response_time": 0.5})
        assert len(self.alert_manager.active_alerts) == 0
    
    async def test_notification_delivery(self):
        """Test notification delivery"""
        notification_sent = False
        
        async def mock_handler(alert: Alert):
            nonlocal notification_sent
            notification_sent = True
        
        self.alert_manager.add_notification_handler(mock_handler)
        
        rule = AlertRule(
            name="notification_test",
            description="Test notifications",
            alert_type=AlertType.ERROR,
            severity=AlertSeverity.CRITICAL,
            metric_name="error_count",
            threshold=10,
            comparison="gt",
            duration=60,
            evaluation_window=60
        )
        
        self.alert_manager.add_rule(rule)
        await self.alert_manager.evaluate_metrics({"error_count": 15})
        
        assert notification_sent
    
    def test_alert_correlation(self):
        """Test alert correlation logic"""
        correlator = AlertCorrelator()
        
        # Create test alerts
        alert1 = Alert(
            id="1",
            rule=AlertRule("db_slow", "", AlertType.PERFORMANCE, AlertSeverity.HIGH, "db_latency", 100, "gt", 60, 60, {"service": "database"}),
            triggered_at=datetime.utcnow()
        )
        
        alert2 = Alert(
            id="2", 
            rule=AlertRule("api_errors", "", AlertType.ERROR, AlertSeverity.HIGH, "error_rate", 5, "gt", 60, 60, {"service": "api"}),
            triggered_at=datetime.utcnow()
        )
        
        # Add correlation rule
        correlator.add_correlation_rule({
            'name': 'db_api_dependency',
            'conditions': [
                {'service': 'database', 'type': 'performance'},
                {'service': 'api', 'type': 'error'}
            ]
        })
        
        correlated = correlator.correlate_alerts([alert1, alert2])
        assert len(correlated) == 1
        assert len(correlated[0]) == 2

# Test execution
async def run_alert_tests():
    alert_manager = AlertManager()
    test_suite = AlertTestSuite(alert_manager)
    
    await test_suite.test_alert_rule_evaluation()
    await test_suite.test_notification_delivery()
    test_suite.test_alert_correlation()
    
    print("All alert tests passed!")

# Chaos testing for alerts
class AlertChaosTest:
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
    
    async def simulate_alert_storm(self, num_alerts: int = 100):
        """Simulate high volume of alerts"""
        metrics = {}
        for i in range(num_alerts):
            metrics[f"metric_{i}"] = 100.0  # High value to trigger alerts
        
        start_time = time.time()
        await self.alert_manager.evaluate_metrics(metrics)
        processing_time = time.time() - start_time
        
        print(f"Processed {num_alerts} alerts in {processing_time:.2f} seconds")
        return processing_time < 5.0  # Should process within 5 seconds
    
    async def test_notification_failures(self):
        """Test system behavior when notifications fail"""
        async def failing_handler(alert: Alert):
            raise Exception("Notification service down")
        
        self.alert_manager.add_notification_handler(failing_handler)
        
        rule = AlertRule("failure_test", "", AlertType.ERROR, AlertSeverity.HIGH, "test_metric", 1, "gt", 60, 60)
        self.alert_manager.add_rule(rule)
        
        # Should not crash system
        await self.alert_manager.evaluate_metrics({"test_metric": 2.0})
        return True
```

## Production Deployment

### 1. Alert Manager Deployment
```dockerfile
# Dockerfile for Alert Manager
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .
COPY config/ ./config/

EXPOSE 8080
CMD ["python", "-m", "alert_manager.main"]
```

### 2. Kubernetes Deployment
```yaml
# k8s-alert-manager.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apm-alert-manager
  labels:
    app: apm-alert-manager
spec:
  replicas: 2
  selector:
    matchLabels:
      app: apm-alert-manager
  template:
    metadata:
      labels:
        app: apm-alert-manager
    spec:
      containers:
      - name: alert-manager
        image: your-repo/apm-alert-manager:latest
        ports:
        - containerPort: 8080
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: postgres-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: apm-alert-manager-service
spec:
  selector:
    app: apm-alert-manager
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
```

This comprehensive APM alerting strategy provides intelligent, scalable alert management with advanced features like anomaly detection, correlation, and multi-channel notifications while maintaining production-grade reliability and performance.