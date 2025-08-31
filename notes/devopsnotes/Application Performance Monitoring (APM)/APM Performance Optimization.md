# APM Performance Optimization

APM Performance Optimization focuses on systematically identifying, analyzing, and resolving application performance bottlenecks through data-driven approaches. This involves profiling, load testing, capacity planning, and implementing targeted optimizations based on APM insights.

## Performance Analysis Framework

### 1. Performance Profiler Integration
```python
import cProfile
import pstats
import io
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
import psutil
import tracemalloc
from functools import wraps

@dataclass
class ProfileMetrics:
    function_name: str
    total_time: float
    cumulative_time: float
    call_count: int
    avg_time_per_call: float
    memory_usage: int = 0
    cpu_percent: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'function': self.function_name,
            'total_time': self.total_time,
            'cumulative_time': self.cumulative_time,
            'calls': self.call_count,
            'avg_time': self.avg_time_per_call,
            'memory_mb': self.memory_usage / 1024 / 1024,
            'cpu_percent': self.cpu_percent
        }

class PerformanceProfiler:
    def __init__(self):
        self.active_profiles: Dict[str, Any] = {}
        self.profile_results: Dict[str, List[ProfileMetrics]] = {}
        self.memory_tracking = False
        self.cpu_tracking = False
        
    def start_memory_tracking(self):
        """Start memory tracking"""
        tracemalloc.start()
        self.memory_tracking = True
    
    def stop_memory_tracking(self):
        """Stop memory tracking"""
        if self.memory_tracking:
            tracemalloc.stop()
            self.memory_tracking = False
    
    @contextmanager
    def profile_context(self, profile_name: str):
        """Context manager for profiling code blocks"""
        profiler = cProfile.Profile()
        start_memory = self._get_memory_usage()
        start_cpu = psutil.cpu_percent()
        
        profiler.enable()
        start_time = time.time()
        
        try:
            yield profiler
        finally:
            end_time = time.time()
            profiler.disable()
            
            end_memory = self._get_memory_usage()
            end_cpu = psutil.cpu_percent()
            
            # Process results
            self._process_profile_results(
                profile_name, profiler, 
                end_time - start_time,
                end_memory - start_memory,
                (end_cpu - start_cpu) if end_cpu > start_cpu else 0
            )
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage"""
        if self.memory_tracking:
            current, peak = tracemalloc.get_traced_memory()
            return current
        return psutil.Process().memory_info().rss
    
    def _process_profile_results(self, profile_name: str, profiler: cProfile.Profile, 
                                duration: float, memory_delta: int, cpu_delta: float):
        """Process and store profiling results"""
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats('cumulative')
        
        # Extract top functions
        metrics = []
        for func_info, (call_count, _, total_time, cumulative_time) in stats.stats.items():
            filename, line_num, func_name = func_info
            
            if call_count > 0:
                metric = ProfileMetrics(
                    function_name=f"{filename}:{line_num}({func_name})",
                    total_time=total_time,
                    cumulative_time=cumulative_time,
                    call_count=call_count,
                    avg_time_per_call=total_time / call_count,
                    memory_usage=memory_delta,
                    cpu_percent=cpu_delta
                )
                metrics.append(metric)
        
        # Sort by cumulative time and keep top 20
        metrics.sort(key=lambda x: x.cumulative_time, reverse=True)
        self.profile_results[profile_name] = metrics[:20]
    
    def get_hotspots(self, profile_name: str, limit: int = 10) -> List[ProfileMetrics]:
        """Get performance hotspots"""
        return self.profile_results.get(profile_name, [])[:limit]
    
    def profile_decorator(self, profile_name: str = None):
        """Decorator for profiling functions"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = profile_name or f"{func.__module__}.{func.__name__}"
                with self.profile_context(name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

# Global profiler instance
profiler = PerformanceProfiler()

# Usage examples
@profiler.profile_decorator("critical_function")
def critical_business_logic():
    # Simulate complex operation
    time.sleep(0.1)
    return sum(i*i for i in range(10000))
```

