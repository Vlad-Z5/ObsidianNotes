# APM Cost Management

## Overview
APM Cost Management focuses on optimizing monitoring costs while maintaining comprehensive observability. This includes data volume optimization, intelligent sampling, cost attribution, and ROI analysis to ensure efficient resource allocation and budget control.

## Cost Optimization Framework

### 1. Data Volume Management and Sampling
```python
import random
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import logging
from collections import defaultdict, deque
import statistics

class SamplingStrategy(Enum):
    PROBABILISTIC = "probabilistic"
    RATE_LIMITING = "rate_limiting" 
    ADAPTIVE = "adaptive"
    PRIORITY_BASED = "priority_based"
    HEAD_BASED = "head_based"
    TAIL_BASED = "tail_based"

@dataclass
class CostMetrics:
    data_volume_mb: float
    ingestion_cost: float
    storage_cost: float
    query_cost: float
    retention_cost: float
    total_cost: float
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            'data_volume_mb': self.data_volume_mb,
            'ingestion_cost': self.ingestion_cost,
            'storage_cost': self.storage_cost,
            'query_cost': self.query_cost,
            'retention_cost': self.retention_cost,
            'total_cost': self.total_cost,
            'timestamp': self.timestamp,
            'cost_per_mb': self.total_cost / max(self.data_volume_mb, 0.001)
        }

class IntelligentSampler:
    def __init__(self):
        self.sampling_rates: Dict[str, float] = {}
        self.error_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.service_priorities: Dict[str, int] = {}  # 1=low, 5=critical
        self.cost_budgets: Dict[str, float] = {}
        self.current_costs: Dict[str, float] = defaultdict(float)
        
    def should_sample(self, trace_data: Dict, sampling_strategy: SamplingStrategy = SamplingStrategy.ADAPTIVE) -> bool:
        """Determine if trace should be sampled based on strategy"""
        service_name = trace_data.get('service_name', 'unknown')
        trace_id = trace_data.get('trace_id', '')
        
        if sampling_strategy == SamplingStrategy.PROBABILISTIC:
            return self._probabilistic_sampling(service_name)
        
        elif sampling_strategy == SamplingStrategy.RATE_LIMITING:
            return self._rate_limiting_sampling(service_name)
        
        elif sampling_strategy == SamplingStrategy.ADAPTIVE:
            return self._adaptive_sampling(trace_data)
        
        elif sampling_strategy == SamplingStrategy.PRIORITY_BASED:
            return self._priority_based_sampling(trace_data)
        
        elif sampling_strategy == SamplingStrategy.HEAD_BASED:
            return self._head_based_sampling(trace_data)
        
        elif sampling_strategy == SamplingStrategy.TAIL_BASED:
            return self._tail_based_sampling(trace_data)
        
        return True  # Default to sampling everything
    
    def _probabilistic_sampling(self, service_name: str) -> bool:
        """Simple probabilistic sampling"""
        rate = self.sampling_rates.get(service_name, 0.1)  # Default 10%
        return random.random() < rate
    
    def _rate_limiting_sampling(self, service_name: str) -> bool:
        """Rate-limited sampling to control costs"""
        current_hour = int(time.time() / 3600)
        rate_key = f"{service_name}_{current_hour}"
        
        if rate_key not in self.current_costs:
            self.current_costs[rate_key] = 0
        
        budget = self.cost_budgets.get(service_name, 100.0)  # $100 default
        cost_per_trace = 0.001  # $0.001 per trace estimate
        
        if self.current_costs[rate_key] + cost_per_trace <= budget:
            self.current_costs[rate_key] += cost_per_trace
            return True
        
        return False
    
    def _adaptive_sampling(self, trace_data: Dict) -> bool:
        """Adaptive sampling based on service health and importance"""
        service_name = trace_data.get('service_name', 'unknown')
        response_time = trace_data.get('duration_ms', 0)
        has_error = trace_data.get('error', False)
        
        # Always sample errors
        if has_error:
            return True
        
        # Update service metrics
        self.response_times[service_name].append(response_time)
        self.error_rates[service_name].append(1 if has_error else 0)
        
        # Calculate dynamic sampling rate
        base_rate = 0.1  # 10% base rate
        
        # Increase rate for slow services
        if len(self.response_times[service_name]) >= 10:
            avg_response_time = statistics.mean(self.response_times[service_name])
            if avg_response_time > 1000:  # > 1 second
                base_rate *= 2
            elif avg_response_time > 5000:  # > 5 seconds
                base_rate *= 3
        
        # Increase rate for services with recent errors
        if len(self.error_rates[service_name]) >= 10:
            recent_error_rate = statistics.mean(list(self.error_rates[service_name])[-10:])
            if recent_error_rate > 0.05:  # > 5% error rate
                base_rate *= 2
        
        # Consider service priority
        priority = self.service_priorities.get(service_name, 3)
        priority_multiplier = priority / 3.0  # Scale by priority
        base_rate *= priority_multiplier
        
        # Cap at 100%
        final_rate = min(base_rate, 1.0)
        
        return random.random() < final_rate
    
    def _priority_based_sampling(self, trace_data: Dict) -> bool:
        """Priority-based sampling for critical services"""
        service_name = trace_data.get('service_name', 'unknown')
        priority = self.service_priorities.get(service_name, 3)
        
        # Critical services (priority 5) - 80% sampling
        # Important services (priority 4) - 50% sampling  
        # Normal services (priority 3) - 20% sampling
        # Low priority services (priority 1-2) - 5% sampling
        
        sampling_rates = {
            5: 0.8,  # Critical
            4: 0.5,  # Important
            3: 0.2,  # Normal
            2: 0.1,  # Low
            1: 0.05  # Very low
        }
        
        rate = sampling_rates.get(priority, 0.1)
        return random.random() < rate
    
    def _head_based_sampling(self, trace_data: Dict) -> bool:
        """Head-based sampling - decide at trace start"""
        trace_id = trace_data.get('trace_id', '')
        service_name = trace_data.get('service_name', 'unknown')
        
        # Use consistent hash for deterministic sampling
        hash_value = int(hashlib.md5(f"{trace_id}_{service_name}".encode()).hexdigest()[:8], 16)
        rate = self.sampling_rates.get(service_name, 0.1)
        threshold = int(rate * 0xFFFFFFFF)
        
        return hash_value < threshold
    
    def _tail_based_sampling(self, trace_data: Dict) -> bool:
        """Tail-based sampling - decide after trace completion"""
        # This would typically require buffering traces and deciding later
        # For this example, we'll use heuristics based on trace characteristics
        
        duration_ms = trace_data.get('duration_ms', 0)
        has_error = trace_data.get('error', False)
        span_count = trace_data.get('span_count', 1)
        
        # Always keep error traces
        if has_error:
            return True
        
        # Keep slow traces
        if duration_ms > 5000:  # > 5 seconds
            return True
        
        # Keep complex traces (many spans)
        if span_count > 50:
            return True
        
        # Sample normal traces at low rate
        return random.random() < 0.05
    
    def update_sampling_configuration(self, service_costs: Dict[str, float], budgets: Dict[str, float]):
        """Update sampling rates based on current costs and budgets"""
        for service, current_cost in service_costs.items():
            budget = budgets.get(service, 100.0)
            
            if current_cost > budget * 0.9:  # 90% of budget used
                # Reduce sampling rate
                current_rate = self.sampling_rates.get(service, 0.1)
                self.sampling_rates[service] = max(current_rate * 0.5, 0.01)  # Minimum 1%
                
            elif current_cost < budget * 0.3:  # Less than 30% of budget used
                # Increase sampling rate
                current_rate = self.sampling_rates.get(service, 0.1)
                self.sampling_rates[service] = min(current_rate * 1.5, 1.0)  # Maximum 100%
```

