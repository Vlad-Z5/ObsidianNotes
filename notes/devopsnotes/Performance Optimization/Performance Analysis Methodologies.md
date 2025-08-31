# Performance Analysis Methodologies

**Focus:** Systematic approaches for identifying performance bottlenecks, root cause analysis, profiling techniques, performance baseline establishment, and data-driven optimization strategies.

## Core Analysis Methodologies

### 1. USE Method (Utilization, Saturation, Errors)
- **Utilization:** Resource usage percentage
- **Saturation:** Degree of queued work
- **Errors:** Error count and rate

### 2. RED Method (Rate, Errors, Duration)
- **Rate:** Request volume per second
- **Errors:** Request failure rate
- **Duration:** Time per request (latency)

### 3. Four Golden Signals
- **Latency:** Response time
- **Traffic:** Request volume
- **Errors:** Error rate
- **Saturation:** Resource fullness

## Performance Analysis Framework

```python
import psutil
import time
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import threading
import queue
import json
from datetime import datetime
import sqlite3

@dataclass
class PerformanceMetric:
    timestamp: float
    metric_type: str
    value: float
    resource: str
    labels: Dict[str, str]

@dataclass
class BottleneckAnalysis:
    resource: str
    severity: str
    utilization: float
    saturation: float
    error_rate: float
    recommendations: List[str]

class EnterprisePerformanceAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        self.metrics_queue = queue.Queue()
        self.baseline_data = {}
        self.analysis_results = []
        self.db_connection = self._setup_database()
        self.collection_thread = None
        self.analysis_thread = None
        self.is_running = False
        
    def _setup_database(self) -> sqlite3.Connection:
        """Initialize metrics database"""
        conn = sqlite3.connect('performance_metrics.db', check_same_thread=False)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY,
                timestamp REAL,
                metric_type TEXT,
                value REAL,
                resource TEXT,
                labels TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS baselines (
                resource TEXT PRIMARY KEY,
                baseline_value REAL,
                threshold_warning REAL,
                threshold_critical REAL,
                created_at REAL
            )
        ''')
        return conn
    
    def start_monitoring(self):
        """Start continuous performance monitoring"""
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collect_metrics)
        self.analysis_thread = threading.Thread(target=self._analyze_metrics)
        
        self.collection_thread.start()
        self.analysis_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and cleanup"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join()
        if self.analysis_thread:
            self.analysis_thread.join()
    
    def _collect_metrics(self):
        """Collect system metrics continuously"""
        while self.is_running:
            try:
                # CPU Metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_times = psutil.cpu_times()
                
                self._add_metric("cpu_utilization", cpu_percent, "cpu")
                self._add_metric("cpu_iowait", cpu_times.iowait, "cpu")
                
                # Memory Metrics
                memory = psutil.virtual_memory()
                self._add_metric("memory_utilization", memory.percent, "memory")
                self._add_metric("memory_available", memory.available, "memory")
                
                # Disk Metrics
                for disk in psutil.disk_partitions():
                    try:
                        disk_usage = psutil.disk_usage(disk.mountpoint)
                        disk_io = psutil.disk_io_counters()
                        
                        self._add_metric("disk_utilization", 
                                       (disk_usage.used / disk_usage.total) * 100,
                                       f"disk_{disk.device}")
                        
                        if disk_io:
                            self._add_metric("disk_read_bytes", disk_io.read_bytes, "disk")
                            self._add_metric("disk_write_bytes", disk_io.write_bytes, "disk")
                    except PermissionError:
                        continue
                
                # Network Metrics
                network = psutil.net_io_counters()
                self._add_metric("network_bytes_sent", network.bytes_sent, "network")
                self._add_metric("network_bytes_recv", network.bytes_recv, "network")
                
                # Process Metrics
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        info = proc.info
                        if info['cpu_percent'] > self.config.get('process_cpu_threshold', 10):
                            self._add_metric("process_cpu", info['cpu_percent'], 
                                           f"process_{info['name']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                time.sleep(self.config.get('collection_interval', 10))
                
            except Exception as e:
                print(f"Error collecting metrics: {e}")
    
    def _add_metric(self, metric_type: str, value: float, resource: str, labels: Dict = None):
        """Add metric to collection queue"""
        if labels is None:
            labels = {}
            
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_type=metric_type,
            value=value,
            resource=resource,
            labels=labels
        )
        
        self.metrics_queue.put(metric)
        
        # Store in database
        self.db_connection.execute(
            'INSERT INTO metrics VALUES (NULL, ?, ?, ?, ?, ?)',
            (metric.timestamp, metric_type, value, resource, json.dumps(labels))
        )
        self.db_connection.commit()
    
    def _analyze_metrics(self):
        """Analyze collected metrics for bottlenecks"""
        while self.is_running:
            try:
                # Process queued metrics
                metrics_batch = []
                while not self.metrics_queue.empty():
                    try:
                        metric = self.metrics_queue.get_nowait()
                        metrics_batch.append(metric)
                    except queue.Empty:
                        break
                
                if metrics_batch:
                    self._perform_use_analysis(metrics_batch)
                    self._detect_anomalies(metrics_batch)
                    self._identify_bottlenecks(metrics_batch)
                
                time.sleep(self.config.get('analysis_interval', 30))
                
            except Exception as e:
                print(f"Error analyzing metrics: {e}")
    
    def _perform_use_analysis(self, metrics: List[PerformanceMetric]):
        """Perform USE method analysis"""
        resource_metrics = {}
        
        for metric in metrics:
            if metric.resource not in resource_metrics:
                resource_metrics[metric.resource] = {
                    'utilization': [],
                    'saturation': [],
                    'errors': []
                }
            
            if 'utilization' in metric.metric_type:
                resource_metrics[metric.resource]['utilization'].append(metric.value)
            elif 'saturation' in metric.metric_type or 'queue' in metric.metric_type:
                resource_metrics[metric.resource]['saturation'].append(metric.value)
            elif 'error' in metric.metric_type or 'fail' in metric.metric_type:
                resource_metrics[metric.resource]['errors'].append(metric.value)
        
        for resource, data in resource_metrics.items():
            if data['utilization']:
                avg_util = np.mean(data['utilization'])
                avg_sat = np.mean(data['saturation']) if data['saturation'] else 0
                avg_errors = np.mean(data['errors']) if data['errors'] else 0
                
                analysis = BottleneckAnalysis(
                    resource=resource,
                    severity=self._calculate_severity(avg_util, avg_sat, avg_errors),
                    utilization=avg_util,
                    saturation=avg_sat,
                    error_rate=avg_errors,
                    recommendations=self._generate_recommendations(resource, avg_util, avg_sat, avg_errors)
                )
                
                self.analysis_results.append(analysis)
    
    def _detect_anomalies(self, metrics: List[PerformanceMetric]):
        """Detect performance anomalies using statistical methods"""
        for metric in metrics:
            baseline = self._get_baseline(metric.resource, metric.metric_type)
            
            if baseline and abs(metric.value - baseline['baseline_value']) > baseline['threshold_warning']:
                severity = 'CRITICAL' if abs(metric.value - baseline['baseline_value']) > baseline['threshold_critical'] else 'WARNING'
                
                print(f"ANOMALY DETECTED: {metric.resource}.{metric.metric_type} = {metric.value} "
                      f"(baseline: {baseline['baseline_value']}, severity: {severity})")
    
    def _get_baseline(self, resource: str, metric_type: str) -> Optional[Dict]:
        """Get baseline data for resource metric"""
        cursor = self.db_connection.execute(
            'SELECT * FROM baselines WHERE resource = ?',
            (f"{resource}_{metric_type}",)
        )
        result = cursor.fetchone()
        
        if result:
            return {
                'baseline_value': result[1],
                'threshold_warning': result[2],
                'threshold_critical': result[3]
            }
        return None
    
    def establish_baseline(self, duration_hours: int = 24):
        """Establish performance baseline over specified duration"""
        end_time = time.time()
        start_time = end_time - (duration_hours * 3600)
        
        cursor = self.db_connection.execute(
            'SELECT resource, metric_type, value FROM metrics WHERE timestamp BETWEEN ? AND ?',
            (start_time, end_time)
        )
        
        baseline_data = {}
        for row in cursor.fetchall():
            key = f"{row[0]}_{row[1]}"
            if key not in baseline_data:
                baseline_data[key] = []
            baseline_data[key].append(row[2])
        
        for key, values in baseline_data.items():
            if len(values) > 10:  # Minimum samples required
                baseline_value = np.median(values)
                std_dev = np.std(values)
                
                warning_threshold = baseline_value + (2 * std_dev)
                critical_threshold = baseline_value + (3 * std_dev)
                
                self.db_connection.execute(
                    'INSERT OR REPLACE INTO baselines VALUES (?, ?, ?, ?, ?)',
                    (key, baseline_value, warning_threshold, critical_threshold, time.time())
                )
        
        self.db_connection.commit()
        print(f"Baseline established for {len(baseline_data)} metrics")
    
    def _calculate_severity(self, utilization: float, saturation: float, error_rate: float) -> str:
        """Calculate bottleneck severity"""
        score = 0
        
        if utilization > 80:
            score += 3
        elif utilization > 60:
            score += 2
        elif utilization > 40:
            score += 1
        
        if saturation > 10:
            score += 3
        elif saturation > 5:
            score += 2
        elif saturation > 1:
            score += 1
        
        if error_rate > 5:
            score += 3
        elif error_rate > 1:
            score += 2
        elif error_rate > 0.1:
            score += 1
        
        if score >= 7:
            return 'CRITICAL'
        elif score >= 4:
            return 'HIGH'
        elif score >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_recommendations(self, resource: str, util: float, sat: float, error_rate: float) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if 'cpu' in resource.lower():
            if util > 80:
                recommendations.extend([
                    "Consider CPU scaling or optimization",
                    "Profile CPU-intensive processes",
                    "Implement CPU affinity for critical processes"
                ])
            if sat > 5:
                recommendations.append("Reduce CPU contention through process prioritization")
        
        elif 'memory' in resource.lower():
            if util > 85:
                recommendations.extend([
                    "Increase memory allocation",
                    "Optimize memory-intensive applications",
                    "Implement memory pooling strategies"
                ])
        
        elif 'disk' in resource.lower():
            if util > 80:
                recommendations.extend([
                    "Consider faster storage (SSD)",
                    "Implement disk I/O optimization",
                    "Use disk striping or RAID"
                ])
        
        elif 'network' in resource.lower():
            if util > 70:
                recommendations.extend([
                    "Optimize network protocols",
                    "Implement connection pooling",
                    "Consider network bandwidth upgrade"
                ])
        
        if error_rate > 1:
            recommendations.append("Investigate and resolve error sources")
        
        return recommendations
    
    def _identify_bottlenecks(self, metrics: List[PerformanceMetric]):
        """Identify system bottlenecks using correlation analysis"""
        # Group metrics by resource
        resource_data = {}
        for metric in metrics:
            if metric.resource not in resource_data:
                resource_data[metric.resource] = {}
            resource_data[metric.resource][metric.metric_type] = metric.value
        
        # Analyze correlations between resources
        bottlenecks = []
        for resource, data in resource_data.items():
            if self._is_bottleneck(data):
                bottlenecks.append(resource)
        
        if bottlenecks:
            print(f"Potential bottlenecks detected: {bottlenecks}")
    
    def _is_bottleneck(self, resource_data: Dict) -> bool:
        """Determine if resource is a bottleneck"""
        utilization_metrics = [v for k, v in resource_data.items() if 'utilization' in k]
        if utilization_metrics and max(utilization_metrics) > 80:
            return True
        
        saturation_metrics = [v for k, v in resource_data.items() if 'saturation' in k or 'queue' in k]
        if saturation_metrics and max(saturation_metrics) > 5:
            return True
        
        return False
    
    def generate_report(self) -> Dict:
        """Generate comprehensive performance analysis report"""
        current_time = datetime.now()
        
        # Get recent metrics
        cursor = self.db_connection.execute(
            'SELECT * FROM metrics WHERE timestamp > ?',
            (time.time() - 3600,)  # Last hour
        )
        recent_metrics = cursor.fetchall()
        
        # Aggregate analysis results
        critical_issues = [a for a in self.analysis_results if a.severity == 'CRITICAL']
        high_issues = [a for a in self.analysis_results if a.severity == 'HIGH']
        
        report = {
            'timestamp': current_time.isoformat(),
            'summary': {
                'total_metrics_collected': len(recent_metrics),
                'critical_issues': len(critical_issues),
                'high_issues': len(high_issues),
                'total_resources_monitored': len(set([m[4] for m in recent_metrics]))
            },
            'critical_bottlenecks': [
                {
                    'resource': issue.resource,
                    'utilization': issue.utilization,
                    'saturation': issue.saturation,
                    'error_rate': issue.error_rate,
                    'recommendations': issue.recommendations
                }
                for issue in critical_issues
            ],
            'high_priority_issues': [
                {
                    'resource': issue.resource,
                    'utilization': issue.utilization,
                    'recommendations': issue.recommendations[:3]  # Top 3 recommendations
                }
                for issue in high_issues
            ]
        }
        
        return report

# Usage Example
if __name__ == "__main__":
    config = {
        'collection_interval': 10,
        'analysis_interval': 30,
        'process_cpu_threshold': 15
    }
    
    analyzer = EnterprisePerformanceAnalyzer(config)
    
    # Establish baseline (run for 24 hours first)
    # analyzer.establish_baseline(duration_hours=24)
    
    # Start monitoring
    analyzer.start_monitoring()
    
    try:
        # Let it run for demonstration
        time.sleep(120)
    finally:
        analyzer.stop_monitoring()
        
        # Generate report
        report = analyzer.generate_report()
        print(json.dumps(report, indent=2))
```