### 2. Database Query Optimization
```python
import sqlalchemy as sa
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import time
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Set

@dataclass
class QueryAnalysis:
    query: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    query_hash: str
    timestamp: float
    explain_plan: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'query': self.query[:200] + '...' if len(self.query) > 200 else self.query,
            'execution_time': self.execution_time,
            'rows_examined': self.rows_examined,
            'rows_returned': self.rows_returned,
            'efficiency_ratio': self.rows_returned / max(self.rows_examined, 1),
            'timestamp': self.timestamp,
            'explain_plan': self.explain_plan
        }

class DatabaseOptimizer:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.slow_queries: List[QueryAnalysis] = []
        self.query_stats: Dict[str, List[float]] = defaultdict(list)
        self.slow_query_threshold = 1.0  # seconds
        self.missing_indexes: Set[str] = set()
        self.setup_query_monitoring()
    
    def setup_query_monitoring(self):
        """Setup automatic query monitoring"""
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute") 
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            execution_time = time.time() - context._query_start_time
            
            # Log slow queries
            if execution_time > self.slow_query_threshold:
                self._analyze_slow_query(statement, execution_time, cursor.rowcount)
    
    def _analyze_slow_query(self, query: str, execution_time: float, row_count: int):
        """Analyze slow query and store results"""
        query_hash = str(hash(query.strip()))
        
        analysis = QueryAnalysis(
            query=query,
            execution_time=execution_time,
            rows_examined=row_count,  # Simplified - would need actual examined count
            rows_returned=row_count,
            query_hash=query_hash,
            timestamp=time.time()
        )
        
        # Get explain plan for slow queries
        try:
            explain_result = self._get_explain_plan(query)
            analysis.explain_plan = explain_result
            self._check_missing_indexes(explain_result)
        except Exception as e:
            logging.warning(f"Could not get explain plan: {e}")
        
        self.slow_queries.append(analysis)
        self.query_stats[query_hash].append(execution_time)
        
        logging.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}...")
    
    def _get_explain_plan(self, query: str) -> str:
        """Get query execution plan"""
        with self.engine.connect() as conn:
            # PostgreSQL EXPLAIN
            if 'postgresql' in str(self.engine.url):
                result = conn.execute(text(f"EXPLAIN ANALYZE {query}"))
                return '\n'.join([row[0] for row in result])
            
            # MySQL EXPLAIN  
            elif 'mysql' in str(self.engine.url):
                result = conn.execute(text(f"EXPLAIN FORMAT=JSON {query}"))
                return str(result.fetchone()[0])
            
            return "Explain plan not available"
    
    def _check_missing_indexes(self, explain_plan: str):
        """Check for missing indexes in explain plan"""
        # Simple heuristic - look for table scans
        if any(keyword in explain_plan.lower() for keyword in 
               ['seq scan', 'table scan', 'full table scan']):
            # Extract table names (simplified)
            import re
            tables = re.findall(r'on\s+(\w+)', explain_plan.lower())
            for table in tables:
                self.missing_indexes.add(f"Consider index on table: {table}")
    
    def get_optimization_recommendations(self) -> List[Dict]:
        """Get database optimization recommendations"""
        recommendations = []
        
        # Analyze slow queries
        if self.slow_queries:
            # Group by query pattern
            query_patterns = defaultdict(list)
            for analysis in self.slow_queries:
                pattern = self._extract_query_pattern(analysis.query)
                query_patterns[pattern].append(analysis)
            
            for pattern, queries in query_patterns.items():
                avg_time = sum(q.execution_time for q in queries) / len(queries)
                total_time = sum(q.execution_time for q in queries)
                
                recommendations.append({
                    'type': 'slow_query',
                    'priority': 'high' if avg_time > 5.0 else 'medium',
                    'query_pattern': pattern,
                    'occurrences': len(queries),
                    'avg_execution_time': avg_time,
                    'total_time_impact': total_time,
                    'recommendation': f"Optimize query pattern: {pattern[:100]}..."
                })
        
        # Add index recommendations
        for index_rec in self.missing_indexes:
            recommendations.append({
                'type': 'missing_index',
                'priority': 'medium',
                'recommendation': index_rec
            })
        
        return sorted(recommendations, key=lambda x: x.get('total_time_impact', 0), reverse=True)
    
    def _extract_query_pattern(self, query: str) -> str:
        """Extract query pattern by removing literals"""
        import re
        # Replace string literals
        pattern = re.sub(r"'[^']*'", "'?'", query)
        # Replace numeric literals
        pattern = re.sub(r'\b\d+\b', '?', pattern)
        # Replace IN clauses
        pattern = re.sub(r'IN\s*\([^)]*\)', 'IN (?)', pattern)
        return pattern

    def suggest_query_optimizations(self, query: str) -> List[str]:
        """Suggest specific optimizations for a query"""
        suggestions = []
        query_lower = query.lower()
        
        # Check for common anti-patterns
        if 'select *' in query_lower:
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        if 'or' in query_lower and 'where' in query_lower:
            suggestions.append("Consider rewriting OR conditions with UNION for better index usage")
        
        if 'like %' in query_lower:
            suggestions.append("Leading wildcard searches cannot use indexes efficiently")
        
        if 'order by' in query_lower and 'limit' in query_lower:
            suggestions.append("Ensure columns in ORDER BY have appropriate indexes")
        
        if query_lower.count('join') > 3:
            suggestions.append("Consider breaking complex joins into smaller operations")
        
        return suggestions
```