### 2. Cost Tracking and Attribution
```python
import asyncio
from datetime import datetime, timedelta

class CostTracker:
    def __init__(self):
        self.cost_history: List[CostMetrics] = []
        self.service_costs: Dict[str, List[CostMetrics]] = defaultdict(list)
        self.team_budgets: Dict[str, float] = {}
        self.cost_alerts: List[Dict] = []
        self.pricing_tiers = self._initialize_pricing_tiers()
        
    def _initialize_pricing_tiers(self) -> Dict:
        """Initialize APM tool pricing tiers"""
        return {
            'datadog': {
                'ingestion_per_gb': 1.27,
                'storage_per_gb_month': 0.0225,
                'query_per_million': 5.0,
                'retention_multiplier': {
                    '30_days': 1.0,
                    '90_days': 1.5,
                    '365_days': 2.0
                }
            },
            'new_relic': {
                'ingestion_per_gb': 0.30,
                'storage_per_gb_month': 0.05,
                'query_per_million': 2.0,
                'retention_multiplier': {
                    '30_days': 1.0,
                    '90_days': 1.2,
                    '365_days': 1.8
                }
            },
            'elastic_apm': {
                'ingestion_per_gb': 0.095,
                'storage_per_gb_month': 0.027,
                'query_per_million': 1.0,
                'retention_multiplier': {
                    '30_days': 1.0,
                    '90_days': 1.3,
                    '365_days': 2.2
                }
            }
        }
    
    def calculate_service_cost(self, service_name: str, data_volume_gb: float, 
                              query_count: int, retention_days: int = 30,
                              apm_provider: str = 'datadog') -> CostMetrics:
        """Calculate cost for a specific service"""
        
        pricing = self.pricing_tiers.get(apm_provider, self.pricing_tiers['datadog'])
        
        # Calculate ingestion cost
        ingestion_cost = data_volume_gb * pricing['ingestion_per_gb']
        
        # Calculate storage cost (monthly)
        storage_cost = data_volume_gb * pricing['storage_per_gb_month']
        
        # Apply retention multiplier
        retention_period = '30_days'
        if retention_days <= 30:
            retention_period = '30_days'
        elif retention_days <= 90:
            retention_period = '90_days'
        else:
            retention_period = '365_days'
        
        retention_multiplier = pricing['retention_multiplier'][retention_period]
        retention_cost = storage_cost * retention_multiplier
        
        # Calculate query cost
        query_cost = (query_count / 1000000) * pricing['query_per_million']
        
        total_cost = ingestion_cost + retention_cost + query_cost
        
        cost_metrics = CostMetrics(
            data_volume_mb=data_volume_gb * 1024,
            ingestion_cost=ingestion_cost,
            storage_cost=storage_cost,
            query_cost=query_cost,
            retention_cost=retention_cost,
            total_cost=total_cost,
            timestamp=time.time()
        )
        
        # Store in service costs
        self.service_costs[service_name].append(cost_metrics)
        
        # Keep only last 30 days
        cutoff_time = time.time() - (30 * 24 * 3600)
        self.service_costs[service_name] = [
            c for c in self.service_costs[service_name] 
            if c.timestamp > cutoff_time
        ]
        
        return cost_metrics
    
    def get_cost_breakdown(self, time_period_days: int = 30) -> Dict:
        """Get detailed cost breakdown"""
        cutoff_time = time.time() - (time_period_days * 24 * 3600)
        
        breakdown = {
            'total_costs': {
                'ingestion': 0,
                'storage': 0,
                'query': 0,
                'retention': 0,
                'total': 0
            },
            'service_costs': {},
            'cost_trends': [],
            'top_cost_drivers': []
        }
        
        # Aggregate costs by service
        for service_name, cost_list in self.service_costs.items():
            recent_costs = [c for c in cost_list if c.timestamp > cutoff_time]
            
            if recent_costs:
                service_total = {
                    'ingestion': sum(c.ingestion_cost for c in recent_costs),
                    'storage': sum(c.storage_cost for c in recent_costs),
                    'query': sum(c.query_cost for c in recent_costs),
                    'retention': sum(c.retention_cost for c in recent_costs),
                    'data_volume_gb': sum(c.data_volume_mb for c in recent_costs) / 1024
                }
                service_total['total'] = sum(service_total[k] for k in ['ingestion', 'storage', 'query', 'retention'])
                
                breakdown['service_costs'][service_name] = service_total
                
                # Add to total
                for cost_type in ['ingestion', 'storage', 'query', 'retention', 'total']:
                    breakdown['total_costs'][cost_type] += service_total[cost_type]
        
        # Calculate trends (daily costs over period)
        for day_offset in range(time_period_days):
            day_start = time.time() - ((day_offset + 1) * 24 * 3600)
            day_end = time.time() - (day_offset * 24 * 3600)
            
            day_cost = 0
            for service_costs in self.service_costs.values():
                day_costs = [c for c in service_costs if day_start <= c.timestamp < day_end]
                day_cost += sum(c.total_cost for c in day_costs)
            
            breakdown['cost_trends'].append({
                'date': datetime.fromtimestamp(day_start).strftime('%Y-%m-%d'),
                'cost': day_cost
            })
        
        # Top cost drivers
        service_totals = [(service, data['total']) for service, data in breakdown['service_costs'].items()]
        breakdown['top_cost_drivers'] = sorted(service_totals, key=lambda x: x[1], reverse=True)[:10]
        
        return breakdown
    
    def check_budget_alerts(self) -> List[Dict]:
        """Check for budget threshold breaches"""
        alerts = []
        
        for team, budget in self.team_budgets.items():
            # Calculate current month costs for team
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_start_timestamp = month_start.timestamp()
            
            team_services = self._get_team_services(team)
            month_cost = 0
            
            for service in team_services:
                if service in self.service_costs:
                    month_costs = [
                        c for c in self.service_costs[service] 
                        if c.timestamp >= month_start_timestamp
                    ]
                    month_cost += sum(c.total_cost for c in month_costs)
            
            # Check thresholds
            if month_cost > budget * 0.9:  # 90% threshold
                severity = 'critical' if month_cost > budget else 'warning'
                alerts.append({
                    'type': 'budget_threshold',
                    'team': team,
                    'budget': budget,
                    'current_cost': month_cost,
                    'usage_percent': (month_cost / budget) * 100,
                    'severity': severity,
                    'timestamp': time.time()
                })
        
        self.cost_alerts.extend(alerts)
        return alerts
    
    def _get_team_services(self, team: str) -> List[str]:
        """Get services owned by team (implementation depends on your service catalog)"""
        # This would typically come from a service catalog or configuration
        team_service_mapping = {
            'platform': ['auth-service', 'user-service', 'notification-service'],
            'payments': ['payment-service', 'billing-service'],
            'checkout': ['cart-service', 'order-service', 'inventory-service']
        }
        return team_service_mapping.get(team, [])
    
    def generate_cost_optimization_recommendations(self) -> List[Dict]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        cost_breakdown = self.get_cost_breakdown()
        
        # High data volume services
        for service, costs in cost_breakdown['service_costs'].items():
            data_volume_gb = costs['data_volume_gb']
            cost_per_gb = costs['total'] / max(data_volume_gb, 0.001)
            
            if data_volume_gb > 100:  # > 100GB per month
                recommendations.append({
                    'type': 'high_volume_service',
                    'service': service,
                    'data_volume_gb': data_volume_gb,
                    'cost': costs['total'],
                    'priority': 'high',
                    'recommendation': f"Service {service} generates {data_volume_gb:.1f}GB of data. Consider implementing intelligent sampling to reduce volume by 50-80%.",
                    'estimated_savings': costs['total'] * 0.6  # 60% potential savings
                })
            
            # Expensive per-GB services
            if cost_per_gb > 2.0 and costs['total'] > 50:
                recommendations.append({
                    'type': 'expensive_per_gb',
                    'service': service,
                    'cost_per_gb': cost_per_gb,
                    'cost': costs['total'],
                    'priority': 'medium',
                    'recommendation': f"Service {service} has high cost per GB ({cost_per_gb:.2f}). Review data retention policies and consider cheaper storage tiers.",
                    'estimated_savings': costs['total'] * 0.3  # 30% potential savings
                })
        
        # Long retention periods
        for service, costs in cost_breakdown['service_costs'].items():
            if costs['retention'] > costs['storage'] * 1.5:  # Retention cost > 150% of base storage
                recommendations.append({
                    'type': 'long_retention',
                    'service': service,
                    'retention_cost': costs['retention'],
                    'priority': 'medium',
                    'recommendation': f"Service {service} has high retention costs. Consider reducing retention period for non-critical data.",
                    'estimated_savings': costs['retention'] * 0.4  # 40% potential savings
                })
        
        # Sort by estimated savings
        recommendations.sort(key=lambda x: x.get('estimated_savings', 0), reverse=True)
        
        return recommendations
```

