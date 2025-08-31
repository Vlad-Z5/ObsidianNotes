# APM Database Performance Monitoring

Database performance monitoring is critical for application performance as databases are often the bottleneck in distributed systems. This guide covers database metrics collection, query performance analysis, connection pool monitoring, and enterprise-grade database monitoring implementations for various database systems including PostgreSQL, MySQL, MongoDB, and Redis.

## Database Performance Monitoring Framework

### Universal Database Metrics Collector

```python
import time
import threading
import psutil
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from abc import ABC, abstractmethod
import statistics
import re

@dataclass
class DatabaseMetric:
    name: str
    value: float
    unit: str
    timestamp: datetime
    database: str
    instance: str
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class QueryMetric:
    query_id: str
    query_hash: str
    normalized_query: str
    execution_time_ms: float
    rows_examined: int
    rows_returned: int
    database: str
    table: str
    operation: str  # SELECT, INSERT, UPDATE, DELETE
    timestamp: datetime
    connection_id: Optional[str] = None
    user: Optional[str] = None
    error: Optional[str] = None

class DatabaseMonitor(ABC):
    """Abstract base class for database monitors"""
    
    def __init__(self, connection_string: str, instance_name: str):
        self.connection_string = connection_string
        self.instance_name = instance_name
        self.metrics_buffer = deque(maxlen=10000)
        self.query_buffer = deque(maxlen=5000)
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f"db_monitor_{instance_name}")
        
    @abstractmethod
    def collect_system_metrics(self) -> List[DatabaseMetric]:
        """Collect database system-level metrics"""
        pass
    
    @abstractmethod
    def collect_query_metrics(self) -> List[QueryMetric]:
        """Collect query performance metrics"""
        pass
    
    @abstractmethod
    def get_slow_queries(self, limit: int = 10) -> List[QueryMetric]:
        """Get slowest queries"""
        pass
    
    def add_metric(self, metric: DatabaseMetric):
        """Add metric to buffer"""
        with self.lock:
            self.metrics_buffer.append(metric)
    
    def add_query_metric(self, query_metric: QueryMetric):
        """Add query metric to buffer"""
        with self.lock:
            self.query_buffer.append(query_metric)
    
    def get_metrics_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Get metrics summary for the last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        with self.lock:
            recent_metrics = [m for m in self.metrics_buffer 
                            if m.timestamp > cutoff_time]
            recent_queries = [q for q in self.query_buffer 
                            if q.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_name[metric.name].append(metric.value)
        
        # Calculate statistics
        summary = {
            'instance': self.instance_name,
            'time_window_minutes': minutes,
            'metrics': {},
            'query_stats': {
                'total_queries': len(recent_queries),
                'avg_execution_time_ms': 0,
                'slow_queries_count': 0
            }
        }
        
        for metric_name, values in metrics_by_name.items():
            if values:
                summary['metrics'][metric_name] = {
                    'current': values[-1],
                    'average': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        # Query statistics
        if recent_queries:
            execution_times = [q.execution_time_ms for q in recent_queries if q.execution_time_ms]
            if execution_times:
                summary['query_stats']['avg_execution_time_ms'] = statistics.mean(execution_times)
                summary['query_stats']['slow_queries_count'] = len([t for t in execution_times if t > 1000])
        
        return summary

class PostgreSQLMonitor(DatabaseMonitor):
    """PostgreSQL-specific database monitor"""
    
    def __init__(self, connection_string: str, instance_name: str):
        super().__init__(connection_string, instance_name)
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            import psycopg2
            self.connection = psycopg2.connect(self.connection_string)
            self.connection.autocommit = True
            self.logger.info(f"Connected to PostgreSQL instance: {self.instance_name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def collect_system_metrics(self) -> List[DatabaseMetric]:
        """Collect PostgreSQL system metrics"""
        metrics = []
        
        if not self.connection:
            return metrics
        
        try:
            cursor = self.connection.cursor()
            timestamp = datetime.utcnow()
            
            # Database size
            cursor.execute("""
                SELECT datname, pg_database_size(datname) as size_bytes
                FROM pg_database 
                WHERE datistemplate = false
            """)
            
            for row in cursor.fetchall():
                metrics.append(DatabaseMetric(
                    name="database_size_bytes",
                    value=float(row[1]),
                    unit="bytes",
                    timestamp=timestamp,
                    database=row[0],
                    instance=self.instance_name
                ))
            
            # Connection statistics
            cursor.execute("""
                SELECT state, count(*) as count
                FROM pg_stat_activity
                GROUP BY state
            """)
            
            for row in cursor.fetchall():
                metrics.append(DatabaseMetric(
                    name=f"connections_{row[0] or 'unknown'}",
                    value=float(row[1]),
                    unit="count",
                    timestamp=timestamp,
                    database="all",
                    instance=self.instance_name
                ))
            
            # Cache hit ratio
            cursor.execute("""
                SELECT 
                    round(
                        (blks_hit * 100.0) / (blks_hit + blks_read), 2
                    ) as cache_hit_ratio
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            
            result = cursor.fetchone()
            if result and result[0]:
                metrics.append(DatabaseMetric(
                    name="cache_hit_ratio",
                    value=float(result[0]),
                    unit="percent",
                    timestamp=timestamp,
                    database="current",
                    instance=self.instance_name
                ))
            
            # Transaction statistics
            cursor.execute("""
                SELECT 
                    xact_commit,
                    xact_rollback,
                    tup_returned,
                    tup_fetched,
                    tup_inserted,
                    tup_updated,
                    tup_deleted
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            
            result = cursor.fetchone()
            if result:
                metric_names = [
                    "transactions_committed", "transactions_rolled_back",
                    "tuples_returned", "tuples_fetched", 
                    "tuples_inserted", "tuples_updated", "tuples_deleted"
                ]
                
                for i, value in enumerate(result):
                    if value is not None:
                        metrics.append(DatabaseMetric(
                            name=metric_names[i],
                            value=float(value),
                            unit="count",
                            timestamp=timestamp,
                            database="current",
                            instance=self.instance_name
                        ))
            
            # Lock statistics
            cursor.execute("""
                SELECT mode, count(*) as count
                FROM pg_locks 
                WHERE NOT granted 
                GROUP BY mode
            """)
            
            total_locks = 0
            for row in cursor.fetchall():
                lock_count = row[1]
                total_locks += lock_count
                metrics.append(DatabaseMetric(
                    name=f"locks_waiting_{row[0].lower()}",
                    value=float(lock_count),
                    unit="count",
                    timestamp=timestamp,
                    database="all",
                    instance=self.instance_name
                ))
            
            metrics.append(DatabaseMetric(
                name="locks_waiting_total",
                value=float(total_locks),
                unit="count",
                timestamp=timestamp,
                database="all",
                instance=self.instance_name
            ))
            
            # Index usage
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_tup_read DESC
                LIMIT 10
            """)
            
            for row in cursor.fetchall():
                metrics.append(DatabaseMetric(
                    name="index_tuples_read",
                    value=float(row[3]),
                    unit="count",
                    timestamp=timestamp,
                    database="current",
                    instance=self.instance_name,
                    tags={
                        "schema": row[0],
                        "table": row[1],
                        "index": row[2]
                    }
                ))
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Error collecting PostgreSQL metrics: {e}")
        
        return metrics
    
    def collect_query_metrics(self) -> List[QueryMetric]:
        """Collect PostgreSQL query performance metrics"""
        query_metrics = []
        
        if not self.connection:
            return query_metrics
        
        try:
            cursor = self.connection.cursor()
            
            # Get query statistics from pg_stat_statements
            cursor.execute("""
                SELECT 
                    queryid,
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    min_exec_time,
                    max_exec_time,
                    rows
                FROM pg_stat_statements
                ORDER BY mean_exec_time DESC
                LIMIT 50
            """)
            
            for row in cursor.fetchall():
                normalized_query = self._normalize_query(row[1])
                operation = self._extract_operation(normalized_query)
                
                query_metrics.append(QueryMetric(
                    query_id=str(row[0]),
                    query_hash=str(row[0]),
                    normalized_query=normalized_query[:500],  # Limit length
                    execution_time_ms=float(row[4]),  # mean_exec_time
                    rows_examined=int(row[7]) if row[7] else 0,
                    rows_returned=int(row[7]) if row[7] else 0,
                    database="current",
                    table=self._extract_table_name(normalized_query),
                    operation=operation,
                    timestamp=datetime.utcnow()
                ))
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Error collecting PostgreSQL query metrics: {e}")
        
        return query_metrics
    
    def get_slow_queries(self, limit: int = 10) -> List[QueryMetric]:
        """Get slowest PostgreSQL queries"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT 
                    queryid,
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_exec_time > 100  -- Queries slower than 100ms
                ORDER BY mean_exec_time DESC
                LIMIT %s
            """, (limit,))
            
            slow_queries = []
            for row in cursor.fetchall():
                normalized_query = self._normalize_query(row[1])
                
                slow_queries.append(QueryMetric(
                    query_id=str(row[0]),
                    query_hash=str(row[0]),
                    normalized_query=normalized_query[:500],
                    execution_time_ms=float(row[4]),  # mean_exec_time
                    rows_examined=int(row[6]) if row[6] else 0,
                    rows_returned=int(row[6]) if row[6] else 0,
                    database="current",
                    table=self._extract_table_name(normalized_query),
                    operation=self._extract_operation(normalized_query),
                    timestamp=datetime.utcnow(),
                    tags={
                        "calls": str(row[2]),
                        "total_time": str(row[3]),
                        "max_time": str(row[5])
                    }
                ))
            
            cursor.close()
            return slow_queries
            
        except Exception as e:
            self.logger.error(f"Error getting slow PostgreSQL queries: {e}")
            return []
    
    def _normalize_query(self, query: str) -> str:
        """Normalize SQL query by removing literals"""
        if not query:
            return ""
        
        # Remove string literals
        normalized = re.sub(r"'[^']*'", "'?'", query)
        # Remove numeric literals
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        # Remove whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _extract_operation(self, query: str) -> str:
        """Extract operation type from SQL query"""
        if not query:
            return "UNKNOWN"
        
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _extract_table_name(self, query: str) -> str:
        """Extract primary table name from SQL query"""
        if not query:
            return "unknown"
        
        # Simple regex to extract table name - can be improved
        from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        if from_match:
            return from_match.group(1)
        
        into_match = re.search(r'INTO\s+(\w+)', query, re.IGNORECASE)
        if into_match:
            return into_match.group(1)
        
        update_match = re.search(r'UPDATE\s+(\w+)', query, re.IGNORECASE)
        if update_match:
            return update_match.group(1)
        
        return "unknown"

class MySQLMonitor(DatabaseMonitor):
    """MySQL-specific database monitor"""
    
    def __init__(self, connection_string: str, instance_name: str):
        super().__init__(connection_string, instance_name)
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish MySQL database connection"""
        try:
            import mysql.connector
            # Parse connection string or use direct parameters
            self.connection = mysql.connector.connect(
                host='localhost',  # Parse from connection_string
                database='performance_schema',
                user='monitor_user',
                password='monitor_pass'
            )
            self.logger.info(f"Connected to MySQL instance: {self.instance_name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL: {e}")
            raise
    
    def collect_system_metrics(self) -> List[DatabaseMetric]:
        """Collect MySQL system metrics"""
        metrics = []
        
        if not self.connection:
            return metrics
        
        try:
            cursor = self.connection.cursor()
            timestamp = datetime.utcnow()
            
            # Global status variables
            cursor.execute("SHOW GLOBAL STATUS")
            
            status_vars = dict(cursor.fetchall())
            
            # Key metrics to track
            key_metrics = {
                'Connections': 'connections_total',
                'Threads_connected': 'connections_active',
                'Threads_running': 'threads_running',
                'Queries': 'queries_total',
                'Slow_queries': 'slow_queries_total',
                'Innodb_buffer_pool_read_requests': 'buffer_pool_read_requests',
                'Innodb_buffer_pool_reads': 'buffer_pool_reads',
                'Innodb_data_read': 'data_read_bytes',
                'Innodb_data_written': 'data_written_bytes',
                'Innodb_rows_read': 'rows_read',
                'Innodb_rows_inserted': 'rows_inserted',
                'Innodb_rows_updated': 'rows_updated',
                'Innodb_rows_deleted': 'rows_deleted'
            }
            
            for mysql_var, metric_name in key_metrics.items():
                if mysql_var in status_vars:
                    value = float(status_vars[mysql_var])
                    unit = "bytes" if "bytes" in metric_name else "count"
                    
                    metrics.append(DatabaseMetric(
                        name=metric_name,
                        value=value,
                        unit=unit,
                        timestamp=timestamp,
                        database="all",
                        instance=self.instance_name
                    ))
            
            # Calculate buffer pool hit ratio
            if all(var in status_vars for var in ['Innodb_buffer_pool_read_requests', 'Innodb_buffer_pool_reads']):
                read_requests = float(status_vars['Innodb_buffer_pool_read_requests'])
                reads = float(status_vars['Innodb_buffer_pool_reads'])
                
                if read_requests > 0:
                    hit_ratio = ((read_requests - reads) / read_requests) * 100
                    metrics.append(DatabaseMetric(
                        name="buffer_pool_hit_ratio",
                        value=hit_ratio,
                        unit="percent",
                        timestamp=timestamp,
                        database="all",
                        instance=self.instance_name
                    ))
            
            # Process list information
            cursor.execute("""
                SELECT state, COUNT(*) as count 
                FROM information_schema.processlist 
                WHERE command != 'Sleep' 
                GROUP BY state
            """)
            
            for row in cursor.fetchall():
                if row[0]:  # state is not None
                    metrics.append(DatabaseMetric(
                        name=f"processes_{row[0].lower().replace(' ', '_')}",
                        value=float(row[1]),
                        unit="count",
                        timestamp=timestamp,
                        database="all",
                        instance=self.instance_name
                    ))
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Error collecting MySQL metrics: {e}")
        
        return metrics
    
    def collect_query_metrics(self) -> List[QueryMetric]:
        """Collect MySQL query performance metrics"""
        query_metrics = []
        
        if not self.connection:
            return query_metrics
        
        try:
            cursor = self.connection.cursor()
            
            # Get query statistics from performance_schema
            cursor.execute("""
                SELECT 
                    DIGEST,
                    DIGEST_TEXT,
                    COUNT_STAR,
                    SUM_TIMER_WAIT / 1000000000 as total_time_ms,
                    AVG_TIMER_WAIT / 1000000000 as avg_time_ms,
                    MAX_TIMER_WAIT / 1000000000 as max_time_ms,
                    SUM_ROWS_EXAMINED,
                    SUM_ROWS_SENT
                FROM performance_schema.events_statements_summary_by_digest
                WHERE DIGEST_TEXT IS NOT NULL
                ORDER BY AVG_TIMER_WAIT DESC
                LIMIT 50
            """)
            
            for row in cursor.fetchall():
                normalized_query = row[1][:500] if row[1] else ""
                operation = self._extract_operation(normalized_query)
                
                query_metrics.append(QueryMetric(
                    query_id=row[0][:16] if row[0] else "",
                    query_hash=row[0] if row[0] else "",
                    normalized_query=normalized_query,
                    execution_time_ms=float(row[4]) if row[4] else 0,  # avg_time_ms
                    rows_examined=int(row[6]) if row[6] else 0,
                    rows_returned=int(row[7]) if row[7] else 0,
                    database="all",
                    table=self._extract_table_name(normalized_query),
                    operation=operation,
                    timestamp=datetime.utcnow()
                ))
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Error collecting MySQL query metrics: {e}")
        
        return query_metrics
    
    def get_slow_queries(self, limit: int = 10) -> List[QueryMetric]:
        """Get slowest MySQL queries"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT 
                    DIGEST,
                    DIGEST_TEXT,
                    COUNT_STAR,
                    AVG_TIMER_WAIT / 1000000000 as avg_time_ms,
                    MAX_TIMER_WAIT / 1000000000 as max_time_ms,
                    SUM_ROWS_EXAMINED,
                    SUM_ROWS_SENT
                FROM performance_schema.events_statements_summary_by_digest
                WHERE DIGEST_TEXT IS NOT NULL 
                    AND AVG_TIMER_WAIT / 1000000000 > 100  -- Slower than 100ms
                ORDER BY AVG_TIMER_WAIT DESC
                LIMIT %s
            """, (limit,))
            
            slow_queries = []
            for row in cursor.fetchall():
                normalized_query = row[1][:500] if row[1] else ""
                
                slow_queries.append(QueryMetric(
                    query_id=row[0][:16] if row[0] else "",
                    query_hash=row[0] if row[0] else "",
                    normalized_query=normalized_query,
                    execution_time_ms=float(row[3]) if row[3] else 0,
                    rows_examined=int(row[5]) if row[5] else 0,
                    rows_returned=int(row[6]) if row[6] else 0,
                    database="all",
                    table=self._extract_table_name(normalized_query),
                    operation=self._extract_operation(normalized_query),
                    timestamp=datetime.utcnow(),
                    tags={
                        "calls": str(row[2]) if row[2] else "0",
                        "max_time_ms": str(row[4]) if row[4] else "0"
                    }
                ))
            
            cursor.close()
            return slow_queries
            
        except Exception as e:
            self.logger.error(f"Error getting slow MySQL queries: {e}")
            return []
    
    def _extract_operation(self, query: str) -> str:
        """Extract operation type from SQL query"""
        if not query:
            return "UNKNOWN"
        
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _extract_table_name(self, query: str) -> str:
        """Extract primary table name from SQL query"""
        if not query:
            return "unknown"
        
        # Simple regex to extract table name
        from_match = re.search(r'FROM\s+`?(\w+)`?', query, re.IGNORECASE)
        if from_match:
            return from_match.group(1)
        
        into_match = re.search(r'INTO\s+`?(\w+)`?', query, re.IGNORECASE)
        if into_match:
            return into_match.group(1)
        
        update_match = re.search(r'UPDATE\s+`?(\w+)`?', query, re.IGNORECASE)
        if update_match:
            return update_match.group(1)
        
        return "unknown"

class DatabasePerformanceAnalyzer:
    """Analyze database performance across multiple instances"""
    
    def __init__(self):
        self.monitors = {}
        self.alerts = []
        self.thresholds = {
            'slow_query_threshold_ms': 1000,
            'connection_threshold': 80,  # 80% of max connections
            'cache_hit_ratio_threshold': 90,  # Below 90% is concerning
            'lock_wait_threshold': 10  # More than 10 waiting locks
        }
    
    def add_monitor(self, name: str, monitor: DatabaseMonitor):
        """Add a database monitor"""
        self.monitors[name] = monitor
    
    def collect_all_metrics(self):
        """Collect metrics from all monitors"""
        all_metrics = {}
        all_queries = {}
        
        for name, monitor in self.monitors.items():
            try:
                # Collect system metrics
                system_metrics = monitor.collect_system_metrics()
                for metric in system_metrics:
                    monitor.add_metric(metric)
                
                # Collect query metrics
                query_metrics = monitor.collect_query_metrics()
                for query_metric in query_metrics:
                    monitor.add_query_metric(query_metric)
                
                # Get summary
                all_metrics[name] = monitor.get_metrics_summary()
                all_queries[name] = monitor.get_slow_queries()
                
            except Exception as e:
                logging.error(f"Error collecting metrics from {name}: {e}")
        
        return all_metrics, all_queries
    
    def analyze_performance(self, metrics: Dict[str, Any], queries: Dict[str, List]) -> Dict[str, Any]:
        """Analyze performance and identify issues"""
        
        analysis = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_health': 'healthy',
            'issues': [],
            'recommendations': [],
            'summary': {
                'total_instances': len(metrics),
                'healthy_instances': 0,
                'instances_with_issues': 0
            }
        }
        
        for instance_name, instance_metrics in metrics.items():
            instance_issues = []
            
            # Check slow queries
            slow_queries = queries.get(instance_name, [])
            if len(slow_queries) > 0:
                avg_slow_time = statistics.mean([q.execution_time_ms for q in slow_queries])
                if avg_slow_time > self.thresholds['slow_query_threshold_ms']:
                    instance_issues.append(f"High average slow query time: {avg_slow_time:.1f}ms")
            
            # Check cache hit ratio
            cache_ratio = None
            if 'cache_hit_ratio' in instance_metrics.get('metrics', {}):
                cache_ratio = instance_metrics['metrics']['cache_hit_ratio']['current']
                if cache_ratio < self.thresholds['cache_hit_ratio_threshold']:
                    instance_issues.append(f"Low cache hit ratio: {cache_ratio:.1f}%")
            
            # Check connections
            active_connections = None
            if 'connections_active' in instance_metrics.get('metrics', {}):
                active_connections = instance_metrics['metrics']['connections_active']['current']
                # Assuming max connections is 100 for this example
                if active_connections > 80:  # 80% threshold
                    instance_issues.append(f"High connection usage: {active_connections}")
            
            # Check for lock waits
            if 'locks_waiting_total' in instance_metrics.get('metrics', {}):
                waiting_locks = instance_metrics['metrics']['locks_waiting_total']['current']
                if waiting_locks > self.thresholds['lock_wait_threshold']:
                    instance_issues.append(f"High lock contention: {waiting_locks} waiting locks")
            
            if instance_issues:
                analysis['issues'].append({
                    'instance': instance_name,
                    'issues': instance_issues
                })
                analysis['summary']['instances_with_issues'] += 1
            else:
                analysis['summary']['healthy_instances'] += 1
        
        # Generate recommendations
        if analysis['summary']['instances_with_issues'] > 0:
            analysis['overall_health'] = 'degraded'
            analysis['recommendations'] = self._generate_recommendations(analysis['issues'])
        
        return analysis
    
    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate performance recommendations based on issues"""
        recommendations = []
        
        for instance_issue in issues:
            instance_name = instance_issue['instance']
            for issue in instance_issue['issues']:
                if 'slow query' in issue.lower():
                    recommendations.append(f"{instance_name}: Optimize slow queries - consider adding indexes or query tuning")
                elif 'cache hit ratio' in issue.lower():
                    recommendations.append(f"{instance_name}: Increase buffer pool size or optimize memory configuration")
                elif 'connection usage' in issue.lower():
                    recommendations.append(f"{instance_name}: Implement connection pooling or increase max connections")
                elif 'lock contention' in issue.lower():
                    recommendations.append(f"{instance_name}: Review transaction isolation levels and optimize concurrent access patterns")
        
        return recommendations
    
    def generate_report(self, metrics: Dict[str, Any], queries: Dict[str, List]) -> str:
        """Generate a comprehensive database performance report"""
        
        analysis = self.analyze_performance(metrics, queries)
        
        report = f"""
Database Performance Report
Generated: {analysis['timestamp']}
Overall Health: {analysis['overall_health'].upper()}

Instance Summary:
- Total Instances: {analysis['summary']['total_instances']}
- Healthy: {analysis['summary']['healthy_instances']}
- With Issues: {analysis['summary']['instances_with_issues']}

"""
        
        if analysis['issues']:
            report += "ISSUES DETECTED:\n"
            report += "=" * 50 + "\n"
            for issue_group in analysis['issues']:
                report += f"\nInstance: {issue_group['instance']}\n"
                for issue in issue_group['issues']:
                    report += f"  • {issue}\n"
        
        if analysis['recommendations']:
            report += "\nRECOMMENDATIONS:\n"
            report += "=" * 50 + "\n"
            for i, recommendation in enumerate(analysis['recommendations'], 1):
                report += f"{i}. {recommendation}\n"
        
        # Add detailed metrics for each instance
        report += "\nDETAILED METRICS:\n"
        report += "=" * 50 + "\n"
        
        for instance_name, instance_metrics in metrics.items():
            report += f"\n{instance_name}:\n"
            report += f"  Query Stats:\n"
            query_stats = instance_metrics.get('query_stats', {})
            report += f"    Total Queries: {query_stats.get('total_queries', 0)}\n"
            report += f"    Avg Execution Time: {query_stats.get('avg_execution_time_ms', 0):.1f}ms\n"
            report += f"    Slow Queries: {query_stats.get('slow_queries_count', 0)}\n"
            
            # Show top metrics
            report += f"  Key Metrics:\n"
            for metric_name, metric_data in instance_metrics.get('metrics', {}).items():
                if isinstance(metric_data, dict) and 'current' in metric_data:
                    report += f"    {metric_name}: {metric_data['current']:.1f}\n"
        
        # Add slow queries summary
        report += "\nSLOW QUERIES SUMMARY:\n"
        report += "=" * 50 + "\n"
        
        for instance_name, slow_queries in queries.items():
            if slow_queries:
                report += f"\n{instance_name} - Top 5 Slowest Queries:\n"
                for i, query in enumerate(slow_queries[:5], 1):
                    report += f"  {i}. {query.execution_time_ms:.1f}ms - {query.operation} on {query.table}\n"
                    report += f"     Query: {query.normalized_query[:100]}...\n"
        
        return report

# Usage example
def demonstrate_database_monitoring():
    """Demonstrate database performance monitoring"""
    
    print("🗄️  Database Performance Monitoring Demo")
    print("=" * 50)
    
    # Initialize monitors (using mock connections for demo)
    analyzer = DatabasePerformanceAnalyzer()
    
    try:
        # Add PostgreSQL monitor
        pg_monitor = PostgreSQLMonitor(
            "postgresql://user:pass@localhost/dbname", 
            "production-pg-01"
        )
        analyzer.add_monitor("postgresql", pg_monitor)
        print("✅ PostgreSQL monitor added")
    except:
        print("⚠️  PostgreSQL monitor not available")
    
    try:
        # Add MySQL monitor
        mysql_monitor = MySQLMonitor(
            "mysql://user:pass@localhost/dbname",
            "production-mysql-01"
        )
        analyzer.add_monitor("mysql", mysql_monitor)
        print("✅ MySQL monitor added")
    except:
        print("⚠️  MySQL monitor not available")
    
    # Simulate metric collection
    print("\n📊 Collecting database metrics...")
    
    # In real implementation, this would collect actual metrics
    # For demo, we'll create mock data
    mock_metrics = {
        "postgresql": {
            "instance": "production-pg-01",
            "time_window_minutes": 5,
            "metrics": {
                "cache_hit_ratio": {"current": 89.5, "average": 90.2},
                "connections_active": {"current": 45, "average": 42},
                "locks_waiting_total": {"current": 15, "average": 8}
            },
            "query_stats": {
                "total_queries": 1250,
                "avg_execution_time_ms": 125.5,
                "slow_queries_count": 8
            }
        },
        "mysql": {
            "instance": "production-mysql-01", 
            "time_window_minutes": 5,
            "metrics": {
                "buffer_pool_hit_ratio": {"current": 94.2, "average": 93.8},
                "connections_active": {"current": 85, "average": 78},
                "threads_running": {"current": 12, "average": 10}
            },
            "query_stats": {
                "total_queries": 2100,
                "avg_execution_time_ms": 89.3,
                "slow_queries_count": 3
            }
        }
    }
    
    # Mock slow queries
    mock_queries = {
        "postgresql": [
            QueryMetric(
                query_id="12345",
                query_hash="abcdef",
                normalized_query="SELECT * FROM orders WHERE status = ? AND created_at > ?",
                execution_time_ms=1250.0,
                rows_examined=50000,
                rows_returned=1200,
                database="ecommerce",
                table="orders",
                operation="SELECT",
                timestamp=datetime.utcnow()
            )
        ],
        "mysql": [
            QueryMetric(
                query_id="67890",
                query_hash="fedcba",
                normalized_query="UPDATE users SET last_login = ? WHERE id = ?",
                execution_time_ms=850.0,
                rows_examined=1,
                rows_returned=1,
                database="users",
                table="users", 
                operation="UPDATE",
                timestamp=datetime.utcnow()
            )
        ]
    }
    
    print("📈 Analyzing performance...")
    analysis = analyzer.analyze_performance(mock_metrics, mock_queries)
    
    print(f"\nOverall Health: {analysis['overall_health'].upper()}")
    print(f"Instances with Issues: {analysis['summary']['instances_with_issues']}")
    
    if analysis['issues']:
        print("\nIssues Detected:")
        for issue_group in analysis['issues']:
            print(f"  {issue_group['instance']}:")
            for issue in issue_group['issues']:
                print(f"    • {issue}")
    
    if analysis['recommendations']:
        print(f"\nRecommendations:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Generate full report
    print(f"\n📋 Generating comprehensive report...")
    report = analyzer.generate_report(mock_metrics, mock_queries)
    
    # Save report to file
    with open('/tmp/database_performance_report.txt', 'w') as f:
        f.write(report)
    
    print(f"Report saved to /tmp/database_performance_report.txt")
    print(f"Report preview (first 500 chars):")
    print("-" * 50)
    print(report[:500] + "...")

if __name__ == "__main__":
    demonstrate_database_monitoring()
```

This comprehensive database performance monitoring system provides enterprise-grade monitoring capabilities for multiple database systems, enabling proactive identification and resolution of performance issues in production environments.