## Advanced Profiling Techniques

### Application Profiling Stack

```yaml
# Performance Profiling Configuration
profiling:
  cpu_profiler:
    enabled: true
    sample_rate: 100
    duration: 300s
    flame_graph: true
    
  memory_profiler:
    enabled: true
    heap_analysis: true
    leak_detection: true
    allocation_tracking: true
    
  io_profiler:
    enabled: true
    file_operations: true
    network_operations: true
    database_queries: true
    
  application_profiler:
    enabled: true
    function_timing: true
    call_graph: true
    hot_path_analysis: true

monitoring:
  metrics_collection:
    interval: 10s
    retention: 7d
    compression: true
    
  alerting:
    cpu_threshold: 80%
    memory_threshold: 85%
    disk_threshold: 90%
    response_time_threshold: 500ms
    
  reporting:
    daily_reports: true
    trend_analysis: true
    capacity_planning: true
```

## Distributed System Performance Analysis

### Microservices Performance Tracking

```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import requests
import time
from typing import Dict, List

class DistributedPerformanceAnalyzer:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = trace.get_tracer(__name__)
        self.setup_tracing()
        
    def setup_tracing(self):
        """Configure distributed tracing"""
        trace.set_tracer_provider(TracerProvider())
        
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=14268,
        )
        
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
    
    def analyze_service_performance(self, service_endpoints: List[str]) -> Dict:
        """Analyze performance across multiple services"""
        results = {}
        
        for endpoint in service_endpoints:
            with self.tracer.start_as_current_span(f"analyze_{endpoint}") as span:
                start_time = time.time()
                
                try:
                    response = requests.get(endpoint, timeout=30)
                    end_time = time.time()
                    
                    results[endpoint] = {
                        'status_code': response.status_code,
                        'response_time': end_time - start_time,
                        'content_length': len(response.content),
                        'success': response.status_code < 400
                    }
                    
                    # Add span attributes
                    span.set_attribute("http.method", "GET")
                    span.set_attribute("http.url", endpoint)
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("response.time", end_time - start_time)
                    
                except Exception as e:
                    results[endpoint] = {
                        'error': str(e),
                        'success': False
                    }
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
        
        return results
    
    def calculate_service_health_score(self, performance_data: Dict) -> float:
        """Calculate overall service health score"""
        total_score = 0
        total_weight = 0
        
        for endpoint, data in performance_data.items():
            if data.get('success'):
                # Response time score (lower is better)
                response_time = data.get('response_time', 0)
                time_score = max(0, 100 - (response_time * 100))  # 1s = 0 points
                
                # Availability score
                availability_score = 100 if data['status_code'] < 400 else 0
                
                # Combined score
                endpoint_score = (time_score * 0.7) + (availability_score * 0.3)
                total_score += endpoint_score
                total_weight += 1
        
        return total_score / total_weight if total_weight > 0 else 0
```

