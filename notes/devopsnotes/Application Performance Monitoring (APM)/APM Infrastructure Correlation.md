# APM Infrastructure Correlation

Infrastructure correlation in APM connects application performance metrics with underlying infrastructure health, enabling holistic visibility across the technology stack. This guide covers infrastructure monitoring integration, correlation algorithms, root cause analysis, and enterprise-grade implementations that link application performance issues to infrastructure problems.

## Infrastructure Correlation Framework

### Multi-Layer Monitoring Integration

```python
import time
import threading
import psutil
import docker
import kubernetes
import requests
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import logging
from enum import Enum

class LayerType(Enum):
    APPLICATION = "application"
    CONTAINER = "container"
    KUBERNETES = "kubernetes"
    HOST = "host"
    NETWORK = "network"
    STORAGE = "storage"

class CorrelationStrength(Enum):
    STRONG = "strong"      # >0.8 correlation
    MODERATE = "moderate"  # 0.5-0.8 correlation
    WEAK = "weak"         # 0.2-0.5 correlation
    NONE = "none"         # <0.2 correlation

@dataclass
class InfrastructureMetric:
    layer: LayerType
    component: str
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class ApplicationMetric:
    service: str
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class Correlation:
    app_metric: str
    infra_metric: str
    app_component: str
    infra_component: str
    correlation_coefficient: float
    strength: CorrelationStrength
    confidence: float
    samples: int
    time_window: timedelta

class InfrastructureCollector:
    """Collect infrastructure metrics from multiple layers"""
    
    def __init__(self):
        self.docker_client = None
        self.k8s_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize infrastructure clients"""
        try:
            self.docker_client = docker.from_env()
        except:
            logging.warning("Docker client not available")
        
        try:
            kubernetes.config.load_incluster_config()
            self.k8s_client = kubernetes.client.ApiClient()
        except:
            try:
                kubernetes.config.load_kube_config()
                self.k8s_client = kubernetes.client.ApiClient()
            except:
                logging.warning("Kubernetes client not available")
    
    def collect_host_metrics(self) -> List[InfrastructureMetric]:
        """Collect host-level infrastructure metrics"""
        metrics = []
        timestamp = datetime.utcnow()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        load_avg = psutil.getloadavg()
        
        metrics.extend([
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="cpu",
                metric_name="cpu_utilization_percent",
                value=cpu_percent,
                unit="percent",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="cpu",
                metric_name="cpu_count",
                value=cpu_count,
                unit="count",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="cpu",
                metric_name="load_average_1m",
                value=load_avg[0],
                unit="load",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="cpu",
                metric_name="load_average_5m",
                value=load_avg[1],
                unit="load",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="cpu",
                metric_name="load_average_15m",
                value=load_avg[2],
                unit="load",
                timestamp=timestamp
            )
        ])
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        metrics.extend([
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="memory",
                metric_name="memory_utilization_percent",
                value=memory.percent,
                unit="percent",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="memory",
                metric_name="memory_available_bytes",
                value=memory.available,
                unit="bytes",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="memory",
                metric_name="memory_total_bytes",
                value=memory.total,
                unit="bytes",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="memory",
                metric_name="swap_utilization_percent",
                value=swap.percent,
                unit="percent",
                timestamp=timestamp
            )
        ])
        
        # Disk metrics
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        metrics.extend([
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="disk",
                metric_name="disk_utilization_percent",
                value=(disk_usage.used / disk_usage.total) * 100,
                unit="percent",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="disk",
                metric_name="disk_free_bytes",
                value=disk_usage.free,
                unit="bytes",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="disk",
                metric_name="disk_io_read_bytes",
                value=disk_io.read_bytes,
                unit="bytes",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="disk",
                metric_name="disk_io_write_bytes",
                value=disk_io.write_bytes,
                unit="bytes",
                timestamp=timestamp
            )
        ])
        
        # Network metrics
        network_io = psutil.net_io_counters()
        network_connections = len(psutil.net_connections())
        
        metrics.extend([
            InfrastructureMetric(
                layer=LayerType.NETWORK,
                component="interface",
                metric_name="network_bytes_sent",
                value=network_io.bytes_sent,
                unit="bytes",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.NETWORK,
                component="interface",
                metric_name="network_bytes_recv",
                value=network_io.bytes_recv,
                unit="bytes",
                timestamp=timestamp
            ),
            InfrastructureMetric(
                layer=LayerType.NETWORK,
                component="interface",
                metric_name="network_connections",
                value=network_connections,
                unit="count",
                timestamp=timestamp
            )
        ])
        
        return metrics
    
    def collect_container_metrics(self) -> List[InfrastructureMetric]:
        """Collect Docker container metrics"""
        metrics = []
        
        if not self.docker_client:
            return metrics
        
        timestamp = datetime.utcnow()
        
        try:
            containers = self.docker_client.containers.list()
            
            for container in containers:
                try:
                    stats = container.stats(stream=False)
                    
                    # CPU metrics
                    cpu_stats = stats.get('cpu_stats', {})
                    precpu_stats = stats.get('precpu_stats', {})
                    
                    if cpu_stats and precpu_stats:
                        cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                        system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
                        
                        if system_delta > 0:
                            cpu_percent = (cpu_delta / system_delta) * len(cpu_stats['cpu_usage'].get('percpu_usage', [])) * 100
                            
                            metrics.append(InfrastructureMetric(
                                layer=LayerType.CONTAINER,
                                component=container.name,
                                metric_name="cpu_utilization_percent",
                                value=cpu_percent,
                                unit="percent",
                                timestamp=timestamp,
                                tags={"container_id": container.id[:12]}
                            ))
                    
                    # Memory metrics
                    memory_stats = stats.get('memory_stats', {})
                    if memory_stats:
                        memory_usage = memory_stats.get('usage', 0)
                        memory_limit = memory_stats.get('limit', 0)
                        
                        if memory_limit > 0:
                            memory_percent = (memory_usage / memory_limit) * 100
                            
                            metrics.extend([
                                InfrastructureMetric(
                                    layer=LayerType.CONTAINER,
                                    component=container.name,
                                    metric_name="memory_utilization_percent",
                                    value=memory_percent,
                                    unit="percent",
                                    timestamp=timestamp,
                                    tags={"container_id": container.id[:12]}
                                ),
                                InfrastructureMetric(
                                    layer=LayerType.CONTAINER,
                                    component=container.name,
                                    metric_name="memory_usage_bytes",
                                    value=memory_usage,
                                    unit="bytes",
                                    timestamp=timestamp,
                                    tags={"container_id": container.id[:12]}
                                )
                            ])
                    
                    # Network metrics
                    networks = stats.get('networks', {})
                    total_rx_bytes = 0
                    total_tx_bytes = 0
                    
                    for interface, net_stats in networks.items():
                        total_rx_bytes += net_stats.get('rx_bytes', 0)
                        total_tx_bytes += net_stats.get('tx_bytes', 0)
                    
                    metrics.extend([
                        InfrastructureMetric(
                            layer=LayerType.CONTAINER,
                            component=container.name,
                            metric_name="network_rx_bytes",
                            value=total_rx_bytes,
                            unit="bytes",
                            timestamp=timestamp,
                            tags={"container_id": container.id[:12]}
                        ),
                        InfrastructureMetric(
                            layer=LayerType.CONTAINER,
                            component=container.name,
                            metric_name="network_tx_bytes",
                            value=total_tx_bytes,
                            unit="bytes",
                            timestamp=timestamp,
                            tags={"container_id": container.id[:12]}
                        )
                    ])
                    
                except Exception as e:
                    logging.warning(f"Error collecting stats for container {container.name}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error collecting container metrics: {e}")
        
        return metrics
    
    def collect_kubernetes_metrics(self) -> List[InfrastructureMetric]:
        """Collect Kubernetes cluster metrics"""
        metrics = []
        
        if not self.k8s_client:
            return metrics
        
        timestamp = datetime.utcnow()
        
        try:
            # Get API instances
            v1 = kubernetes.client.CoreV1Api(self.k8s_client)
            apps_v1 = kubernetes.client.AppsV1Api(self.k8s_client)
            
            # Pod metrics
            pods = v1.list_pod_for_all_namespaces()
            pod_phases = defaultdict(int)
            
            for pod in pods.items:
                pod_phases[pod.status.phase] += 1
                
                # Pod resource requests/limits
                for container in pod.spec.containers:
                    if container.resources:
                        requests = container.resources.requests or {}
                        limits = container.resources.limits or {}
                        
                        if 'cpu' in requests:
                            cpu_request = self._parse_cpu_value(requests['cpu'])
                            metrics.append(InfrastructureMetric(
                                layer=LayerType.KUBERNETES,
                                component=f"pod/{pod.metadata.name}",
                                metric_name="cpu_request",
                                value=cpu_request,
                                unit="cores",
                                timestamp=timestamp,
                                tags={
                                    "namespace": pod.metadata.namespace,
                                    "container": container.name
                                }
                            ))
                        
                        if 'memory' in requests:
                            memory_request = self._parse_memory_value(requests['memory'])
                            metrics.append(InfrastructureMetric(
                                layer=LayerType.KUBERNETES,
                                component=f"pod/{pod.metadata.name}",
                                metric_name="memory_request_bytes",
                                value=memory_request,
                                unit="bytes",
                                timestamp=timestamp,
                                tags={
                                    "namespace": pod.metadata.namespace,
                                    "container": container.name
                                }
                            ))
            
            # Add pod phase counts
            for phase, count in pod_phases.items():
                metrics.append(InfrastructureMetric(
                    layer=LayerType.KUBERNETES,
                    component="cluster",
                    metric_name=f"pods_{phase.lower()}",
                    value=count,
                    unit="count",
                    timestamp=timestamp
                ))
            
            # Node metrics
            nodes = v1.list_node()
            ready_nodes = 0
            total_capacity = {"cpu": 0, "memory": 0}
            
            for node in nodes.items:
                # Check node readiness
                for condition in node.status.conditions or []:
                    if condition.type == "Ready" and condition.status == "True":
                        ready_nodes += 1
                        break
                
                # Add node capacity
                if node.status.capacity:
                    cpu_capacity = self._parse_cpu_value(node.status.capacity.get('cpu', '0'))
                    memory_capacity = self._parse_memory_value(node.status.capacity.get('memory', '0'))
                    
                    total_capacity["cpu"] += cpu_capacity
                    total_capacity["memory"] += memory_capacity
            
            metrics.extend([
                InfrastructureMetric(
                    layer=LayerType.KUBERNETES,
                    component="cluster",
                    metric_name="nodes_ready",
                    value=ready_nodes,
                    unit="count",
                    timestamp=timestamp
                ),
                InfrastructureMetric(
                    layer=LayerType.KUBERNETES,
                    component="cluster",
                    metric_name="nodes_total",
                    value=len(nodes.items),
                    unit="count",
                    timestamp=timestamp
                ),
                InfrastructureMetric(
                    layer=LayerType.KUBERNETES,
                    component="cluster",
                    metric_name="cpu_capacity_total",
                    value=total_capacity["cpu"],
                    unit="cores",
                    timestamp=timestamp
                ),
                InfrastructureMetric(
                    layer=LayerType.KUBERNETES,
                    component="cluster",
                    metric_name="memory_capacity_total",
                    value=total_capacity["memory"],
                    unit="bytes",
                    timestamp=timestamp
                )
            ])
            
        except Exception as e:
            logging.error(f"Error collecting Kubernetes metrics: {e}")
        
        return metrics
    
    def _parse_cpu_value(self, cpu_str: str) -> float:
        """Parse Kubernetes CPU value to cores"""
        if not cpu_str:
            return 0.0
        
        cpu_str = cpu_str.lower()
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000  # milicores to cores
        else:
            return float(cpu_str)
    
    def _parse_memory_value(self, memory_str: str) -> float:
        """Parse Kubernetes memory value to bytes"""
        if not memory_str:
            return 0.0
        
        memory_str = memory_str.upper()
        multipliers = {
            'K': 1024, 'KI': 1024,
            'M': 1024**2, 'MI': 1024**2,
            'G': 1024**3, 'GI': 1024**3,
            'T': 1024**4, 'TI': 1024**4
        }
        
        for suffix, multiplier in multipliers.items():
            if memory_str.endswith(suffix):
                return float(memory_str[:-len(suffix)]) * multiplier
        
        return float(memory_str)

class CorrelationAnalyzer:
    """Analyze correlations between application and infrastructure metrics"""
    
    def __init__(self, time_window_minutes: int = 30):
        self.time_window = timedelta(minutes=time_window_minutes)
        self.app_metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.infra_metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.correlations = {}
        self.lock = threading.Lock()
    
    def add_application_metric(self, metric: ApplicationMetric):
        """Add application metric to buffer"""
        with self.lock:
            key = f"{metric.service}:{metric.metric_name}"
            self.app_metrics_buffer[key].append((metric.timestamp, metric.value))
    
    def add_infrastructure_metric(self, metric: InfrastructureMetric):
        """Add infrastructure metric to buffer"""
        with self.lock:
            key = f"{metric.layer.value}:{metric.component}:{metric.metric_name}"
            self.infra_metrics_buffer[key].append((metric.timestamp, metric.value))
    
    def calculate_correlations(self) -> List[Correlation]:
        """Calculate correlations between application and infrastructure metrics"""
        correlations = []
        current_time = datetime.utcnow()
        cutoff_time = current_time - self.time_window
        
        with self.lock:
            # Get recent metrics
            recent_app_metrics = {}
            for key, metrics in self.app_metrics_buffer.items():
                recent_values = [(ts, val) for ts, val in metrics if ts > cutoff_time]
                if len(recent_values) >= 10:  # Minimum samples for correlation
                    recent_app_metrics[key] = recent_values
            
            recent_infra_metrics = {}
            for key, metrics in self.infra_metrics_buffer.items():
                recent_values = [(ts, val) for ts, val in metrics if ts > cutoff_time]
                if len(recent_values) >= 10:
                    recent_infra_metrics[key] = recent_values
        
        # Calculate correlations between all app and infra metric pairs
        for app_key, app_data in recent_app_metrics.items():
            for infra_key, infra_data in recent_infra_metrics.items():
                
                # Align timestamps (find common time points)
                aligned_data = self._align_time_series(app_data, infra_data)
                
                if len(aligned_data) >= 10:
                    app_values = [point[0] for point in aligned_data]
                    infra_values = [point[1] for point in aligned_data]
                    
                    # Calculate Pearson correlation coefficient
                    correlation_coeff = self._calculate_correlation(app_values, infra_values)
                    
                    if abs(correlation_coeff) >= 0.2:  # Only keep meaningful correlations
                        
                        # Determine correlation strength
                        strength = self._classify_correlation_strength(abs(correlation_coeff))
                        
                        # Calculate confidence based on sample size and consistency
                        confidence = min(len(aligned_data) / 100.0, 1.0) * abs(correlation_coeff)
                        
                        # Parse component names
                        app_service = app_key.split(':')[0]
                        app_metric = app_key.split(':')[1]
                        infra_component = infra_key.split(':')[1]
                        infra_metric = infra_key.split(':')[2]
                        
                        correlation = Correlation(
                            app_metric=app_metric,
                            infra_metric=infra_metric,
                            app_component=app_service,
                            infra_component=infra_component,
                            correlation_coefficient=correlation_coeff,
                            strength=strength,
                            confidence=confidence,
                            samples=len(aligned_data),
                            time_window=self.time_window
                        )
                        
                        correlations.append(correlation)
        
        # Sort by correlation strength and confidence
        correlations.sort(key=lambda c: (abs(c.correlation_coefficient), c.confidence), reverse=True)
        
        return correlations
    
    def _align_time_series(self, series1: List[Tuple], series2: List[Tuple], 
                          tolerance_seconds: int = 30) -> List[Tuple[float, float]]:
        """Align two time series within a tolerance window"""
        aligned = []
        tolerance = timedelta(seconds=tolerance_seconds)
        
        for ts1, val1 in series1:
            # Find closest timestamp in series2
            closest_match = None
            min_diff = float('inf')
            
            for ts2, val2 in series2:
                diff = abs((ts1 - ts2).total_seconds())
                if diff <= tolerance_seconds and diff < min_diff:
                    min_diff = diff
                    closest_match = (val1, val2)
            
            if closest_match:
                aligned.append(closest_match)
        
        return aligned
    
    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        x_var = sum((x - x_mean) ** 2 for x in x_values)
        y_var = sum((y - y_mean) ** 2 for y in y_values)
        
        denominator = (x_var * y_var) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _classify_correlation_strength(self, correlation_abs: float) -> CorrelationStrength:
        """Classify correlation strength"""
        if correlation_abs >= 0.8:
            return CorrelationStrength.STRONG
        elif correlation_abs >= 0.5:
            return CorrelationStrength.MODERATE
        elif correlation_abs >= 0.2:
            return CorrelationStrength.WEAK
        else:
            return CorrelationStrength.NONE

class RootCauseAnalyzer:
    """Analyze root causes of performance issues using correlations"""
    
    def __init__(self, correlation_analyzer: CorrelationAnalyzer):
        self.correlation_analyzer = correlation_analyzer
        self.issue_patterns = {}
    
    def analyze_performance_issue(self, app_service: str, app_metric: str, 
                                issue_threshold: float, current_value: float) -> Dict[str, Any]:
        """Analyze potential root causes of a performance issue"""
        
        analysis = {
            'service': app_service,
            'metric': app_metric,
            'issue_threshold': issue_threshold,
            'current_value': current_value,
            'severity': self._calculate_severity(issue_threshold, current_value),
            'potential_root_causes': [],
            'recommendations': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Get current correlations
        correlations = self.correlation_analyzer.calculate_correlations()
        
        # Filter correlations relevant to the problematic app metric
        relevant_correlations = [
            corr for corr in correlations 
            if corr.app_component == app_service and corr.app_metric == app_metric
        ]
        
        # Sort by correlation strength and confidence
        relevant_correlations.sort(
            key=lambda c: (c.strength.value == "strong", abs(c.correlation_coefficient), c.confidence),
            reverse=True
        )
        
        # Analyze top correlations for root causes
        for correlation in relevant_correlations[:10]:  # Top 10 correlations
            root_cause = self._analyze_correlation_for_root_cause(correlation, current_value)
            if root_cause:
                analysis['potential_root_causes'].append(root_cause)
        
        # Generate recommendations based on root causes
        analysis['recommendations'] = self._generate_recommendations(analysis['potential_root_causes'])
        
        return analysis
    
    def _calculate_severity(self, threshold: float, current_value: float) -> str:
        """Calculate issue severity"""
        ratio = current_value / threshold if threshold > 0 else 1
        
        if ratio >= 2.0:
            return "critical"
        elif ratio >= 1.5:
            return "high"
        elif ratio >= 1.2:
            return "medium"
        else:
            return "low"
    
    def _analyze_correlation_for_root_cause(self, correlation: Correlation, 
                                          current_app_value: float) -> Optional[Dict[str, Any]]:
        """Analyze a correlation to determine if it's a potential root cause"""
        
        # Strong positive correlation suggests infrastructure issue may be causing app issue
        if correlation.strength in [CorrelationStrength.STRONG, CorrelationStrength.MODERATE]:
            
            # Get recent infrastructure metric value
            infra_key = f"{correlation.infra_component}:{correlation.infra_metric}"
            
            # Simulate getting current infrastructure value (in real implementation, 
            # this would query the actual infrastructure monitoring system)
            current_infra_value = self._get_current_infra_value(correlation.infra_component, 
                                                              correlation.infra_metric)
            
            if current_infra_value is not None:
                root_cause = {
                    'infrastructure_component': correlation.infra_component,
                    'infrastructure_metric': correlation.infra_metric,
                    'current_infra_value': current_infra_value,
                    'correlation_coefficient': correlation.correlation_coefficient,
                    'correlation_strength': correlation.strength.value,
                    'confidence': correlation.confidence,
                    'likely_cause': self._determine_likely_cause(correlation),
                    'impact_direction': 'positive' if correlation.correlation_coefficient > 0 else 'negative'
                }
                
                return root_cause
        
        return None
    
    def _get_current_infra_value(self, component: str, metric: str) -> Optional[float]:
        """Get current infrastructure metric value (mock implementation)"""
        # In real implementation, this would query the monitoring system
        # For demo purposes, return simulated values
        
        mock_values = {
            'cpu:cpu_utilization_percent': 85.5,
            'memory:memory_utilization_percent': 78.3,
            'disk:disk_utilization_percent': 92.1,
            'network:network_connections': 450
        }
        
        key = f"{component}:{metric}"
        return mock_values.get(key)
    
    def _determine_likely_cause(self, correlation: Correlation) -> str:
        """Determine likely root cause based on correlation pattern"""
        
        infra_metric = correlation.infra_metric.lower()
        
        if 'cpu' in infra_metric and 'utilization' in infra_metric:
            return "High CPU utilization affecting application performance"
        elif 'memory' in infra_metric and 'utilization' in infra_metric:
            return "Memory pressure impacting application response times"
        elif 'disk' in infra_metric and ('utilization' in infra_metric or 'io' in infra_metric):
            return "Disk I/O bottleneck causing application slowdowns"
        elif 'network' in infra_metric:
            return "Network congestion or connectivity issues affecting application"
        elif 'connection' in infra_metric:
            return "Connection pool exhaustion or database connection issues"
        else:
            return f"Infrastructure issue with {correlation.infra_component} affecting application performance"
    
    def _generate_recommendations(self, root_causes: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on root causes"""
        recommendations = []
        
        for cause in root_causes:
            component = cause['infrastructure_component']
            metric = cause['infrastructure_metric']
            
            if 'cpu' in component.lower() or 'cpu' in metric.lower():
                recommendations.append(
                    "Scale horizontally or vertically to reduce CPU pressure"
                )
                recommendations.append(
                    "Review and optimize CPU-intensive application code"
                )
            
            elif 'memory' in component.lower() or 'memory' in metric.lower():
                recommendations.append(
                    "Increase available memory or optimize memory usage"
                )
                recommendations.append(
                    "Review application for memory leaks or inefficient memory usage"
                )
            
            elif 'disk' in component.lower() or 'disk' in metric.lower():
                recommendations.append(
                    "Optimize disk I/O patterns or upgrade to faster storage"
                )
                recommendations.append(
                    "Implement caching to reduce disk access"
                )
            
            elif 'network' in component.lower() or 'network' in metric.lower():
                recommendations.append(
                    "Investigate network connectivity and bandwidth utilization"
                )
                recommendations.append(
                    "Optimize network-intensive operations and implement connection pooling"
                )
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:5]  # Return top 5 recommendations

# Usage example and demonstration
def demonstrate_infrastructure_correlation():
    """Demonstrate infrastructure correlation capabilities"""
    
    print("🔗 Infrastructure Correlation Analysis Demo")
    print("=" * 50)
    
    # Initialize components
    infra_collector = InfrastructureCollector()
    correlation_analyzer = CorrelationAnalyzer(time_window_minutes=30)
    root_cause_analyzer = RootCauseAnalyzer(correlation_analyzer)
    
    print("📊 Collecting infrastructure metrics...")
    
    # Collect metrics from different layers
    host_metrics = infra_collector.collect_host_metrics()
    container_metrics = infra_collector.collect_container_metrics()
    k8s_metrics = infra_collector.collect_kubernetes_metrics()
    
    all_infra_metrics = host_metrics + container_metrics + k8s_metrics
    
    print(f"Collected {len(all_infra_metrics)} infrastructure metrics:")
    
    # Group by layer for display
    metrics_by_layer = defaultdict(list)
    for metric in all_infra_metrics:
        metrics_by_layer[metric.layer].append(metric)
    
    for layer, metrics in metrics_by_layer.items():
        print(f"  {layer.value}: {len(metrics)} metrics")
    
    # Add infrastructure metrics to correlation analyzer
    for metric in all_infra_metrics:
        correlation_analyzer.add_infrastructure_metric(metric)
    
    # Simulate application metrics
    print("\n📈 Simulating application metrics...")
    
    app_metrics = [
        ApplicationMetric("web-api", "response_time_ms", 450.0, "milliseconds", datetime.utcnow()),
        ApplicationMetric("web-api", "throughput_rps", 85.2, "requests/sec", datetime.utcnow()),
        ApplicationMetric("web-api", "error_rate", 2.5, "percent", datetime.utcnow()),
        ApplicationMetric("user-service", "response_time_ms", 250.0, "milliseconds", datetime.utcnow()),
        ApplicationMetric("order-service", "response_time_ms", 180.0, "milliseconds", datetime.utcnow()),
    ]
    
    # Add application metrics
    for metric in app_metrics:
        correlation_analyzer.add_application_metric(metric)
    
    # Simulate historical data for correlation analysis
    print("🔄 Simulating historical data for correlation analysis...")
    
    import random
    for i in range(100):  # Simulate 100 data points
        timestamp = datetime.utcnow() - timedelta(minutes=random.randint(0, 30))
        
        # Simulate correlated metrics (high CPU -> high response time)
        cpu_util = random.normalvariate(70, 15)
        response_time = 200 + (cpu_util - 50) * 4 + random.normalvariate(0, 20)  # Positive correlation
        
        # Add simulated metrics
        correlation_analyzer.add_infrastructure_metric(
            InfrastructureMetric(
                layer=LayerType.HOST,
                component="cpu",
                metric_name="cpu_utilization_percent",
                value=max(0, min(100, cpu_util)),
                unit="percent",
                timestamp=timestamp
            )
        )
        
        correlation_analyzer.add_application_metric(
            ApplicationMetric(
                service="web-api",
                metric_name="response_time_ms",
                value=max(50, response_time),
                unit="milliseconds",
                timestamp=timestamp
            )
        )
    
    print("🔍 Calculating correlations...")
    correlations = correlation_analyzer.calculate_correlations()
    
    print(f"\nFound {len(correlations)} significant correlations:")
    
    for corr in correlations[:5]:  # Show top 5
        print(f"  • {corr.app_component}:{corr.app_metric} ↔ {corr.infra_component}:{corr.infra_metric}")
        print(f"    Correlation: {corr.correlation_coefficient:.3f} ({corr.strength.value})")
        print(f"    Confidence: {corr.confidence:.2f}, Samples: {corr.samples}")
    
    # Simulate performance issue analysis
    print(f"\n🚨 Analyzing performance issue...")
    
    issue_analysis = root_cause_analyzer.analyze_performance_issue(
        app_service="web-api",
        app_metric="response_time_ms", 
        issue_threshold=200.0,  # Threshold: 200ms
        current_value=450.0     # Current: 450ms (issue!)
    )
    
    print(f"Performance Issue Analysis:")
    print(f"  Service: {issue_analysis['service']}")
    print(f"  Metric: {issue_analysis['metric']}")
    print(f"  Severity: {issue_analysis['severity']}")
    print(f"  Current Value: {issue_analysis['current_value']}")
    print(f"  Threshold: {issue_analysis['issue_threshold']}")
    
    if issue_analysis['potential_root_causes']:
        print(f"\n🎯 Potential Root Causes:")
        for i, cause in enumerate(issue_analysis['potential_root_causes'], 1):
            print(f"  {i}. {cause['likely_cause']}")
            print(f"     Infrastructure: {cause['infrastructure_component']} - {cause['infrastructure_metric']}")
            print(f"     Correlation: {cause['correlation_coefficient']:.3f} ({cause['correlation_strength']})")
            print(f"     Current Value: {cause['current_infra_value']}")
    
    if issue_analysis['recommendations']:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(issue_analysis['recommendations'], 1):
            print(f"  {i}. {rec}")

if __name__ == "__main__":
    demonstrate_infrastructure_correlation()
```

This comprehensive infrastructure correlation system provides enterprise-grade capabilities for connecting application performance issues with underlying infrastructure problems, enabling rapid root cause identification and resolution in complex distributed environments.