### 3. Memory Optimization Framework
```python
import gc
import sys
import weakref
from typing import Any, Dict, List, Optional
import objgraph
import psutil
import threading
import time
from collections import defaultdict

class MemoryOptimizer:
    def __init__(self):
        self.memory_snapshots: List[Dict] = []
        self.object_growth_tracking: Dict[str, List[int]] = defaultdict(list)
        self.memory_leaks: List[Dict] = []
        self.gc_stats: List[Dict] = []
        self.monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous memory monitoring"""
        self.monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_memory, 
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join()
    
    def _monitor_memory(self, interval: int):
        """Internal memory monitoring loop"""
        while self.monitoring_active:
            try:
                snapshot = self.take_memory_snapshot()
                self.memory_snapshots.append(snapshot)
                
                # Keep only last 100 snapshots
                if len(self.memory_snapshots) > 100:
                    self.memory_snapshots.pop(0)
                
                # Analyze for memory leaks
                self._analyze_memory_trends()
                
                time.sleep(interval)
            except Exception as e:
                logging.error(f"Memory monitoring error: {e}")
                time.sleep(interval)
    
    def take_memory_snapshot(self) -> Dict:
        """Take detailed memory snapshot"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Get object counts by type
        object_counts = objgraph.typestats()
        
        # Get garbage collection stats
        gc_stats = {
            f'generation_{i}': {
                'count': gc.get_count()[i],
                'threshold': gc.get_threshold()[i]
            }
            for i in range(3)
        }
        
        snapshot = {
            'timestamp': time.time(),
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'object_counts': dict(object_counts[:20]),  # Top 20 object types
            'gc_stats': gc_stats,
            'total_objects': len(gc.get_objects())
        }
        
        # Track object growth
        for obj_type, count in object_counts[:10]:
            self.object_growth_tracking[obj_type].append(count)
            # Keep only last 50 measurements
            if len(self.object_growth_tracking[obj_type]) > 50:
                self.object_growth_tracking[obj_type].pop(0)
        
        return snapshot
    
    def _analyze_memory_trends(self):
        """Analyze memory usage trends for leaks"""
        if len(self.memory_snapshots) < 10:
            return
        
        # Check for consistent memory growth
        recent_snapshots = self.memory_snapshots[-10:]
        memory_values = [s['rss_mb'] for s in recent_snapshots]
        
        # Simple linear trend analysis
        if len(memory_values) >= 5:
            growth_rate = (memory_values[-1] - memory_values[0]) / len(memory_values)
            if growth_rate > 10:  # Growing more than 10MB per snapshot
                self.memory_leaks.append({
                    'detected_at': time.time(),
                    'growth_rate_mb': growth_rate,
                    'current_usage_mb': memory_values[-1],
                    'trend': 'increasing'
                })
    
    def get_memory_report(self) -> Dict:
        """Generate comprehensive memory report"""
        if not self.memory_snapshots:
            return {'error': 'No memory snapshots available'}
        
        latest = self.memory_snapshots[-1]
        
        report = {
            'current_usage': {
                'rss_mb': latest['rss_mb'],
                'vms_mb': latest['vms_mb'],
                'percent': latest['percent'],
                'total_objects': latest['total_objects']
            },
            'top_object_types': latest['object_counts'],
            'memory_leaks_detected': len(self.memory_leaks),
            'recommendations': self._generate_memory_recommendations()
        }
        
        # Add trend analysis if enough data
        if len(self.memory_snapshots) >= 5:
            memory_history = [s['rss_mb'] for s in self.memory_snapshots[-10:]]
            report['trend_analysis'] = {
                'memory_growth_trend': 'increasing' if memory_history[-1] > memory_history[0] else 'stable',
                'peak_usage_mb': max(memory_history),
                'average_usage_mb': sum(memory_history) / len(memory_history)
            }
        
        return report
    
    def _generate_memory_recommendations(self) -> List[str]:
        """Generate memory optimization recommendations"""
        recommendations = []
        
        if not self.memory_snapshots:
            return recommendations
        
        latest = self.memory_snapshots[-1]
        
        # High memory usage
        if latest['percent'] > 80:
            recommendations.append("Memory usage is high (>80%). Consider optimizing data structures or increasing available memory.")
        
        # Many objects
        if latest['total_objects'] > 1000000:
            recommendations.append("High object count detected. Consider object pooling or more efficient data structures.")
        
        # Check for potential leaks
        if self.memory_leaks:
            recommendations.append(f"Potential memory leaks detected ({len(self.memory_leaks)} instances). Review object lifecycle management.")
        
        # Garbage collection recommendations
        gc_stats = latest.get('gc_stats', {})
        for gen, stats in gc_stats.items():
            if stats['count'] > stats['threshold'] * 0.8:
                recommendations.append(f"Garbage collection {gen} is frequently triggered. Consider manual gc.collect() in appropriate places.")
        
        return recommendations
    
    def force_garbage_collection(self) -> Dict:
        """Force garbage collection and return results"""
        before_objects = len(gc.get_objects())
        before_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Collect all generations
        collected = []
        for generation in range(3):
            collected.append(gc.collect(generation))
        
        after_objects = len(gc.get_objects())
        after_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        result = {
            'objects_collected': collected,
            'objects_before': before_objects,
            'objects_after': after_objects,
            'objects_freed': before_objects - after_objects,
            'memory_before_mb': before_memory,
            'memory_after_mb': after_memory,
            'memory_freed_mb': before_memory - after_memory
        }
        
        self.gc_stats.append({
            'timestamp': time.time(),
            **result
        })
        
        return result

    def find_memory_leaks(self) -> List[Dict]:
        """Find potential memory leaks using object growth analysis"""
        leaks = []
        
        for obj_type, counts in self.object_growth_tracking.items():
            if len(counts) >= 10:
                # Check for consistent growth
                growth_trend = sum(counts[-5:]) / 5 - sum(counts[:5]) / 5
                if growth_trend > 100:  # More than 100 objects growth on average
                    leaks.append({
                        'object_type': obj_type,
                        'growth_trend': growth_trend,
                        'current_count': counts[-1],
                        'severity': 'high' if growth_trend > 1000 else 'medium'
                    })
        
        return sorted(leaks, key=lambda x: x['growth_trend'], reverse=True)
```