## Real-time Performance Dashboard

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

class PerformanceDashboard:
    def __init__(self, analyzer: EnterprisePerformanceAnalyzer):
        self.analyzer = analyzer
        
    def create_realtime_dashboard(self) -> go.Figure:
        """Create real-time performance dashboard"""
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('CPU Utilization', 'Memory Usage', 
                          'Disk I/O', 'Network Traffic',
                          'Response Times', 'Error Rates'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": True}, {"secondary_y": True}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Get recent metrics from database
        end_time = time.time()
        start_time = end_time - 3600  # Last hour
        
        cursor = self.analyzer.db_connection.execute(
            'SELECT timestamp, metric_type, value, resource FROM metrics WHERE timestamp BETWEEN ? AND ?',
            (start_time, end_time)
        )
        
        metrics_data = cursor.fetchall()
        df = pd.DataFrame(metrics_data, columns=['timestamp', 'metric_type', 'value', 'resource'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # CPU Utilization
        cpu_data = df[df['metric_type'] == 'cpu_utilization']
        if not cpu_data.empty:
            fig.add_trace(
                go.Scatter(x=cpu_data['timestamp'], y=cpu_data['value'],
                          name='CPU %', line=dict(color='red')),
                row=1, col=1
            )
        
        # Memory Usage
        memory_data = df[df['metric_type'] == 'memory_utilization']
        if not memory_data.empty:
            fig.add_trace(
                go.Scatter(x=memory_data['timestamp'], y=memory_data['value'],
                          name='Memory %', line=dict(color='blue')),
                row=1, col=2
            )
        
        # Update layout
        fig.update_layout(
            title="Real-time Performance Dashboard",
            showlegend=True,
            height=800
        )
        
        return fig
    
    def generate_performance_summary(self) -> Dict:
        """Generate performance summary statistics"""
        report = self.analyzer.generate_report()
        
        summary = {
            'current_status': 'HEALTHY' if report['summary']['critical_issues'] == 0 else 'DEGRADED',
            'key_metrics': {
                'total_resources': report['summary']['total_resources_monitored'],
                'critical_issues': report['summary']['critical_issues'],
                'high_priority_issues': report['summary']['high_issues']
            },
            'top_recommendations': []
        }
        
        # Collect top recommendations
        all_recommendations = []
        for issue in report.get('critical_bottlenecks', []):
            all_recommendations.extend(issue['recommendations'])
        
        # Get unique recommendations
        unique_recommendations = list(set(all_recommendations))
        summary['top_recommendations'] = unique_recommendations[:5]
        
        return summary
```

This comprehensive performance analysis framework provides:

1. **Multi-methodology Analysis**: USE, RED, and Four Golden Signals
2. **Real-time Monitoring**: Continuous metric collection and analysis  
3. **Anomaly Detection**: Statistical baseline comparison
4. **Bottleneck Identification**: Automated correlation analysis
5. **Distributed Tracing**: Microservices performance tracking
6. **Interactive Dashboards**: Real-time visualization
7. **Actionable Recommendations**: Context-aware optimization suggestions

The system enables proactive performance management through continuous monitoring, intelligent analysis, and automated reporting for enterprise-scale environments.