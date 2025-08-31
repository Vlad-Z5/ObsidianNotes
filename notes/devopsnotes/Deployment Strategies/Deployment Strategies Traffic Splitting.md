# Deployment Strategies Traffic Splitting

Advanced traffic splitting methodologies, intelligent routing algorithms, and dynamic traffic management for sophisticated deployment strategies.

## Table of Contents
1. [Enterprise Traffic Splitting Architecture](#enterprise-traffic-splitting-architecture)
2. [Intelligent Routing Algorithms](#intelligent-routing-algorithms)
3. [Multi-Dimensional Traffic Control](#multi-dimensional-traffic-control)
4. [Advanced Load Balancing Strategies](#advanced-load-balancing-strategies)
5. [Real-Time Traffic Management](#real-time-traffic-management)
6. [Service Mesh Integration](#service-mesh-integration)
7. [Performance-Based Routing](#performance-based-routing)
8. [Automated Traffic Optimization](#automated-traffic-optimization)

## Enterprise Traffic Splitting Architecture

### Intelligent Traffic Splitting Engine
```python
#!/usr/bin/env python3
# enterprise_traffic_splitter.py
# Advanced traffic splitting and routing management system

import asyncio
import json
import logging
import time
import random
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import aiohttp
import kubernetes_asyncio as k8s
import numpy as np
from scipy import stats
import redis.asyncio as redis

class TrafficSplitStrategy(Enum):
    PERCENTAGE_BASED = "percentage_based"
    USER_BASED = "user_based"
    GEOGRAPHIC_BASED = "geographic_based"
    DEVICE_BASED = "device_based"
    TIME_BASED = "time_based"
    PERFORMANCE_BASED = "performance_based"
    CANARY_ANALYSIS = "canary_analysis"
    A_B_TESTING = "ab_testing"
    FEATURE_FLAG_BASED = "feature_flag_based"
    LOAD_BASED = "load_based"

class RoutingCriteria(Enum):
    RANDOM = "random"
    HASH_BASED = "hash_based"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    COMBINED_SCORE = "combined_score"

@dataclass
class TrafficTarget:
    name: str
    version: str
    weight: float
    endpoints: List[str]
    health_score: float
    performance_metrics: Dict[str, float]
    metadata: Dict[str, Any]
    enabled: bool = True
    max_capacity: Optional[int] = None
    current_load: int = 0

@dataclass
class TrafficSplitRule:
    rule_id: str
    name: str
    strategy: TrafficSplitStrategy
    routing_criteria: RoutingCriteria
    targets: List[TrafficTarget]
    conditions: Dict[str, Any]
    priority: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class TrafficRequest:
    request_id: str
    user_id: Optional[str]
    session_id: str
    ip_address: str
    user_agent: str
    headers: Dict[str, str]
    geographic_location: Optional[Dict[str, str]]
    device_info: Optional[Dict[str, str]]
    timestamp: datetime
    feature_flags: List[str] = None

@dataclass
class RoutingDecision:
    request_id: str
    selected_target: TrafficTarget
    rule_applied: TrafficSplitRule
    routing_reason: str
    confidence_score: float
    processing_time_ms: float
    metadata: Dict[str, Any]

class EnterpriseTrafficSplitter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Traffic splitting rules
        self.rules: Dict[str, TrafficSplitRule] = {}
        self.active_experiments: Dict[str, Dict] = {}
        
        # Performance tracking
        self.performance_cache = {}
        self.routing_history = {}
        
        # External integrations
        self.redis_client = None
        self.k8s_client = None
        
        # Real-time metrics
        self.target_metrics = {}
        self.routing_stats = {}
        
        # Machine learning components
        self.routing_model = None
        self.performance_predictor = None
    
    async def initialize(self):
        """Initialize the traffic splitting engine"""
        try:
            # Initialize Redis for caching and state management
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(**redis_config)
            
            # Initialize Kubernetes client for service discovery
            await k8s.config.load_incluster_config()
            self.k8s_client = k8s.client.ApiClient()
            
            # Start background tasks
            asyncio.create_task(self._metrics_collection_loop())
            asyncio.create_task(self._performance_monitoring_loop())
            asyncio.create_task(self._experiment_analysis_loop())
            
            # Load existing rules
            await self._load_traffic_rules()
            
            self.logger.info("Enterprise Traffic Splitter initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize traffic splitter: {e}")
            raise
    
    async def route_traffic(self, request: TrafficRequest) -> RoutingDecision:
        """Main traffic routing decision function"""
        
        start_time = time.time()
        
        try:
            # Find applicable rules
            applicable_rules = await self._find_applicable_rules(request)
            
            if not applicable_rules:
                # Default routing if no rules match
                default_target = await self._get_default_target()
                return RoutingDecision(
                    request_id=request.request_id,
                    selected_target=default_target,
                    rule_applied=None,
                    routing_reason="No applicable rules found, using default",
                    confidence_score=0.5,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    metadata={}
                )
            
            # Select the highest priority rule
            selected_rule = max(applicable_rules, key=lambda r: r.priority)
            
            # Apply the routing strategy
            selected_target = await self._apply_routing_strategy(request, selected_rule)
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(request, selected_rule, selected_target)
            
            # Create routing decision
            decision = RoutingDecision(
                request_id=request.request_id,
                selected_target=selected_target,
                rule_applied=selected_rule,
                routing_reason=f"Applied {selected_rule.strategy.value} strategy",
                confidence_score=confidence_score,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={
                    'rule_id': selected_rule.rule_id,
                    'strategy': selected_rule.strategy.value,
                    'target_weight': selected_target.weight
                }
            )
            
            # Record routing decision
            await self._record_routing_decision(decision)
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in traffic routing: {e}")
            
            # Fallback to default routing
            default_target = await self._get_default_target()
            return RoutingDecision(
                request_id=request.request_id,
                selected_target=default_target,
                rule_applied=None,
                routing_reason=f"Error in routing: {str(e)}, using default",
                confidence_score=0.1,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={'error': str(e)}
            )
    
    async def _apply_routing_strategy(
        self,
        request: TrafficRequest,
        rule: TrafficSplitRule
    ) -> TrafficTarget:
        """Apply the specified routing strategy"""
        
        strategy = rule.strategy
        targets = [t for t in rule.targets if t.enabled]
        
        if not targets:
            raise ValueError(f"No enabled targets for rule {rule.rule_id}")
        
        if strategy == TrafficSplitStrategy.PERCENTAGE_BASED:
            return await self._percentage_based_routing(request, targets)
        
        elif strategy == TrafficSplitStrategy.USER_BASED:
            return await self._user_based_routing(request, targets, rule)
        
        elif strategy == TrafficSplitStrategy.GEOGRAPHIC_BASED:
            return await self._geographic_based_routing(request, targets, rule)
        
        elif strategy == TrafficSplitStrategy.PERFORMANCE_BASED:
            return await self._performance_based_routing(request, targets)
        
        elif strategy == TrafficSplitStrategy.CANARY_ANALYSIS:
            return await self._canary_analysis_routing(request, targets, rule)
        
        elif strategy == TrafficSplitStrategy.A_B_TESTING:
            return await self._ab_testing_routing(request, targets, rule)
        
        elif strategy == TrafficSplitStrategy.FEATURE_FLAG_BASED:
            return await self._feature_flag_routing(request, targets, rule)
        
        elif strategy == TrafficSplitStrategy.LOAD_BASED:
            return await self._load_based_routing(request, targets)
        
        else:
            # Default to percentage-based routing
            return await self._percentage_based_routing(request, targets)
    
    async def _percentage_based_routing(
        self,
        request: TrafficRequest,
        targets: List[TrafficTarget]
    ) -> TrafficTarget:
        """Simple percentage-based traffic splitting"""
        
        # Normalize weights
        total_weight = sum(t.weight for t in targets)
        if total_weight == 0:
            return random.choice(targets)
        
        # Generate random value
        random_value = random.uniform(0, total_weight)
        
        # Select target based on cumulative weights
        cumulative_weight = 0
        for target in targets:
            cumulative_weight += target.weight
            if random_value <= cumulative_weight:
                return target
        
        # Fallback to last target
        return targets[-1]
    
    async def _user_based_routing(
        self,
        request: TrafficRequest,
        targets: List[TrafficTarget],
        rule: TrafficSplitRule
    ) -> TrafficTarget:
        """Route based on user characteristics"""
        
        if not request.user_id:
            # No user ID, fall back to session-based routing
            routing_key = request.session_id
        else:
            routing_key = request.user_id
        
        # Hash-based consistent routing
        hash_value = int(hashlib.md5(routing_key.encode()).hexdigest(), 16)
        
        # User segmentation based on conditions
        user_segment = rule.conditions.get('user_segment', 'default')
        
        if user_segment == 'premium':
            # Premium users get priority routing to best performing targets
            best_targets = sorted(targets, key=lambda t: t.performance_metrics.get('success_rate', 0), reverse=True)
            target_index = hash_value % min(2, len(best_targets))  # Top 2 targets
            return best_targets[target_index]
        
        elif user_segment == 'beta':
            # Beta users get routed to newer versions
            beta_targets = [t for t in targets if 'beta' in t.version or 'canary' in t.version]
            if beta_targets:
                target_index = hash_value % len(beta_targets)
                return beta_targets[target_index]
        
        # Default hash-based routing
        target_index = hash_value % len(targets)
        return targets[target_index]
    
    async def _geographic_based_routing(
        self,
        request: TrafficRequest,
        targets: List[TrafficTarget],
        rule: TrafficSplitRule
    ) -> TrafficTarget:
        """Route based on geographic location"""
        
        if not request.geographic_location:
            return await self._percentage_based_routing(request, targets)
        
        user_country = request.geographic_location.get('country', 'unknown')
        user_region = request.geographic_location.get('region', 'unknown')
        
        # Geographic routing preferences
        geo_preferences = rule.conditions.get('geographic_preferences', {})
        
        # Find targets optimized for user's location
        preferred_targets = []
        for target in targets:
            target_regions = target.metadata.get('preferred_regions', [])
            if user_region in target_regions or user_country in target_regions:
                preferred_targets.append(target)
        
        if preferred_targets:
            return await self._percentage_based_routing(request, preferred_targets)
        
        # Fall back to latency-based routing
        return await self._latency_based_routing(request, targets)
    
    async def _performance_based_routing(
        self,
        request: TrafficRequest,
        targets: List[TrafficTarget]
    ) -> TrafficTarget:
        """Route based on target performance metrics"""
        
        # Calculate performance scores for each target
        scored_targets = []
        
        for target in targets:
            metrics = target.performance_metrics
            
            # Composite performance score
            success_rate = metrics.get('success_rate', 0.95)
            response_time = metrics.get('avg_response_time', 1000)  # ms
            error_rate = metrics.get('error_rate', 0.05)
            cpu_utilization = metrics.get('cpu_utilization', 50)
            
            # Normalize and weight metrics (higher is better)
            success_score = success_rate * 100  # 0-100
            response_score = max(0, 100 - (response_time / 10))  # Penalize high response times
            error_score = max(0, 100 - (error_rate * 1000))  # Penalize high error rates
            cpu_score = max(0, 100 - cpu_utilization)  # Penalize high CPU usage
            
            # Weighted composite score
            composite_score = (
                success_score * 0.3 +
                response_score * 0.3 +
                error_score * 0.3 +
                cpu_score * 0.1
            )
            
            scored_targets.append((target, composite_score))
        
        # Sort by performance score (descending)
        scored_targets.sort(key=lambda x: x[1], reverse=True)
        
        # Weighted selection based on performance scores
        total_score = sum(score for _, score in scored_targets)
        
        if total_score == 0:
            return random.choice(targets)
        
        random_value = random.uniform(0, total_score)
        cumulative_score = 0
        
        for target, score in scored_targets:
            cumulative_score += score
            if random_value <= cumulative_score:
                return target
        
        # Fallback to best performing target
        return scored_targets[0][0]
    
    async def _canary_analysis_routing(
        self,
        request: TrafficRequest,
        targets: List[TrafficTarget],
        rule: TrafficSplitRule
    ) -> TrafficTarget:
        """Intelligent canary analysis routing"""
        
        # Identify canary and stable targets
        canary_targets = [t for t in targets if 'canary' in t.version.lower()]
        stable_targets = [t for t in targets if 'canary' not in t.version.lower()]
        
        if not canary_targets or not stable_targets:
            return await self._percentage_based_routing(request, targets)
        
        # Get canary configuration
        canary_config = rule.conditions.get('canary', {})
        current_canary_percentage = canary_config.get('percentage', 10)
        ramp_up_rate = canary_config.get('ramp_up_rate', 5)  # % per hour
        success_threshold = canary_config.get('success_threshold', 0.99)
        
        # Analyze canary performance
        canary_performance = await self._analyze_canary_performance(canary_targets[0])
        
        # Adjust canary percentage based on performance
        if canary_performance['success_rate'] >= success_threshold:
            # Performance is good, consider ramping up
            new_percentage = min(100, current_canary_percentage + ramp_up_rate)
            await self._update_canary_percentage(rule.rule_id, new_percentage)
        elif canary_performance['success_rate'] < success_threshold * 0.95:
            # Performance is poor, ramp down
            new_percentage = max(0, current_canary_percentage - ramp_up_rate * 2)
            await self._update_canary_percentage(rule.rule_id, new_percentage)
        
        # Route based on current canary percentage
        if random.uniform(0, 100) < current_canary_percentage:
            return random.choice(canary_targets)
        else:
            return random.choice(stable_targets)
    
    async def _ab_testing_routing(
        self,
        request: TrafficRequest,
        targets: List[TrafficTarget],
        rule: TrafficSplitRule
    ) -> TrafficTarget:
        """A/B testing routing with statistical significance"""
        
        ab_config = rule.conditions.get('ab_test', {})
        experiment_id = ab_config.get('experiment_id')
        
        if not experiment_id:
            return await self._percentage_based_routing(request, targets)
        
        # Check if user is already assigned to a variant
        user_key = request.user_id or request.session_id
        existing_assignment = await self._get_user_assignment(experiment_id, user_key)
        
        if existing_assignment:
            # Return previously assigned target
            for target in targets:
                if target.name == existing_assignment:
                    return target
        
        # New assignment needed
        experiment_data = self.active_experiments.get(experiment_id, {})
        
        # Check if experiment has reached statistical significance
        if experiment_data.get('statistically_significant', False):
            # Route all new users to winning variant
            winning_variant = experiment_data.get('winning_variant')
            if winning_variant:
                for target in targets:
                    if target.name == winning_variant:
                        await self._assign_user_to_variant(experiment_id, user_key, target.name)
                        return target
        
        # Random assignment for active experiment
        selected_target = await self._percentage_based_routing(request, targets)
        await self._assign_user_to_variant(experiment_id, user_key, selected_target.name)
        
        return selected_target
    
    async def _load_based_routing(
        self,
        request: TrafficRequest,
        targets: List[TrafficTarget]
    ) -> TrafficTarget:
        """Route based on current load and capacity"""
        
        available_targets = []
        
        for target in targets:
            # Check if target has capacity
            if target.max_capacity:
                if target.current_load < target.max_capacity:
                    # Calculate available capacity percentage
                    available_capacity = (target.max_capacity - target.current_load) / target.max_capacity
                    available_targets.append((target, available_capacity))
            else:
                # No capacity limit specified, assume available
                available_targets.append((target, 1.0))
        
        if not available_targets:
            # All targets at capacity, route to least loaded
            least_loaded = min(targets, key=lambda t: t.current_load / (t.max_capacity or 1))
            return least_loaded
        
        # Weight by available capacity
        total_capacity = sum(capacity for _, capacity in available_targets)
        
        if total_capacity == 0:
            return available_targets[0][0]
        
        random_value = random.uniform(0, total_capacity)
        cumulative_capacity = 0
        
        for target, capacity in available_targets:
            cumulative_capacity += capacity
            if random_value <= cumulative_capacity:
                return target
        
        return available_targets[-1][0]
    
    async def create_traffic_split_rule(self, rule_config: Dict[str, Any]) -> TrafficSplitRule:
        """Create a new traffic splitting rule"""
        
        rule = TrafficSplitRule(
            rule_id=rule_config['rule_id'],
            name=rule_config['name'],
            strategy=TrafficSplitStrategy(rule_config['strategy']),
            routing_criteria=RoutingCriteria(rule_config.get('routing_criteria', 'weighted_round_robin')),
            targets=[
                TrafficTarget(**target_config) 
                for target_config in rule_config['targets']
            ],
            conditions=rule_config.get('conditions', {}),
            priority=rule_config.get('priority', 100),
            enabled=rule_config.get('enabled', True),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=rule_config.get('metadata', {})
        )
        
        # Validate rule
        await self._validate_traffic_rule(rule)
        
        # Store rule
        self.rules[rule.rule_id] = rule
        await self._persist_traffic_rule(rule)
        
        self.logger.info(f"Created traffic split rule: {rule.rule_id}")
        
        return rule
    
    async def update_traffic_weights(
        self,
        rule_id: str,
        weight_updates: Dict[str, float]
    ) -> bool:
        """Update traffic weights for a specific rule"""
        
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        
        # Update weights
        for target in rule.targets:
            if target.name in weight_updates:
                target.weight = weight_updates[target.name]
        
        rule.updated_at = datetime.now()
        
        # Persist changes
        await self._persist_traffic_rule(rule)
        
        self.logger.info(f"Updated traffic weights for rule {rule_id}: {weight_updates}")
        
        return True
    
    async def _metrics_collection_loop(self):
        """Background loop for collecting target metrics"""
        
        while True:
            try:
                for rule in self.rules.values():
                    for target in rule.targets:
                        if target.enabled:
                            # Collect performance metrics
                            metrics = await self._collect_target_metrics(target)
                            target.performance_metrics.update(metrics)
                            
                            # Update health score
                            target.health_score = self._calculate_health_score(metrics)
                
                # Update routing statistics
                await self._update_routing_statistics()
                
                await asyncio.sleep(30)  # Collect metrics every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def generate_traffic_split_report(self, rule_id: str, hours: int = 24) -> str:
        """Generate traffic split analysis report"""
        
        if rule_id not in self.rules:
            return f"Rule {rule_id} not found"
        
        rule = self.rules[rule_id]
        
        report = f"""
# Traffic Split Report

**Rule ID:** {rule_id}
**Rule Name:** {rule.name}
**Strategy:** {rule.strategy.value}
**Status:** {'Enabled' if rule.enabled else 'Disabled'}

## Current Configuration
"""
        
        total_weight = sum(t.weight for t in rule.targets)
        for target in rule.targets:
            percentage = (target.weight / total_weight * 100) if total_weight > 0 else 0
            status_icon = "✅" if target.enabled else "❌"
            
            report += f"""
### {status_icon} {target.name} (v{target.version})
- **Weight:** {target.weight} ({percentage:.1f}%)
- **Health Score:** {target.health_score:.2f}
- **Current Load:** {target.current_load}
- **Endpoints:** {len(target.endpoints)}
"""
        
        # Performance metrics
        report += "\n## Performance Metrics\n"
        for target in rule.targets:
            if target.performance_metrics:
                report += f"\n### {target.name}\n"
                for metric, value in target.performance_metrics.items():
                    report += f"- **{metric}:** {value}\n"
        
        # Routing statistics
        if rule_id in self.routing_stats:
            stats = self.routing_stats[rule_id]
            report += f"""
## Routing Statistics (Last {hours}h)
- **Total Requests:** {stats.get('total_requests', 0):,}
- **Success Rate:** {stats.get('success_rate', 0):.2%}
- **Average Response Time:** {stats.get('avg_response_time', 0):.0f}ms
- **Error Rate:** {stats.get('error_rate', 0):.2%}
"""
        
        return report

# Service Mesh Integration
istio_traffic_split_config = """
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: intelligent-traffic-split
  namespace: production
spec:
  hosts:
  - user-service
  http:
  - match:
    - headers:
        user-segment:
          exact: premium
    route:
    - destination:
        host: user-service
        subset: v2-premium
      weight: 70
    - destination:
        host: user-service
        subset: v2-standard  
      weight: 30
    
  - match:
    - headers:
        experiment:
          exact: ab-test-001
    route:
    - destination:
        host: user-service
        subset: v2-variant-a
      weight: 50
    - destination:
        host: user-service
        subset: v2-variant-b
      weight: 50
  
  - match:
    - headers:
        canary-user:
          exact: "true"
    route:
    - destination:
        host: user-service
        subset: v3-canary
      weight: 100
  
  - route:
    - destination:
        host: user-service
        subset: v2-stable
      weight: 90
    - destination:
        host: user-service
        subset: v3-canary
      weight: 10
    fault:
      delay:
        percentage:
          value: 0.1
        fixedDelay: 5s
      abort:
        percentage:
          value: 0.1
        httpStatus: 500

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: user-service-destinations
  namespace: production
spec:
  host: user-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 2
    loadBalancer:
      consistentHash:
        httpHeaderName: "user-id"
    outlierDetection:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  
  subsets:
  - name: v2-stable
    labels:
      version: v2.0.0
      variant: stable
    trafficPolicy:
      connectionPool:
        tcp:
          maxConnections: 80
  
  - name: v2-premium
    labels:
      version: v2.0.0
      variant: premium
    trafficPolicy:
      connectionPool:
        tcp:
          maxConnections: 120
  
  - name: v3-canary
    labels:
      version: v3.0.0
      variant: canary
    trafficPolicy:
      connectionPool:
        tcp:
          maxConnections: 20
      outlierDetection:
        consecutiveErrors: 2
        interval: 15s
        baseEjectionTime: 15s
  
  - name: v2-variant-a
    labels:
      version: v2.0.0
      experiment: variant-a
  
  - name: v2-variant-b
    labels:
      version: v2.0.0
      experiment: variant-b
"""

# Usage example
async def main():
    config = {
        'redis': {
            'host': 'redis',
            'port': 6379,
            'db': 0
        }
    }
    
    splitter = EnterpriseTrafficSplitter(config)
    await splitter.initialize()
    
    # Create a canary deployment rule
    canary_rule_config = {
        'rule_id': 'user-service-canary',
        'name': 'User Service Canary Deployment',
        'strategy': 'canary_analysis',
        'targets': [
            {
                'name': 'stable',
                'version': 'v2.0.0',
                'weight': 90,
                'endpoints': ['user-service-v2:8080'],
                'health_score': 0.95,
                'performance_metrics': {
                    'success_rate': 0.99,
                    'avg_response_time': 150,
                    'error_rate': 0.01
                },
                'metadata': {}
            },
            {
                'name': 'canary',
                'version': 'v3.0.0',
                'weight': 10,
                'endpoints': ['user-service-v3:8080'],
                'health_score': 0.90,
                'performance_metrics': {
                    'success_rate': 0.97,
                    'avg_response_time': 180,
                    'error_rate': 0.03
                },
                'metadata': {}
            }
        ],
        'conditions': {
            'canary': {
                'percentage': 10,
                'success_threshold': 0.99,
                'ramp_up_rate': 5
            }
        }
    }
    
    rule = await splitter.create_traffic_split_rule(canary_rule_config)
    
    # Simulate traffic routing
    for i in range(100):
        request = TrafficRequest(
            request_id=f"req-{i}",
            user_id=f"user-{i % 20}",
            session_id=f"session-{i}",
            ip_address=f"192.168.1.{i % 255}",
            user_agent="Mozilla/5.0...",
            headers={},
            geographic_location={'country': 'US', 'region': 'west'},
            device_info={'type': 'mobile'},
            timestamp=datetime.now()
        )
        
        decision = await splitter.route_traffic(request)
        print(f"Request {i}: routed to {decision.selected_target.name} (confidence: {decision.confidence_score:.2f})")
    
    # Generate report
    report = splitter.generate_traffic_split_report('user-service-canary')
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive traffic splitting system provides enterprise-grade capabilities for intelligent traffic routing, performance-based decisions, A/B testing, canary analysis, and real-time traffic optimization with advanced service mesh integration.