### 4. Load Testing Integration
```python
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Callable, Optional

@dataclass
class LoadTestResult:
    request_count: int
    success_count: int
    error_count: int
    response_times: List[float]
    error_details: List[str]
    throughput_rps: float
    
    @property
    def success_rate(self) -> float:
        return (self.success_count / self.request_count) * 100 if self.request_count > 0 else 0
    
    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def p95_response_time(self) -> float:
        return statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else 0
    
    @property
    def p99_response_time(self) -> float:
        return statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else 0
    
    def to_dict(self) -> Dict:
        return {
            'request_count': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'p95_response_time': self.p95_response_time,
            'p99_response_time': self.p99_response_time,
            'throughput_rps': self.throughput_rps,
            'error_details': self.error_details[:10]  # Limit error details
        }

class LoadTester:
    def __init__(self):
        self.results_history: List[LoadTestResult] = []
    
    async def run_load_test(self, 
                           url: str,
                           concurrent_users: int = 10,
                           duration_seconds: int = 60,
                           request_data: Optional[Dict] = None,
                           headers: Optional[Dict] = None) -> LoadTestResult:
        """Run load test with specified parameters"""
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        results = {
            'responses': [],
            'errors': []
        }
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def make_request(session: aiohttp.ClientSession):
            async with semaphore:
                try:
                    request_start = time.time()
                    
                    if request_data:
                        async with session.post(url, json=request_data, headers=headers) as response:
                            await response.text()  # Ensure response is fully read
                    else:
                        async with session.get(url, headers=headers) as response:
                            await response.text()
                    
                    request_time = time.time() - request_start
                    results['responses'].append({
                        'time': request_time,
                        'status': response.status,
                        'success': 200 <= response.status < 300
                    })
                    
                except Exception as e:
                    results['errors'].append(str(e))
        
        # Run concurrent requests until duration expires
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=concurrent_users * 2)
        ) as session:
            
            tasks = []
            while time.time() < end_time:
                if len(tasks) < concurrent_users:
                    task = asyncio.create_task(make_request(session))
                    tasks.append(task)
                
                # Clean up completed tasks
                tasks = [task for task in tasks if not task.done()]
                
                await asyncio.sleep(0.01)  # Small delay to prevent tight loop
            
            # Wait for remaining tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        total_requests = len(results['responses']) + len(results['errors'])
        successful_requests = sum(1 for r in results['responses'] if r['success'])
        response_times = [r['time'] for r in results['responses']]
        actual_duration = time.time() - start_time
        
        result = LoadTestResult(
            request_count=total_requests,
            success_count=successful_requests,
            error_count=len(results['errors']),
            response_times=response_times,
            error_details=results['errors'],
            throughput_rps=total_requests / actual_duration if actual_duration > 0 else 0
        )
        
        self.results_history.append(result)
        return result
    
    def run_capacity_test(self, 
                         url: str,
                         max_users: int = 100,
                         step_size: int = 10,
                         step_duration: int = 30) -> List[LoadTestResult]:
        """Run capacity test to find breaking point"""
        
        results = []
        
        async def capacity_test():
            for users in range(step_size, max_users + 1, step_size):
                print(f"Testing with {users} concurrent users...")
                
                result = await self.run_load_test(
                    url=url,
                    concurrent_users=users,
                    duration_seconds=step_duration
                )
                
                results.append(result)
                
                # Stop if error rate is too high or response time is too slow
                if result.success_rate < 95 or result.p95_response_time > 5.0:
                    print(f"Breaking point found at {users} users")
                    break
                    
                # Brief pause between steps
                await asyncio.sleep(5)
        
        asyncio.run(capacity_test())
        return results
    
    def analyze_performance_trends(self) -> Dict:
        """Analyze performance trends from test history"""
        if len(self.results_history) < 2:
            return {'error': 'Insufficient data for trend analysis'}
        
        recent_results = self.results_history[-10:]  # Last 10 tests
        
        avg_response_times = [r.avg_response_time for r in recent_results]
        success_rates = [r.success_rate for r in recent_results]
        throughputs = [r.throughput_rps for r in recent_results]
        
        return {
            'performance_trend': {
                'avg_response_time': {
                    'current': avg_response_times[-1],
                    'trend': 'improving' if avg_response_times[-1] < avg_response_times[0] else 'degrading',
                    'change_percent': ((avg_response_times[-1] - avg_response_times[0]) / avg_response_times[0]) * 100
                },
                'success_rate': {
                    'current': success_rates[-1],
                    'trend': 'improving' if success_rates[-1] > success_rates[0] else 'degrading',
                    'change_percent': success_rates[-1] - success_rates[0]
                },
                'throughput': {
                    'current': throughputs[-1],
                    'trend': 'improving' if throughputs[-1] > throughputs[0] else 'degrading',
                    'change_percent': ((throughputs[-1] - throughputs[0]) / throughputs[0]) * 100
                }
            },
            'recommendations': self._generate_load_test_recommendations(recent_results[-1])
        }
    
    def _generate_load_test_recommendations(self, result: LoadTestResult) -> List[str]:
        """Generate optimization recommendations based on load test results"""
        recommendations = []
        
        if result.success_rate < 99:
            recommendations.append(f"Success rate is {result.success_rate:.1f}%. Investigate error causes and improve error handling.")
        
        if result.avg_response_time > 1.0:
            recommendations.append(f"Average response time is {result.avg_response_time:.2f}s. Consider performance optimizations.")
        
        if result.p95_response_time > 3.0:
            recommendations.append(f"95th percentile response time is {result.p95_response_time:.2f}s. Optimize slow requests.")
        
        if result.throughput_rps < 100:
            recommendations.append(f"Throughput is {result.throughput_rps:.1f} RPS. Consider scaling or performance improvements.")
        
        return recommendations
```

