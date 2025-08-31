# APM Application Metrics & KPIs

Application metrics and Key Performance Indicators (KPIs) provide quantitative insights into application performance, user experience, and business outcomes. This guide covers essential metrics collection, analysis frameworks, alerting strategies, and enterprise-grade monitoring implementations crucial for maintaining optimal application performance and reliability.

## Core Application Metrics Framework

### Golden Signals and SLI/SLO Implementation

```python
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import statistics
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import json

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class SLO:
    name: str
    description: str
    target_percentage: float  # e.g., 99.9 for 99.9%
    time_window_hours: int    # e.g., 24 for 24 hours
    error_budget_minutes: float = field(init=False)
    
    def __post_init__(self):
        # Calculate error budget in minutes
        total_minutes = self.time_window_hours * 60
        self.error_budget_minutes = total_minutes * (100 - self.target_percentage) / 100

@dataclass
class Metric:
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    help_text: str = ""

class MetricsCollector:
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Time series data for analysis
        self.time_series: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
    def increment_counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            metric_key = self._get_metric_key(name, labels)
            self.counters[metric_key] += value
            
            metric = Metric(
                name=name,
                metric_type=MetricType.COUNTER,
                value=self.counters[metric_key],
                timestamp=datetime.utcnow(),
                labels=labels or {}
            )
            
            self.metrics[name].append(metric)
            self.time_series[metric_key].append((time.time(), self.counters[metric_key]))
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value"""
        with self.lock:
            metric_key = self._get_metric_key(name, labels)
            self.gauges[metric_key] = value
            
            metric = Metric(
                name=name,
                metric_type=MetricType.GAUGE,
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels or {}
            )
            
            self.metrics[name].append(metric)
            self.time_series[metric_key].append((time.time(), value))
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Add observation to histogram"""
        with self.lock:
            metric_key = self._get_metric_key(name, labels)
            self.histograms[metric_key].append(value)
            
            metric = Metric(
                name=name,
                metric_type=MetricType.HISTOGRAM,
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels or {}
            )
            
            self.metrics[name].append(metric)
            self.time_series[metric_key].append((time.time(), value))
    
    def get_histogram_percentiles(self, name: str, labels: Dict[str, str] = None, 
                                percentiles: List[float] = None) -> Dict[float, float]:
        """Calculate histogram percentiles"""
        if percentiles is None:
            percentiles = [0.5, 0.90, 0.95, 0.99]
        
        metric_key = self._get_metric_key(name, labels)
        values = self.histograms.get(metric_key, [])
        
        if not values:
            return {p: 0.0 for p in percentiles}
        
        sorted_values = sorted(values)
        result = {}
        
        for percentile in percentiles:
            index = int(percentile * (len(sorted_values) - 1))
            result[percentile] = sorted_values[index]
        
        return result
    
    def get_rate(self, name: str, labels: Dict[str, str] = None, 
                window_seconds: int = 60) -> float:
        """Calculate rate of change for counter"""
        metric_key = self._get_metric_key(name, labels)
        time_series = list(self.time_series.get(metric_key, []))
        
        if len(time_series) < 2:
            return 0.0
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Filter to time window
        windowed_data = [(t, v) for t, v in time_series if t >= window_start]
        
        if len(windowed_data) < 2:
            return 0.0
        
        # Calculate rate (change in value / time difference)
        earliest = windowed_data[0]
        latest = windowed_data[-1]
        
        time_diff = latest[0] - earliest[0]
        value_diff = latest[1] - earliest[1]
        
        return value_diff / time_diff if time_diff > 0 else 0.0
    
    def _get_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Generate unique key for metric with labels"""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

class GoldenSignalsMonitor:
    """Monitor the four golden signals of monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.slos = {}
        
    def configure_slos(self):
        """Configure Service Level Objectives"""
        self.slos = {
            'availability': SLO(
                name='availability',
                description='Service availability',
                target_percentage=99.9,
                time_window_hours=24
            ),
            'latency_p95': SLO(
                name='latency_p95',
                description='95th percentile latency under 200ms',
                target_percentage=95.0,
                time_window_hours=1
            ),
            'error_rate': SLO(
                name='error_rate',
                description='Error rate below 0.1%',
                target_percentage=99.9,
                time_window_hours=1
            ),
            'saturation_cpu': SLO(
                name='saturation_cpu',
                description='CPU utilization under 80%',
                target_percentage=95.0,
                time_window_hours=1
            )
        }
    
    def track_request(self, endpoint: str, method: str, status_code: int, 
                     duration_ms: float, user_id: str = None):
        """Track HTTP request metrics"""
        labels = {
            'endpoint': endpoint,
            'method': method,
            'status_class': f"{status_code // 100}xx"
        }
        
        if user_id:
            labels['user_id'] = user_id
        
        # Latency (Golden Signal #1)
        self.metrics.observe_histogram('http_request_duration_ms', duration_ms, labels)
        
        # Traffic (Golden Signal #2) 
        self.metrics.increment_counter('http_requests_total', 1, labels)
        
        # Errors (Golden Signal #3)
        if status_code >= 400:
            error_labels = labels.copy()
            error_labels['status_code'] = str(status_code)
            self.metrics.increment_counter('http_requests_errors_total', 1, error_labels)
        
        # Success counter for availability calculation
        if status_code < 400:
            self.metrics.increment_counter('http_requests_success_total', 1, labels)
    
    def track_saturation_metrics(self, cpu_percent: float, memory_percent: float, 
                               disk_percent: float, network_connections: int):
        """Track saturation metrics (Golden Signal #4)"""
        self.metrics.set_gauge('cpu_utilization_percent', cpu_percent)
        self.metrics.set_gauge('memory_utilization_percent', memory_percent)
        self.metrics.set_gauge('disk_utilization_percent', disk_percent)
        self.metrics.set_gauge('network_connections_active', network_connections)
    
    def calculate_golden_signals(self, time_window_minutes: int = 5) -> Dict[str, Any]:
        """Calculate current golden signals metrics"""
        
        # 1. Latency
        latency_p95 = self.metrics.get_histogram_percentiles(
            'http_request_duration_ms', 
            percentiles=[0.95]
        )[0.95]
        
        latency_p99 = self.metrics.get_histogram_percentiles(
            'http_request_duration_ms',
            percentiles=[0.99]
        )[0.99]
        
        # 2. Traffic
        request_rate = self.metrics.get_rate('http_requests_total', window_seconds=time_window_minutes * 60)
        
        # 3. Errors
        error_rate = self.metrics.get_rate('http_requests_errors_total', window_seconds=time_window_minutes * 60)
        success_rate = self.metrics.get_rate('http_requests_success_total', window_seconds=time_window_minutes * 60)
        
        total_rate = request_rate
        error_percentage = (error_rate / total_rate * 100) if total_rate > 0 else 0
        availability = (success_rate / total_rate * 100) if total_rate > 0 else 100
        
        # 4. Saturation
        current_gauges = {}
        for metric_name in ['cpu_utilization_percent', 'memory_utilization_percent', 
                          'disk_utilization_percent', 'network_connections_active']:
            gauge_key = self._get_latest_gauge_value(metric_name)
            current_gauges[metric_name] = gauge_key
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'latency': {
                'p95_ms': latency_p95,
                'p99_ms': latency_p99,
                'slo_target_ms': 200,
                'slo_compliance': latency_p95 <= 200
            },
            'traffic': {
                'requests_per_second': request_rate,
                'requests_per_minute': request_rate * 60
            },
            'errors': {
                'error_rate_percent': error_percentage,
                'availability_percent': availability,
                'slo_target_availability': 99.9,
                'slo_compliance': availability >= 99.9
            },
            'saturation': {
                'cpu_percent': current_gauges.get('cpu_utilization_percent', 0),
                'memory_percent': current_gauges.get('memory_utilization_percent', 0),
                'disk_percent': current_gauges.get('disk_utilization_percent', 0),
                'network_connections': current_gauges.get('network_connections_active', 0),
                'slo_compliance': current_gauges.get('cpu_utilization_percent', 0) <= 80
            }
        }
    
    def _get_latest_gauge_value(self, metric_name: str) -> float:
        """Get latest value for a gauge metric"""
        if metric_name in self.metrics.gauges:
            return list(self.metrics.gauges.values())[0] if self.metrics.gauges else 0
        return 0.0
    
    def check_slo_compliance(self) -> Dict[str, Any]:
        """Check SLO compliance and calculate error budget burn"""
        compliance_report = {}
        
        for slo_name, slo in self.slos.items():
            if slo_name == 'availability':
                # Check availability SLO
                golden_signals = self.calculate_golden_signals(time_window_minutes=60)
                current_availability = golden_signals['errors']['availability_percent']
                
                compliance = current_availability >= slo.target_percentage
                error_budget_used = max(0, 100 - current_availability)
                error_budget_remaining = max(0, (100 - slo.target_percentage) - error_budget_used)
                
                compliance_report[slo_name] = {
                    'slo': slo.target_percentage,
                    'current': current_availability,
                    'compliant': compliance,
                    'error_budget_total_minutes': slo.error_budget_minutes,
                    'error_budget_used_percent': (error_budget_used / (100 - slo.target_percentage)) * 100,
                    'error_budget_remaining_minutes': (error_budget_remaining / 100) * (slo.time_window_hours * 60)
                }
            
            elif slo_name == 'latency_p95':
                # Check latency SLO
                golden_signals = self.calculate_golden_signals(time_window_minutes=60)
                current_latency = golden_signals['latency']['p95_ms']
                
                compliance = current_latency <= 200  # 200ms target
                compliance_report[slo_name] = {
                    'slo': 200,
                    'current': current_latency,
                    'compliant': compliance
                }
        
        return compliance_report

# Business Metrics and KPI Tracking
class BusinessMetricsTracker:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        
    def track_user_activity(self, user_id: str, action: str, value: float = 1):
        """Track user activity metrics"""
        labels = {
            'user_id': user_id,
            'action': action
        }
        
        self.metrics.increment_counter('user_actions_total', value, labels)
        
        # Track unique active users
        self.metrics.set_gauge(f'user_active_{user_id}', 1, {'action': action})
    
    def track_business_transaction(self, transaction_type: str, amount: float, 
                                 currency: str = 'USD', user_id: str = None):
        """Track business transactions"""
        labels = {
            'transaction_type': transaction_type,
            'currency': currency
        }
        
        if user_id:
            labels['user_id'] = user_id
        
        # Transaction count
        self.metrics.increment_counter('business_transactions_total', 1, labels)
        
        # Transaction value
        self.metrics.observe_histogram('business_transaction_value', amount, labels)
        
        # Revenue tracking
        if transaction_type in ['purchase', 'subscription', 'upgrade']:
            self.metrics.increment_counter('revenue_total', amount, labels)
    
    def track_conversion_funnel(self, stage: str, user_id: str = None):
        """Track conversion funnel stages"""
        labels = {
            'stage': stage
        }
        
        if user_id:
            labels['user_id'] = user_id
        
        self.metrics.increment_counter('conversion_funnel_total', 1, labels)
    
    def track_feature_usage(self, feature: str, user_id: str = None, 
                          session_id: str = None):
        """Track feature usage"""
        labels = {
            'feature': feature
        }
        
        if user_id:
            labels['user_id'] = user_id
        if session_id:
            labels['session_id'] = session_id
        
        self.metrics.increment_counter('feature_usage_total', 1, labels)
    
    def calculate_business_kpis(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Calculate business KPIs"""
        window_seconds = time_window_minutes * 60
        
        # Revenue metrics
        revenue_rate = self.metrics.get_rate('revenue_total', window_seconds=window_seconds)
        
        # Transaction metrics
        transaction_rate = self.metrics.get_rate('business_transactions_total', window_seconds=window_seconds)
        
        # User activity
        user_action_rate = self.metrics.get_rate('user_actions_total', window_seconds=window_seconds)
        
        # Feature usage
        feature_usage_rate = self.metrics.get_rate('feature_usage_total', window_seconds=window_seconds)
        
        # Conversion rates (simplified calculation)
        conversion_stages = ['landing', 'signup', 'trial', 'purchase']
        conversion_funnel = {}
        
        for stage in conversion_stages:
            stage_rate = self.metrics.get_rate(
                'conversion_funnel_total', 
                labels={'stage': stage},
                window_seconds=window_seconds
            )
            conversion_funnel[stage] = stage_rate
        
        # Calculate conversion rates
        signup_conversion = 0
        trial_conversion = 0
        purchase_conversion = 0
        
        if conversion_funnel['landing'] > 0:
            signup_conversion = (conversion_funnel['signup'] / conversion_funnel['landing']) * 100
        
        if conversion_funnel['signup'] > 0:
            trial_conversion = (conversion_funnel['trial'] / conversion_funnel['signup']) * 100
        
        if conversion_funnel['trial'] > 0:
            purchase_conversion = (conversion_funnel['purchase'] / conversion_funnel['trial']) * 100
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'time_window_minutes': time_window_minutes,
            'revenue': {
                'revenue_per_minute': revenue_rate * 60,
                'revenue_per_hour': revenue_rate * 3600,
                'estimated_daily_revenue': revenue_rate * 86400
            },
            'transactions': {
                'transactions_per_minute': transaction_rate * 60,
                'transactions_per_hour': transaction_rate * 3600
            },
            'user_engagement': {
                'user_actions_per_minute': user_action_rate * 60,
                'feature_usage_per_minute': feature_usage_rate * 60
            },
            'conversion_funnel': {
                'landing_to_signup_percent': signup_conversion,
                'signup_to_trial_percent': trial_conversion,
                'trial_to_purchase_percent': purchase_conversion,
                'overall_conversion_percent': (conversion_funnel['purchase'] / conversion_funnel['landing'] * 100) if conversion_funnel['landing'] > 0 else 0
            }
        }

# Real-time Alerting System
class MetricsAlerter:
    def __init__(self, golden_signals_monitor: GoldenSignalsMonitor):
        self.monitor = golden_signals_monitor
        self.alert_rules = {}
        self.alert_history = []
        
    def add_alert_rule(self, name: str, metric_path: str, threshold: float, 
                      comparison: str, severity: AlertSeverity, 
                      description: str = ""):
        """Add alert rule"""
        self.alert_rules[name] = {
            'metric_path': metric_path,
            'threshold': threshold,
            'comparison': comparison,  # 'gt', 'lt', 'eq'
            'severity': severity,
            'description': description,
            'last_fired': None,
            'fired_count': 0
        }
    
    def configure_default_alerts(self):
        """Configure default alert rules"""
        # Latency alerts
        self.add_alert_rule(
            'high_latency_p95',
            'latency.p95_ms',
            200,
            'gt',
            AlertSeverity.WARNING,
            'P95 latency above 200ms'
        )
        
        self.add_alert_rule(
            'critical_latency_p95',
            'latency.p95_ms', 
            500,
            'gt',
            AlertSeverity.CRITICAL,
            'P95 latency above 500ms'
        )
        
        # Error rate alerts
        self.add_alert_rule(
            'high_error_rate',
            'errors.error_rate_percent',
            1.0,
            'gt',
            AlertSeverity.WARNING,
            'Error rate above 1%'
        )
        
        self.add_alert_rule(
            'critical_error_rate',
            'errors.error_rate_percent',
            5.0,
            'gt',
            AlertSeverity.CRITICAL,
            'Error rate above 5%'
        )
        
        # Availability alerts
        self.add_alert_rule(
            'low_availability',
            'errors.availability_percent',
            99.0,
            'lt',
            AlertSeverity.CRITICAL,
            'Availability below 99%'
        )
        
        # Saturation alerts
        self.add_alert_rule(
            'high_cpu_usage',
            'saturation.cpu_percent',
            80.0,
            'gt',
            AlertSeverity.WARNING,
            'CPU usage above 80%'
        )
        
        self.add_alert_rule(
            'critical_cpu_usage',
            'saturation.cpu_percent',
            95.0,
            'gt',
            AlertSeverity.CRITICAL,
            'CPU usage above 95%'
        )
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check all alert rules and return fired alerts"""
        golden_signals = self.monitor.calculate_golden_signals()
        fired_alerts = []
        
        for rule_name, rule in self.alert_rules.items():
            metric_value = self._get_nested_value(golden_signals, rule['metric_path'])
            
            if metric_value is None:
                continue
            
            alert_fired = False
            
            if rule['comparison'] == 'gt' and metric_value > rule['threshold']:
                alert_fired = True
            elif rule['comparison'] == 'lt' and metric_value < rule['threshold']:
                alert_fired = True
            elif rule['comparison'] == 'eq' and metric_value == rule['threshold']:
                alert_fired = True
            
            if alert_fired:
                alert = {
                    'rule_name': rule_name,
                    'severity': rule['severity'].value,
                    'description': rule['description'],
                    'metric_path': rule['metric_path'],
                    'current_value': metric_value,
                    'threshold': rule['threshold'],
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                fired_alerts.append(alert)
                self.alert_history.append(alert)
                
                # Update rule statistics
                rule['last_fired'] = datetime.utcnow()
                rule['fired_count'] += 1
        
        return fired_alerts
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in self.alert_history 
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
        
        severity_counts = defaultdict(int)
        rule_counts = defaultdict(int)
        
        for alert in recent_alerts:
            severity_counts[alert['severity']] += 1
            rule_counts[alert['rule_name']] += 1
        
        return {
            'time_window_hours': hours,
            'total_alerts': len(recent_alerts),
            'severity_breakdown': dict(severity_counts),
            'most_frequent_alerts': dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'recent_alerts': recent_alerts[-20:]  # Last 20 alerts
        }

# Example usage and demonstration
def demonstrate_metrics_system():
    """Demonstrate the comprehensive metrics system"""
    
    # Initialize components
    metrics_collector = MetricsCollector()
    golden_signals_monitor = GoldenSignalsMonitor(metrics_collector)
    business_tracker = BusinessMetricsTracker(metrics_collector)
    alerter = MetricsAlerter(golden_signals_monitor)
    
    # Configure SLOs and alerts
    golden_signals_monitor.configure_slos()
    alerter.configure_default_alerts()
    
    print("🚀 Starting Application Metrics & KPI Monitoring Demo")
    print("=" * 60)
    
    # Simulate application traffic
    print("\n📊 Simulating application traffic...")
    
    import random
    
    # Simulate 100 requests
    for i in range(100):
        # Random request parameters
        endpoints = ['/api/users', '/api/products', '/api/orders', '/api/payments']
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        
        endpoint = random.choice(endpoints)
        method = random.choice(methods)
        
        # Simulate different response characteristics
        if endpoint == '/api/payments':
            # Payment endpoints are slower and occasionally fail
            duration_ms = random.normalvariate(300, 100)  # 300ms avg
            status_code = random.choices([200, 500], weights=[95, 5])[0]  # 5% error rate
        elif endpoint == '/api/orders':
            duration_ms = random.normalvariate(150, 50)   # 150ms avg
            status_code = random.choices([200, 201, 400, 500], weights=[85, 10, 3, 2])[0]
        else:
            duration_ms = random.normalvariate(80, 30)    # 80ms avg
            status_code = random.choices([200, 404, 500], weights=[95, 4, 1])[0]
        
        duration_ms = max(10, duration_ms)  # Minimum 10ms
        user_id = f"user_{random.randint(1, 50)}"
        
        # Track the request
        golden_signals_monitor.track_request(endpoint, method, status_code, duration_ms, user_id)
        
        # Track business activities
        if endpoint == '/api/orders' and status_code in [200, 201]:
            business_tracker.track_business_transaction('purchase', random.uniform(10, 500), 'USD', user_id)
            business_tracker.track_conversion_funnel('purchase', user_id)
        
        if endpoint == '/api/users' and method == 'POST':
            business_tracker.track_conversion_funnel('signup', user_id)
        
        business_tracker.track_user_activity(user_id, endpoint.split('/')[-1])
        business_tracker.track_feature_usage(endpoint.split('/')[-1], user_id)
    
    # Simulate system resource metrics
    for i in range(10):
        cpu = random.uniform(30, 90)
        memory = random.uniform(40, 80)
        disk = random.uniform(20, 70)
        connections = random.randint(50, 200)
        
        golden_signals_monitor.track_saturation_metrics(cpu, memory, disk, connections)
        time.sleep(0.1)
    
    print("✅ Generated 100 requests and system metrics")
    
    # Calculate and display golden signals
    print("\n🎯 Golden Signals Analysis:")
    print("-" * 30)
    
    golden_signals = golden_signals_monitor.calculate_golden_signals()
    
    print(f"Latency:")
    print(f"  P95: {golden_signals['latency']['p95_ms']:.1f}ms")
    print(f"  P99: {golden_signals['latency']['p99_ms']:.1f}ms")
    print(f"  SLO Compliance: {'✅' if golden_signals['latency']['slo_compliance'] else '❌'}")
    
    print(f"\nTraffic:")
    print(f"  Requests/sec: {golden_signals['traffic']['requests_per_second']:.2f}")
    print(f"  Requests/min: {golden_signals['traffic']['requests_per_minute']:.1f}")
    
    print(f"\nErrors:")
    print(f"  Error Rate: {golden_signals['errors']['error_rate_percent']:.2f}%")
    print(f"  Availability: {golden_signals['errors']['availability_percent']:.2f}%")
    print(f"  SLO Compliance: {'✅' if golden_signals['errors']['slo_compliance'] else '❌'}")
    
    print(f"\nSaturation:")
    print(f"  CPU: {golden_signals['saturation']['cpu_percent']:.1f}%")
    print(f"  Memory: {golden_signals['saturation']['memory_percent']:.1f}%")
    print(f"  Disk: {golden_signals['saturation']['disk_percent']:.1f}%")
    print(f"  SLO Compliance: {'✅' if golden_signals['saturation']['slo_compliance'] else '❌'}")
    
    # Business KPIs
    print("\n💼 Business KPIs Analysis:")
    print("-" * 25)
    
    business_kpis = business_tracker.calculate_business_kpis()
    
    print(f"Revenue:")
    print(f"  Revenue/hour: ${business_kpis['revenue']['revenue_per_hour']:.2f}")
    print(f"  Est. daily revenue: ${business_kpis['revenue']['estimated_daily_revenue']:.2f}")
    
    print(f"\nTransactions:")
    print(f"  Transactions/min: {business_kpis['transactions']['transactions_per_minute']:.1f}")
    
    print(f"\nUser Engagement:")
    print(f"  Actions/min: {business_kpis['user_engagement']['user_actions_per_minute']:.1f}")
    print(f"  Feature usage/min: {business_kpis['user_engagement']['feature_usage_per_minute']:.1f}")
    
    print(f"\nConversion Funnel:")
    print(f"  Landing → Signup: {business_kpis['conversion_funnel']['landing_to_signup_percent']:.1f}%")
    print(f"  Signup → Trial: {business_kpis['conversion_funnel']['signup_to_trial_percent']:.1f}%")
    print(f"  Trial → Purchase: {business_kpis['conversion_funnel']['trial_to_purchase_percent']:.1f}%")
    print(f"  Overall Conversion: {business_kpis['conversion_funnel']['overall_conversion_percent']:.1f}%")
    
    # SLO Compliance
    print("\n📋 SLO Compliance Report:")
    print("-" * 25)
    
    slo_compliance = golden_signals_monitor.check_slo_compliance()
    
    for slo_name, compliance_data in slo_compliance.items():
        compliance_icon = "✅" if compliance_data['compliant'] else "❌"
        print(f"{slo_name.replace('_', ' ').title()}: {compliance_icon}")
        print(f"  Target: {compliance_data['slo']}")
        print(f"  Current: {compliance_data['current']:.2f}")
        
        if 'error_budget_remaining_minutes' in compliance_data:
            print(f"  Error Budget Used: {compliance_data['error_budget_used_percent']:.1f}%")
            print(f"  Error Budget Remaining: {compliance_data['error_budget_remaining_minutes']:.1f} minutes")
    
    # Check alerts
    print("\n🚨 Alert Status:")
    print("-" * 15)
    
    fired_alerts = alerter.check_alerts()
    
    if fired_alerts:
        for alert in fired_alerts:
            severity_icon = {"warning": "⚠️", "critical": "🚨", "info": "ℹ️"}.get(alert['severity'], "🔔")
            print(f"{severity_icon} {alert['rule_name']}: {alert['description']}")
            print(f"   Current: {alert['current_value']:.2f}, Threshold: {alert['threshold']}")
    else:
        print("✅ No alerts fired - system healthy")
    
    # Alert summary
    alert_summary = alerter.get_alert_summary(hours=1)
    print(f"\nAlert Summary (last hour):")
    print(f"  Total alerts: {alert_summary['total_alerts']}")
    print(f"  By severity: {alert_summary['severity_breakdown']}")

if __name__ == "__main__":
    demonstrate_metrics_system()
```

This comprehensive application metrics and KPIs system provides enterprise-grade monitoring capabilities essential for maintaining optimal application performance, tracking business outcomes, and ensuring SLO compliance in production environments.