### 3. Resource Right-Sizing and Optimization
```python
class ResourceOptimizer:
    def __init__(self):
        self.resource_usage: Dict[str, List[Dict]] = defaultdict(list)
        self.optimization_rules: List[Dict] = []
        self.cost_models: Dict[str, Dict] = {}
        
    def track_resource_usage(self, resource_type: str, service: str, usage_data: Dict):
        """Track resource usage for optimization analysis"""
        usage_entry = {
            'service': service,
            'timestamp': time.time(),
            'cpu_utilization': usage_data.get('cpu_percent', 0),
            'memory_utilization': usage_data.get('memory_percent', 0),
            'network_io': usage_data.get('network_bytes', 0),
            'disk_io': usage_data.get('disk_bytes', 0),
            'request_rate': usage_data.get('requests_per_second', 0),
            'cost_per_hour': usage_data.get('cost_per_hour', 0)
        }
        
        self.resource_usage[resource_type].append(usage_entry)
        
        # Keep only last 7 days
        cutoff_time = time.time() - (7 * 24 * 3600)
        self.resource_usage[resource_type] = [
            entry for entry in self.resource_usage[resource_type]
            if entry['timestamp'] > cutoff_time
        ]
    
    def analyze_resource_utilization(self) -> Dict:
        """Analyze resource utilization patterns"""
        analysis = {
            'underutilized_resources': [],
            'overutilized_resources': [],
            'right_sizing_opportunities': [],
            'total_waste_cost': 0
        }
        
        for resource_type, usage_list in self.resource_usage.items():
            # Group by service
            service_usage = defaultdict(list)
            for entry in usage_list:
                service_usage[entry['service']].append(entry)
            
            for service, entries in service_usage.items():
                if len(entries) < 10:  # Need minimum data points
                    continue
                
                # Calculate averages
                avg_cpu = statistics.mean([e['cpu_utilization'] for e in entries])
                avg_memory = statistics.mean([e['memory_utilization'] for e in entries])
                avg_cost = statistics.mean([e['cost_per_hour'] for e in entries])
                
                # Underutilized (< 20% CPU and < 30% memory)
                if avg_cpu < 20 and avg_memory < 30:
                    potential_savings = avg_cost * 0.5 * 24 * 30  # 50% savings for a month
                    analysis['underutilized_resources'].append({
                        'resource_type': resource_type,
                        'service': service,
                        'avg_cpu': avg_cpu,
                        'avg_memory': avg_memory,
                        'cost_per_hour': avg_cost,
                        'potential_monthly_savings': potential_savings,
                        'recommendation': 'Consider downsizing or using spot instances'
                    })
                    analysis['total_waste_cost'] += potential_savings
                
                # Overutilized (> 80% CPU or > 85% memory)
                elif avg_cpu > 80 or avg_memory > 85:
                    analysis['overutilized_resources'].append({
                        'resource_type': resource_type,
                        'service': service,
                        'avg_cpu': avg_cpu,
                        'avg_memory': avg_memory,
                        'cost_per_hour': avg_cost,
                        'recommendation': 'Consider upgrading to prevent performance issues'
                    })
                
                # Right-sizing opportunities (moderate usage)
                elif 30 <= avg_cpu <= 70 and 40 <= avg_memory <= 75:
                    analysis['right_sizing_opportunities'].append({
                        'resource_type': resource_type,
                        'service': service,
                        'avg_cpu': avg_cpu,
                        'avg_memory': avg_memory,
                        'status': 'well_sized'
                    })
        
        return analysis
    
    def generate_scaling_recommendations(self) -> List[Dict]:
        """Generate auto-scaling recommendations"""
        recommendations = []
        
        for resource_type, usage_list in self.resource_usage.items():
            service_patterns = defaultdict(list)
            
            # Group by service and analyze patterns
            for entry in usage_list:
                service_patterns[entry['service']].append(entry)
            
            for service, entries in service_patterns.items():
                if len(entries) < 50:  # Need sufficient data
                    continue
                
                # Sort by timestamp
                entries.sort(key=lambda x: x['timestamp'])
                
                # Calculate metrics
                cpu_values = [e['cpu_utilization'] for e in entries]
                memory_values = [e['memory_utilization'] for e in entries]
                request_rates = [e['request_rate'] for e in entries]
                
                # Check for spikes
                cpu_p95 = statistics.quantiles(cpu_values, n=20)[18] if len(cpu_values) >= 20 else max(cpu_values)
                cpu_avg = statistics.mean(cpu_values)
                
                memory_p95 = statistics.quantiles(memory_values, n=20)[18] if len(memory_values) >= 20 else max(memory_values)
                memory_avg = statistics.mean(memory_values)
                
                # Recommendation logic
                if cpu_p95 > 90 or memory_p95 > 95:
                    recommendations.append({
                        'service': service,
                        'resource_type': resource_type,
                        'recommendation_type': 'enable_autoscaling',
                        'priority': 'high',
                        'reason': f"Resource spikes detected (CPU P95: {cpu_p95:.1f}%, Memory P95: {memory_p95:.1f}%)",
                        'suggested_config': {
                            'min_instances': 2,
                            'max_instances': 10,
                            'cpu_threshold': 70,
                            'memory_threshold': 80,
                            'scale_up_policy': 'aggressive',
                            'scale_down_policy': 'conservative'
                        }
                    })
                
                elif cpu_avg < 30 and memory_avg < 40:
                    recommendations.append({
                        'service': service,
                        'resource_type': resource_type,
                        'recommendation_type': 'reduce_base_capacity',
                        'priority': 'medium',
                        'reason': f"Consistent low utilization (CPU: {cpu_avg:.1f}%, Memory: {memory_avg:.1f}%)",
                        'suggested_config': {
                            'reduce_instances_by': 0.5,
                            'estimated_savings': entries[0]['cost_per_hour'] * 0.5 * 24 * 30
                        }
                    })
        
        return recommendations

class CostOptimizationEngine:
    def __init__(self):
        self.sampler = IntelligentSampler()
        self.cost_tracker = CostTracker()
        self.resource_optimizer = ResourceOptimizer()
        self.optimization_history: List[Dict] = []
        
    async def run_optimization_cycle(self) -> Dict:
        """Run complete cost optimization cycle"""
        optimization_results = {
            'timestamp': time.time(),
            'cost_analysis': {},
            'sampling_adjustments': {},
            'resource_recommendations': [],
            'estimated_total_savings': 0
        }
        
        # 1. Analyze current costs
        cost_breakdown = self.cost_tracker.get_cost_breakdown()
        optimization_results['cost_analysis'] = cost_breakdown
        
        # 2. Check budget alerts
        budget_alerts = self.cost_tracker.check_budget_alerts()
        
        # 3. Generate cost optimization recommendations
        cost_recommendations = self.cost_tracker.generate_cost_optimization_recommendations()
        
        # 4. Adjust sampling rates based on costs
        service_costs = {
            service: data['total'] 
            for service, data in cost_breakdown['service_costs'].items()
        }
        
        # Assume budgets (in production, these would come from configuration)
        budgets = {service: cost * 1.2 for service, cost in service_costs.items()}  # 20% buffer
        
        self.sampler.update_sampling_configuration(service_costs, budgets)
        optimization_results['sampling_adjustments'] = self.sampler.sampling_rates
        
        # 5. Get resource optimization recommendations
        resource_analysis = self.resource_optimizer.analyze_resource_utilization()
        scaling_recommendations = self.resource_optimizer.generate_scaling_recommendations()
        
        optimization_results['resource_recommendations'] = scaling_recommendations
        
        # 6. Calculate total estimated savings
        total_savings = 0
        for rec in cost_recommendations:
            total_savings += rec.get('estimated_savings', 0)
        
        total_savings += resource_analysis['total_waste_cost']
        optimization_results['estimated_total_savings'] = total_savings
        
        # Store optimization history
        self.optimization_history.append(optimization_results)
        
        return optimization_results
    
    def implement_optimization_recommendations(self, recommendations: List[Dict]) -> Dict:
        """Implement approved optimization recommendations"""
        implementation_results = {
            'implemented': [],
            'failed': [],
            'total_savings_realized': 0
        }
        
        for rec in recommendations:
            try:
                if rec['type'] == 'high_volume_service':
                    # Implement intelligent sampling
                    service = rec['service']
                    self.sampler.sampling_rates[service] = 0.2  # Reduce to 20%
                    self.sampler.service_priorities[service] = 3  # Normal priority
                    
                    implementation_results['implemented'].append({
                        'recommendation_id': rec.get('id'),
                        'type': rec['type'],
                        'action': f"Reduced sampling rate to 20% for {service}",
                        'estimated_savings': rec['estimated_savings'] * 0.8  # 80% of estimated
                    })
                    
                elif rec['type'] == 'long_retention':
                    # This would integrate with your APM tool's API
                    service = rec['service']
                    implementation_results['implemented'].append({
                        'recommendation_id': rec.get('id'),
                        'type': rec['type'],
                        'action': f"Reduced retention period for {service}",
                        'estimated_savings': rec['estimated_savings'] * 0.6  # 60% of estimated
                    })
                
                # Add realized savings
                implementation_results['total_savings_realized'] += implementation_results['implemented'][-1]['estimated_savings']
                
            except Exception as e:
                implementation_results['failed'].append({
                    'recommendation_id': rec.get('id'),
                    'error': str(e),
                    'type': rec['type']
                })
        
        return implementation_results

# Usage example and monitoring
class APMCostDashboard:
    def __init__(self, cost_engine: CostOptimizationEngine):
        self.cost_engine = cost_engine
        
    def generate_cost_dashboard_data(self) -> Dict:
        """Generate data for cost management dashboard"""
        cost_breakdown = self.cost_engine.cost_tracker.get_cost_breakdown()
        resource_analysis = self.cost_engine.resource_optimizer.analyze_resource_utilization()
        
        dashboard_data = {
            'summary': {
                'total_monthly_cost': cost_breakdown['total_costs']['total'],
                'cost_per_gb': cost_breakdown['total_costs']['total'] / max(sum(
                    data['data_volume_gb'] for data in cost_breakdown['service_costs'].values()
                ), 0.001),
                'top_cost_driver': cost_breakdown['top_cost_drivers'][0] if cost_breakdown['top_cost_drivers'] else None,
                'potential_savings': resource_analysis['total_waste_cost']
            },
            'cost_trends': cost_breakdown['cost_trends'],
            'service_breakdown': cost_breakdown['service_costs'],
            'optimization_opportunities': {
                'underutilized_resources': len(resource_analysis['underutilized_resources']),
                'high_volume_services': sum(1 for s, d in cost_breakdown['service_costs'].items() if d['data_volume_gb'] > 100),
                'total_potential_savings': resource_analysis['total_waste_cost']
            },
            'sampling_rates': self.cost_engine.sampler.sampling_rates,
            'budget_status': self._get_budget_status()
        }
        
        return dashboard_data
    
    def _get_budget_status(self) -> Dict:
        """Get budget status for all teams"""
        budget_alerts = self.cost_engine.cost_tracker.check_budget_alerts()
        
        return {
            'total_teams': len(self.cost_engine.cost_tracker.team_budgets),
            'teams_over_budget': len([a for a in budget_alerts if a['severity'] == 'critical']),
            'teams_near_budget': len([a for a in budget_alerts if a['severity'] == 'warning']),
            'alerts': budget_alerts
        }

# Automated cost optimization job
async def run_daily_cost_optimization():
    """Daily cost optimization job"""
    cost_engine = CostOptimizationEngine()
    
    # Run optimization cycle
    results = await cost_engine.run_optimization_cycle()
    
    # Auto-implement low-risk optimizations
    auto_implement_recommendations = [
        rec for rec in results.get('cost_analysis', {}).get('recommendations', [])
        if rec.get('priority') == 'medium' and rec.get('estimated_savings', 0) > 100
    ]
    
    if auto_implement_recommendations:
        implementation_results = cost_engine.implement_optimization_recommendations(auto_implement_recommendations)
        
        logging.info(f"Auto-implemented {len(implementation_results['implemented'])} cost optimizations")
        logging.info(f"Total realized savings: ${implementation_results['total_savings_realized']:.2f}")
    
    return results

# Example usage
if __name__ == "__main__":
    # Initialize cost management system
    cost_engine = CostOptimizationEngine()
    dashboard = APMCostDashboard(cost_engine)
    
    # Simulate some cost data
    cost_engine.cost_tracker.calculate_service_cost('auth-service', 50.0, 1000000, 90, 'datadog')
    cost_engine.cost_tracker.calculate_service_cost('payment-service', 150.0, 5000000, 180, 'datadog')
    cost_engine.cost_tracker.calculate_service_cost('user-service', 25.0, 500000, 30, 'datadog')
    
    # Set team budgets
    cost_engine.cost_tracker.team_budgets = {
        'platform': 500.0,
        'payments': 800.0,
        'frontend': 300.0
    }
    
    # Run optimization
    results = asyncio.run(cost_engine.run_optimization_cycle())
    
    # Generate dashboard data
    dashboard_data = dashboard.generate_cost_dashboard_data()
    
    print(json.dumps(dashboard_data, indent=2, default=str))
```

This comprehensive APM Cost Management framework provides intelligent sampling, cost tracking, resource optimization, and automated cost control while maintaining observability quality and ensuring budget compliance.