### 5. Performance Optimization Strategies
```python
class PerformanceOptimizationEngine:
    def __init__(self):
        self.optimization_rules: List[Dict] = [
            {
                'name': 'database_connection_pooling',
                'condition': lambda metrics: metrics.get('db_connection_time', 0) > 0.1,
                'recommendation': 'Implement database connection pooling to reduce connection overhead',
                'priority': 'high',
                'implementation': self._implement_db_pooling
            },
            {
                'name': 'response_caching',
                'condition': lambda metrics: metrics.get('cache_hit_rate', 100) < 80,
                'recommendation': 'Improve caching strategy to increase cache hit rate',
                'priority': 'medium',
                'implementation': self._implement_caching
            },
            {
                'name': 'query_optimization',
                'condition': lambda metrics: metrics.get('slow_query_count', 0) > 10,
                'recommendation': 'Optimize slow database queries',
                'priority': 'high',
                'implementation': self._optimize_queries
            },
            {
                'name': 'memory_optimization',
                'condition': lambda metrics: metrics.get('memory_usage_percent', 0) > 80,
                'recommendation': 'Implement memory optimization techniques',
                'priority': 'high',
                'implementation': self._optimize_memory
            }
        ]
    
    def analyze_and_recommend(self, performance_metrics: Dict) -> List[Dict]:
        """Analyze metrics and provide optimization recommendations"""
        recommendations = []
        
        for rule in self.optimization_rules:
            try:
                if rule['condition'](performance_metrics):
                    recommendations.append({
                        'name': rule['name'],
                        'recommendation': rule['recommendation'],
                        'priority': rule['priority'],
                        'current_value': self._extract_relevant_metric(rule['name'], performance_metrics),
                        'implementation_available': rule['implementation'] is not None
                    })
            except Exception as e:
                logging.error(f"Error evaluating optimization rule {rule['name']}: {e}")
        
        return sorted(recommendations, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)
    
    def _extract_relevant_metric(self, rule_name: str, metrics: Dict) -> Any:
        """Extract relevant metric for the rule"""
        metric_mappings = {
            'database_connection_pooling': metrics.get('db_connection_time'),
            'response_caching': metrics.get('cache_hit_rate'),
            'query_optimization': metrics.get('slow_query_count'),
            'memory_optimization': metrics.get('memory_usage_percent')
        }
        return metric_mappings.get(rule_name, 'N/A')
    
    def _implement_db_pooling(self, config: Dict) -> str:
        """Generate database pooling implementation"""
        return """
# Database Connection Pooling Implementation
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

# Configure connection pooling
engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,          # Number of connections to maintain
    max_overflow=30,       # Additional connections allowed
    pool_recycle=3600,     # Recycle connections every hour
    pool_pre_ping=True     # Validate connections before use
)

# Connection pool monitoring
def monitor_pool():
    pool = engine.pool
    return {
        'size': pool.size(),
        'checked_in': pool.checkedin(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'invalid': pool.invalid()
    }
"""
    
    def _implement_caching(self, config: Dict) -> str:
        """Generate caching implementation"""
        return """
# Response Caching Implementation
import redis
from functools import wraps
import pickle
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_response(expiry=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"cache:{func.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return pickle.loads(cached_result)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiry, pickle.dumps(result))
            return result
        return wrapper
    return decorator

# Usage example
@cache_response(expiry=600)
def expensive_computation(data):
    # Expensive operation
    return processed_data
"""
    
    def _optimize_queries(self, config: Dict) -> str:
        """Generate query optimization implementation"""
        return """
# Database Query Optimization
from sqlalchemy import Index, text

# Add indexes for slow queries
def create_optimization_indexes():
    # Example indexes based on common slow query patterns
    indexes = [
        Index('idx_users_email_status', 'email', 'status'),
        Index('idx_orders_user_created', 'user_id', 'created_at'),
        Index('idx_products_category_price', 'category_id', 'price')
    ]
    
    for index in indexes:
        try:
            index.create(engine)
            print(f"Created index: {index.name}")
        except Exception as e:
            print(f"Index creation failed: {e}")

# Query optimization techniques
def optimize_query_patterns():
    # Use query.options() for eager loading
    from sqlalchemy.orm import joinedload
    
    # Instead of N+1 queries
    users = session.query(User).options(joinedload(User.orders)).all()
    
    # Use bulk operations for large datasets
    session.bulk_update_mappings(User, user_updates)
    
    # Use raw SQL for complex queries
    result = session.execute(text("SELECT * FROM optimized_view WHERE condition = :param"), {"param": value})
"""
    
    def _optimize_memory(self, config: Dict) -> str:
        """Generate memory optimization implementation"""
        return """
# Memory Optimization Implementation
import gc
from functools import lru_cache
import weakref

# Object pooling for frequently created objects
class ObjectPool:
    def __init__(self, create_func, reset_func=None):
        self._create_func = create_func
        self._reset_func = reset_func
        self._pool = []
    
    def acquire(self):
        if self._pool:
            obj = self._pool.pop()
            return obj
        return self._create_func()
    
    def release(self, obj):
        if self._reset_func:
            self._reset_func(obj)
        self._pool.append(obj)

# Memory-efficient data structures
def use_slots_classes():
    class EfficientClass:
        __slots__ = ['attr1', 'attr2', 'attr3']
        
        def __init__(self, attr1, attr2, attr3):
            self.attr1 = attr1
            self.attr2 = attr2
            self.attr3 = attr3

# Lazy loading for large datasets
class LazyLoader:
    def __init__(self, loader_func):
        self._loader_func = loader_func
        self._data = None
        self._loaded = False
    
    @property
    def data(self):
        if not self._loaded:
            self._data = self._loader_func()
            self._loaded = True
        return self._data

# Regular garbage collection
def setup_gc_optimization():
    gc.set_threshold(700, 10, 10)  # Tune GC thresholds
    
    # Periodic cleanup
    import threading
    import time
    
    def periodic_cleanup():
        while True:
            time.sleep(300)  # Every 5 minutes
            collected = gc.collect()
            if collected > 0:
                print(f"Garbage collected {collected} objects")
    
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
"""

# Usage example combining all optimization techniques
async def comprehensive_performance_optimization():
    # Initialize components
    profiler = PerformanceProfiler()
    memory_optimizer = MemoryOptimizer()
    load_tester = LoadTester()
    db_optimizer = DatabaseOptimizer(engine)
    optimization_engine = PerformanceOptimizationEngine()
    
    # Start monitoring
    profiler.start_memory_tracking()
    memory_optimizer.start_monitoring(interval=30)
    
    try:
        # Profile critical functions
        with profiler.profile_context("app_startup"):
            # Application initialization code
            pass
        
        # Run load test
        load_result = await load_tester.run_load_test(
            url="http://localhost:8000/api/health",
            concurrent_users=50,
            duration_seconds=120
        )
        
        # Collect performance metrics
        performance_metrics = {
            'db_connection_time': 0.15,
            'cache_hit_rate': 75,
            'slow_query_count': 25,
            'memory_usage_percent': 85,
            'avg_response_time': load_result.avg_response_time,
            'p95_response_time': load_result.p95_response_time,
            'throughput_rps': load_result.throughput_rps
        }
        
        # Get optimization recommendations
        recommendations = optimization_engine.analyze_and_recommend(performance_metrics)
        
        # Generate comprehensive report
        report = {
            'performance_profile': profiler.get_hotspots("app_startup"),
            'memory_analysis': memory_optimizer.get_memory_report(),
            'load_test_results': load_result.to_dict(),
            'database_analysis': db_optimizer.get_optimization_recommendations(),
            'optimization_recommendations': recommendations,
            'timestamp': time.time()
        }
        
        return report
        
    finally:
        # Cleanup
        memory_optimizer.stop_monitoring()
        profiler.stop_memory_tracking()

# Run the comprehensive optimization
if __name__ == "__main__":
    result = asyncio.run(comprehensive_performance_optimization())
    print(json.dumps(result, indent=2, default=str))
```

This comprehensive APM Performance Optimization framework provides systematic approaches to identify, analyze, and resolve performance bottlenecks through profiling, database optimization, memory management, load testing, and automated optimization recommendations.