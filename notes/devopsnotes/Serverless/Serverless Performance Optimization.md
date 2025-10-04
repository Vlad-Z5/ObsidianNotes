# Serverless Performance Optimization

**Serverless Performance Optimization** encompasses advanced techniques for minimizing cold starts, optimizing memory and CPU usage, implementing efficient data access patterns, and leveraging caching strategies to achieve optimal performance and cost efficiency in serverless applications.

## Cold Start Optimization

### Cold Start Mitigation Strategies

#### Provisioned Concurrency and Warm-up Techniques
```yaml
cold_start_optimization:
  provisioned_concurrency: |
    # serverless.yml - Provisioned Concurrency Configuration
    service: high-performance-api

    provider:
      name: aws
      runtime: python3.9
      region: us-east-1
      memorySize: 1024
      timeout: 30

    functions:
      criticalApi:
        handler: src/handlers/critical_api.handler
        events:
          - http:
              path: /api/critical
              method: any
              cors: true
        provisionedConcurrency: 10  # Always keep 10 instances warm
        reservedConcurrency: 50     # Reserve 50 concurrent executions

      businessApi:
        handler: src/handlers/business_api.handler
        events:
          - http:
              path: /api/business
              method: any
              cors: true
        provisionedConcurrency: 5
        reservedConcurrency: 25

      batchProcessor:
        handler: src/handlers/batch_processor.handler
        events:
          - schedule:
              rate: rate(5 minutes)
              input:
                warmup: true
        provisionedConcurrency: 2

    # Auto-scaling configuration for provisioned concurrency
    resources:
      Resources:
        CriticalApiConcurrencyTarget:
          Type: AWS::ApplicationAutoScaling::ScalableTarget
          Properties:
            ServiceNamespace: lambda
            ResourceId: function:${self:service}-${self:provider.stage}-criticalApi:provisioned
            ScalableDimension: lambda:provisioned-concurrency:utilization
            MinCapacity: 5
            MaxCapacity: 100
            RoleArn: !GetAtt ApplicationAutoScalingLambdaRole.Arn

        CriticalApiScalingPolicy:
          Type: AWS::ApplicationAutoScaling::ScalingPolicy
          Properties:
            PolicyName: CriticalApiProvisionedConcurrencyScalingPolicy
            PolicyType: TargetTrackingScaling
            ServiceNamespace: lambda
            ResourceId: function:${self:service}-${self:provider.stage}-criticalApi:provisioned
            ScalableDimension: lambda:provisioned-concurrency:utilization
            TargetTrackingScalingPolicyConfiguration:
              TargetValue: 70.0
              ScaleInCooldown: 300
              ScaleOutCooldown: 300
              PredefinedMetricSpecification:
                PredefinedMetricType: LambdaProvisionedConcurrencyUtilization

  warmup_implementation: |
    # Intelligent Warm-up Strategy
    import json
    import boto3
    import time
    import threading
    from typing import List, Dict, Any
    from concurrent.futures import ThreadPoolExecutor, as_completed

    class ServerlessWarmupManager:
        def __init__(self, region: str = 'us-east-1'):
            self.lambda_client = boto3.client('lambda', region_name=region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)

        def warmup_functions(self, function_configs: List[Dict[str, Any]]):
            """Warm up multiple Lambda functions concurrently"""

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []

                for config in function_configs:
                    future = executor.submit(
                        self.warmup_single_function,
                        config['function_name'],
                        config.get('concurrency', 1),
                        config.get('payload', {})
                    )
                    futures.append(future)

                # Collect results
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=30)
                        results.append(result)
                    except Exception as e:
                        print(f"Warmup failed: {str(e)}")
                        results.append({'success': False, 'error': str(e)})

                return results

        def warmup_single_function(self, function_name: str, concurrency: int = 1, payload: Dict = None):
            """Warm up a single Lambda function with specified concurrency"""

            if payload is None:
                payload = {'warmup': True, 'timestamp': int(time.time())}

            warmup_payload = json.dumps(payload)

            # Execute concurrent invocations
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []

                for i in range(concurrency):
                    future = executor.submit(
                        self.invoke_function_async,
                        function_name,
                        warmup_payload
                    )
                    futures.append(future)

                # Wait for all invocations
                successful_warmups = 0
                for future in as_completed(futures):
                    try:
                        future.result(timeout=15)
                        successful_warmups += 1
                    except Exception as e:
                        print(f"Individual warmup failed: {str(e)}")

            return {
                'function_name': function_name,
                'requested_concurrency': concurrency,
                'successful_warmups': successful_warmups,
                'success': successful_warmups > 0
            }

        def invoke_function_async(self, function_name: str, payload: str):
            """Invoke Lambda function asynchronously for warmup"""

            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',  # Synchronous for warmup
                Payload=payload
            )

            if response['StatusCode'] != 200:
                raise Exception(f"Function invocation failed with status: {response['StatusCode']}")

            return response

        def schedule_intelligent_warmup(self, functions: List[str]):
            """Schedule warmup based on traffic patterns"""

            # Analyze traffic patterns from CloudWatch
            traffic_patterns = self.analyze_traffic_patterns(functions)

            # Schedule warmups before predicted traffic spikes
            warmup_schedule = []

            for function_name, pattern in traffic_patterns.items():
                peak_hours = pattern.get('peak_hours', [])
                for hour in peak_hours:
                    # Schedule warmup 10 minutes before peak
                    warmup_time = hour - 10
                    warmup_schedule.append({
                        'function_name': function_name,
                        'warmup_time': warmup_time,
                        'concurrency': pattern.get('peak_concurrency', 5)
                    })

            return warmup_schedule

        def analyze_traffic_patterns(self, functions: List[str]) -> Dict[str, Dict]:
            """Analyze traffic patterns from CloudWatch metrics"""

            patterns = {}

            for function_name in functions:
                # Get invocation metrics for the past week
                end_time = time.time()
                start_time = end_time - (7 * 24 * 3600)  # 7 days

                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[
                        {'Name': 'FunctionName', 'Value': function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Sum']
                )

                # Analyze hourly patterns
                hourly_invocations = {}
                for datapoint in response['Datapoints']:
                    hour = datapoint['Timestamp'].hour
                    if hour not in hourly_invocations:
                        hourly_invocations[hour] = []
                    hourly_invocations[hour].append(datapoint['Sum'])

                # Find peak hours (top 25% of traffic)
                avg_hourly = {hour: sum(invocations) / len(invocations)
                             for hour, invocations in hourly_invocations.items()}

                sorted_hours = sorted(avg_hourly.items(), key=lambda x: x[1], reverse=True)
                peak_hours = [hour for hour, _ in sorted_hours[:6]]  # Top 6 hours

                patterns[function_name] = {
                    'peak_hours': peak_hours,
                    'peak_concurrency': min(max(int(sorted_hours[0][1] / 100), 2), 10),
                    'avg_invocations': sum(avg_hourly.values()) / len(avg_hourly)
                }

            return patterns

    # Lambda handler for warmup scheduler
    def warmup_scheduler_handler(event, context):
        """CloudWatch Events handler for scheduled warmups"""

        warmup_manager = ServerlessWarmupManager()

        # Function configurations for warmup
        function_configs = [
            {
                'function_name': 'high-performance-api-prod-criticalApi',
                'concurrency': 8,
                'payload': {'warmup': True, 'source': 'scheduler'}
            },
            {
                'function_name': 'high-performance-api-prod-businessApi',
                'concurrency': 5,
                'payload': {'warmup': True, 'source': 'scheduler'}
            }
        ]

        results = warmup_manager.warmup_functions(function_configs)

        # Log results
        successful_warmups = sum(1 for r in results if r.get('success', False))
        print(f"Warmup completed: {successful_warmups}/{len(function_configs)} functions warmed up successfully")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'warmup_results': results,
                'summary': f'{successful_warmups}/{len(function_configs)} successful'
            })
        }

  language_optimization: |
    # Language-Specific Cold Start Optimizations

    # Python Optimization
    import sys
    import importlib
    import time

    # Import optimization - load heavy modules at module level
    import boto3
    import json
    import requests
    import pandas as pd  # Load heavy libraries once

    # Pre-initialize clients outside handler
    dynamodb = boto3.resource('dynamodb')
    s3_client = boto3.client('s3')

    # Connection pooling for external services
    session = requests.Session()
    session.mount('https://', requests.adapters.HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=3
    ))

    # Cache expensive computations
    _compiled_regex_cache = {}
    _config_cache = {}

    def optimized_handler(event, context):
        """Optimized Lambda handler with minimal cold start impact"""

        # Check if this is a warmup request
        if event.get('warmup'):
            return {'statusCode': 200, 'body': 'warmed up'}

        # Fast path for simple operations
        if event.get('operation') == 'health_check':
            return {'statusCode': 200, 'body': 'healthy'}

        # Your actual business logic here
        return process_request(event)

    # Node.js Optimization Example
    """
    // Pre-load modules and initialize connections
    const AWS = require('aws-sdk');
    const dynamodb = new AWS.DynamoDB.DocumentClient({
        maxRetries: 3,
        retryDelayOptions: {
            customBackoff: function(retryCount) {
                return Math.pow(2, retryCount) * 100;
            }
        }
    });

    // Connection pooling
    const https = require('https');
    const agent = new https.Agent({
        keepAlive: true,
        maxSockets: 50
    });

    // Pre-compile regex patterns
    const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    // Cache for expensive operations
    const cache = new Map();

    exports.handler = async (event, context) => {
        // Warmup check
        if (event.warmup) {
            return { statusCode: 200, body: 'warmed up' };
        }

        // Fast path for health checks
        if (event.operation === 'health_check') {
            return { statusCode: 200, body: 'healthy' };
        }

        // Your business logic
        return await processRequest(event);
    };
    """
```

### Memory and CPU Optimization

#### Intelligent Memory Sizing
```python
#!/usr/bin/env python3
"""
Lambda Memory and CPU Optimization Framework
"""

import json
import boto3
import time
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class PerformanceMetrics:
    duration: float
    memory_used: float
    memory_allocated: int
    cost: float
    cold_start: bool

class LambdaPerformanceOptimizer:
    def __init__(self, region: str = 'us-east-1'):
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)

    def analyze_function_performance(self, function_name: str, days: int = 7) -> Dict:
        """Analyze Lambda function performance over specified period"""

        # Get CloudWatch metrics
        metrics = self._get_cloudwatch_metrics(function_name, days)

        # Get memory utilization from CloudWatch Logs
        memory_stats = self._get_memory_utilization(function_name, days)

        # Calculate cost metrics
        cost_analysis = self._calculate_cost_metrics(function_name, metrics, memory_stats)

        # Generate optimization recommendations
        recommendations = self._generate_recommendations(metrics, memory_stats, cost_analysis)

        return {
            'function_name': function_name,
            'analysis_period_days': days,
            'performance_metrics': metrics,
            'memory_utilization': memory_stats,
            'cost_analysis': cost_analysis,
            'recommendations': recommendations
        }

    def _get_cloudwatch_metrics(self, function_name: str, days: int) -> Dict:
        """Retrieve CloudWatch metrics for Lambda function"""

        end_time = int(time.time())
        start_time = end_time - (days * 24 * 3600)

        metrics = {}

        # Duration metrics
        duration_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Duration',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum', 'Minimum']
        )

        if duration_response['Datapoints']:
            durations = [dp['Average'] for dp in duration_response['Datapoints']]
            metrics['duration'] = {
                'average': statistics.mean(durations),
                'p95': statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
                'p99': statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
                'maximum': max(durations),
                'minimum': min(durations)
            }

        # Invocation count
        invocation_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )

        total_invocations = sum(dp['Sum'] for dp in invocation_response['Datapoints'])
        metrics['invocations'] = {
            'total': total_invocations,
            'average_per_hour': total_invocations / (days * 24) if days > 0 else 0
        }

        # Error rate
        error_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )

        total_errors = sum(dp['Sum'] for dp in error_response['Datapoints'])
        metrics['error_rate'] = (total_errors / total_invocations * 100) if total_invocations > 0 else 0

        return metrics

    def _get_memory_utilization(self, function_name: str, days: int) -> Dict:
        """Extract memory utilization from CloudWatch Logs"""

        log_group_name = f'/aws/lambda/{function_name}'

        # Query for REPORT log entries
        query = """
        fields @timestamp, @message
        | filter @message like /REPORT/
        | parse @message "Max Memory Used: * MB"
        | stats avg(Max_Memory_Used), min(Max_Memory_Used), max(Max_Memory_Used), count() by bin(1h)
        """

        start_time = int((time.time() - (days * 24 * 3600)) * 1000)
        end_time = int(time.time() * 1000)

        try:
            query_response = self.logs_client.start_query(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                queryString=query
            )

            query_id = query_response['queryId']

            # Wait for query to complete
            while True:
                result = self.logs_client.get_query_results(queryId=query_id)
                if result['status'] == 'Complete':
                    break
                time.sleep(1)

            # Process results
            memory_usage = []
            for result_row in result['results']:
                if len(result_row) > 0 and result_row[0]['value'] != 'avg(Max_Memory_Used)':
                    memory_usage.append(float(result_row[0]['value']))

            if memory_usage:
                return {
                    'average_memory_used': statistics.mean(memory_usage),
                    'p95_memory_used': statistics.quantiles(memory_usage, n=20)[18] if len(memory_usage) > 1 else memory_usage[0],
                    'max_memory_used': max(memory_usage),
                    'min_memory_used': min(memory_usage),
                    'samples': len(memory_usage)
                }

        except Exception as e:
            print(f"Error querying memory utilization: {str(e)}")

        return {'error': 'Unable to retrieve memory utilization data'}

    def _calculate_cost_metrics(self, function_name: str, metrics: Dict, memory_stats: Dict) -> Dict:
        """Calculate cost metrics and optimization potential"""

        # Get current function configuration
        try:
            config = self.lambda_client.get_function_configuration(FunctionName=function_name)
            current_memory = config['MemorySize']
            timeout = config['Timeout']
        except Exception:
            return {'error': 'Unable to retrieve function configuration'}

        total_invocations = metrics.get('invocations', {}).get('total', 0)
        avg_duration = metrics.get('duration', {}).get('average', 0)

        if total_invocations == 0 or avg_duration == 0:
            return {'error': 'Insufficient metrics data'}

        # Calculate current cost (simplified pricing model)
        gb_seconds = (current_memory / 1024) * (avg_duration / 1000) * total_invocations
        current_cost = gb_seconds * 0.0000166667  # Approximate Lambda pricing

        # Calculate optimal memory configuration
        avg_memory_used = memory_stats.get('average_memory_used', current_memory * 0.7)

        # Recommend memory size (add 20% buffer)
        recommended_memory = max(128, int((avg_memory_used * 1.2) // 64) * 64)

        # Calculate potential savings
        if recommended_memory < current_memory:
            optimized_gb_seconds = (recommended_memory / 1024) * (avg_duration / 1000) * total_invocations
            optimized_cost = optimized_gb_seconds * 0.0000166667
            potential_savings = current_cost - optimized_cost
            savings_percentage = (potential_savings / current_cost) * 100
        else:
            potential_savings = 0
            savings_percentage = 0

        return {
            'current_memory_mb': current_memory,
            'recommended_memory_mb': recommended_memory,
            'current_monthly_cost': current_cost * 30,  # Extrapolate to monthly
            'optimized_monthly_cost': (current_cost - potential_savings) * 30,
            'potential_monthly_savings': potential_savings * 30,
            'savings_percentage': savings_percentage,
            'memory_utilization_percentage': (avg_memory_used / current_memory) * 100
        }

    def _generate_recommendations(self, metrics: Dict, memory_stats: Dict, cost_analysis: Dict) -> List[Dict]:
        """Generate optimization recommendations"""

        recommendations = []

        # Memory optimization
        if cost_analysis.get('savings_percentage', 0) > 10:
            recommendations.append({
                'type': 'memory_optimization',
                'priority': 'high',
                'description': f"Reduce memory from {cost_analysis['current_memory_mb']}MB to {cost_analysis['recommended_memory_mb']}MB",
                'expected_savings': f"{cost_analysis['savings_percentage']:.1f}% cost reduction",
                'implementation': 'Update function memory configuration'
            })

        # Performance optimization
        avg_duration = metrics.get('duration', {}).get('average', 0)
        if avg_duration > 5000:  # 5 seconds
            recommendations.append({
                'type': 'performance_optimization',
                'priority': 'medium',
                'description': 'Function duration is high, consider optimization',
                'suggestions': [
                    'Implement connection pooling',
                    'Optimize database queries',
                    'Use caching for frequently accessed data',
                    'Consider increasing memory for CPU-intensive tasks'
                ]
            })

        # Error rate optimization
        error_rate = metrics.get('error_rate', 0)
        if error_rate > 1:  # 1% error rate
            recommendations.append({
                'type': 'reliability_optimization',
                'priority': 'high',
                'description': f'High error rate detected: {error_rate:.2f}%',
                'suggestions': [
                    'Implement proper error handling',
                    'Add retry logic for transient failures',
                    'Increase function timeout if needed',
                    'Monitor dependency health'
                ]
            })

        # Concurrency optimization
        invocations_per_hour = metrics.get('invocations', {}).get('average_per_hour', 0)
        if invocations_per_hour > 100:
            recommendations.append({
                'type': 'concurrency_optimization',
                'priority': 'medium',
                'description': 'High invocation rate detected',
                'suggestions': [
                    'Consider provisioned concurrency for consistent performance',
                    'Implement request batching where possible',
                    'Use SQS for asynchronous processing',
                    'Monitor for throttling'
                ]
            })

        return recommendations

    def optimize_multiple_functions(self, function_names: List[str]) -> Dict:
        """Optimize multiple functions concurrently"""

        results = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.analyze_function_performance, func_name): func_name
                for func_name in function_names
            }

            for future in futures:
                func_name = futures[future]
                try:
                    results[func_name] = future.result(timeout=300)
                except Exception as e:
                    results[func_name] = {'error': str(e)}

        # Generate summary report
        total_potential_savings = sum(
            result.get('cost_analysis', {}).get('potential_monthly_savings', 0)
            for result in results.values()
            if 'error' not in result
        )

        return {
            'optimization_results': results,
            'summary': {
                'functions_analyzed': len(function_names),
                'successful_analyses': len([r for r in results.values() if 'error' not in r]),
                'total_potential_monthly_savings': total_potential_savings
            }
        }

# Usage example
def lambda_optimizer_handler(event, context):
    """Lambda function to run performance optimization analysis"""

    optimizer = LambdaPerformanceOptimizer()

    # Get function names from event or analyze all functions
    function_names = event.get('function_names', [])

    if not function_names:
        # List all functions in account (if not specified)
        paginator = optimizer.lambda_client.get_paginator('list_functions')
        function_names = []
        for page in paginator.paginate():
            function_names.extend([func['FunctionName'] for func in page['Functions']])

    # Run optimization analysis
    optimization_results = optimizer.optimize_multiple_functions(function_names[:10])  # Limit to 10 for demo

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(optimization_results, default=str)
    }
```

## Data Access Optimization

### Database Connection Optimization

#### Connection Pooling and RDS Proxy
```yaml
database_optimization:
  rds_proxy_configuration: |
    # RDS Proxy for Lambda Connection Pooling
    Resources:
      RDSProxy:
        Type: AWS::RDS::DBProxy
        Properties:
          DBProxyName: serverless-app-proxy
          EngineFamily: MYSQL
          Auth:
            - AuthScheme: SECRETS
              SecretArn: !Ref DatabaseSecret
              IAMAuth: DISABLED
          RoleArn: !GetAtt RDSProxyRole.Arn
          VpcSubnetIds:
            - !Ref PrivateSubnet1
            - !Ref PrivateSubnet2
          VpcSecurityGroupIds:
            - !Ref RDSProxySecurityGroup
          RequireTLS: true
          IdleClientTimeout: 1800
          MaxConnectionsPercent: 100
          MaxIdleConnectionsPercent: 50
          TargetGroupName: default
          DBInstanceIdentifiers:
            - !Ref DatabaseInstance

      RDSProxyTargetGroup:
        Type: AWS::RDS::DBProxyTargetGroup
        Properties:
          DBProxyName: !Ref RDSProxy
          TargetGroupName: default
          DBInstanceIdentifiers:
            - !Ref DatabaseInstance
          ConnectionPoolConfigurationInfo:
            MaxConnectionsPercent: 100
            MaxIdleConnectionsPercent: 50
            SessionPinningFilters:
              - EXCLUDE_VARIABLE_SETS

      RDSProxySecurityGroup:
        Type: AWS::EC2::SecurityGroup
        Properties:
          GroupDescription: Security group for RDS Proxy
          VpcId: !Ref VPC
          SecurityGroupIngress:
            - IpProtocol: tcp
              FromPort: 3306
              ToPort: 3306
              SourceSecurityGroupId: !Ref LambdaSecurityGroup

  connection_pooling_implementation: |
    # Optimized Database Connection Management
    import pymysql
    import boto3
    import os
    import json
    from typing import Optional, Dict, Any
    import threading
    import time

    class OptimizedDatabaseConnection:
        _instance = None
        _lock = threading.Lock()
        _connection = None
        _last_activity = 0
        _connection_timeout = 300  # 5 minutes

        def __new__(cls):
            if cls._instance is None:
                with cls._lock:
                    if cls._instance is None:
                        cls._instance = super().__new__(cls)
            return cls._instance

        def __init__(self):
            if not hasattr(self, 'initialized'):
                self.initialized = True
                self.rds_client = boto3.client('rds')
                self.secrets_client = boto3.client('secretsmanager')

        def get_connection(self):
            """Get database connection with automatic reconnection"""
            current_time = time.time()

            # Check if connection exists and is still valid
            if (self._connection is None or
                current_time - self._last_activity > self._connection_timeout):
                self._create_connection()

            self._last_activity = current_time
            return self._connection

        def _create_connection(self):
            """Create new database connection through RDS Proxy"""
            try:
                # Get database credentials from Secrets Manager
                secret_response = self.secrets_client.get_secret_value(
                    SecretId=os.environ['DB_SECRET_ARN']
                )
                credentials = json.loads(secret_response['SecretString'])

                # Connect through RDS Proxy
                self._connection = pymysql.connect(
                    host=os.environ['RDS_PROXY_ENDPOINT'],
                    port=int(os.environ.get('DB_PORT', 3306)),
                    user=credentials['username'],
                    password=credentials['password'],
                    database=credentials['dbname'],
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True,
                    connect_timeout=10,
                    read_timeout=30,
                    write_timeout=30,
                    # Connection pooling settings
                    max_allowed_packet=16777216,
                    sql_mode="STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"
                )

                print("Database connection established through RDS Proxy")

            except Exception as e:
                print(f"Failed to create database connection: {str(e)}")
                self._connection = None
                raise

        def execute_query(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
            """Execute query with automatic retry and connection management"""
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                try:
                    connection = self.get_connection()
                    with connection.cursor() as cursor:
                        cursor.execute(query, params)

                        if query.strip().upper().startswith('SELECT'):
                            return cursor.fetchall()
                        else:
                            return {'affected_rows': cursor.rowcount}

                except (pymysql.Error, AttributeError) as e:
                    retry_count += 1
                    print(f"Database query failed (attempt {retry_count}): {str(e)}")

                    if retry_count < max_retries:
                        # Force connection recreation on retry
                        self._connection = None
                        time.sleep(0.1 * retry_count)  # Exponential backoff
                    else:
                        raise

            return None

    # Singleton instance
    db_connection = OptimizedDatabaseConnection()

    def optimized_lambda_handler(event, context):
        """Lambda handler with optimized database access"""
        try:
            # Example database operations
            user_id = event.get('user_id')

            if not user_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'user_id is required'})
                }

            # Efficient query with proper indexing
            user_data = db_connection.execute_query(
                "SELECT user_id, email, name, created_at FROM users WHERE user_id = %s",
                (user_id,)
            )

            if not user_data:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'User not found'})
                }

            # Get user orders with optimized query
            orders = db_connection.execute_query("""
                SELECT o.order_id, o.total_amount, o.status, o.created_at,
                       COUNT(oi.item_id) as item_count
                FROM orders o
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                WHERE o.user_id = %s AND o.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
                GROUP BY o.order_id
                ORDER BY o.created_at DESC
                LIMIT 10
            """, (user_id,))

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'user': user_data[0],
                    'recent_orders': orders
                })
            }

        except Exception as e:
            print(f"Error in lambda handler: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }

  query_optimization: |
    # Database Query Optimization Patterns
    class QueryOptimizer:
        def __init__(self, db_connection):
            self.db = db_connection

        def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
            """Optimized dashboard query with single database roundtrip"""

            # Single optimized query instead of multiple queries
            dashboard_query = """
            SELECT
                u.user_id,
                u.email,
                u.name,
                u.created_at as user_created_at,

                -- Order statistics (subquery)
                (SELECT COUNT(*) FROM orders WHERE user_id = u.user_id) as total_orders,
                (SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE user_id = u.user_id) as total_spent,
                (SELECT MAX(created_at) FROM orders WHERE user_id = u.user_id) as last_order_date,

                -- Recent order details
                (
                    SELECT JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'order_id', order_id,
                            'total_amount', total_amount,
                            'status', status,
                            'created_at', created_at
                        )
                    )
                    FROM (
                        SELECT order_id, total_amount, status, created_at
                        FROM orders
                        WHERE user_id = u.user_id
                        ORDER BY created_at DESC
                        LIMIT 5
                    ) recent_orders
                ) as recent_orders_json

            FROM users u
            WHERE u.user_id = %s
            """

            result = self.db.execute_query(dashboard_query, (user_id,))

            if not result:
                return None

            data = result[0]

            # Parse JSON fields
            if data['recent_orders_json']:
                data['recent_orders'] = json.loads(data['recent_orders_json'])
            else:
                data['recent_orders'] = []

            del data['recent_orders_json']  # Remove raw JSON field

            return data

        def get_analytics_data(self, date_range: tuple) -> Dict[str, Any]:
            """Optimized analytics query with proper aggregations"""

            analytics_query = """
            SELECT
                DATE(created_at) as date,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_orders,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_order_value,

                -- Status breakdown
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders,

                -- Revenue by status
                SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END) as completed_revenue

            FROM orders
            WHERE created_at BETWEEN %s AND %s
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """

            return self.db.execute_query(analytics_query, date_range)

        def search_products_optimized(self, search_term: str, category: str = None, limit: int = 20) -> List[Dict]:
            """Optimized product search with full-text search and proper indexing"""

            # Use full-text search for better performance
            if category:
                search_query = """
                SELECT p.product_id, p.name, p.description, p.price, p.category,
                       p.image_url, p.rating, p.review_count,
                       MATCH(p.name, p.description) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance_score
                FROM products p
                WHERE MATCH(p.name, p.description) AGAINST(%s IN NATURAL LANGUAGE MODE)
                  AND p.category = %s
                  AND p.active = 1
                ORDER BY relevance_score DESC, p.rating DESC
                LIMIT %s
                """
                params = (search_term, search_term, category, limit)
            else:
                search_query = """
                SELECT p.product_id, p.name, p.description, p.price, p.category,
                       p.image_url, p.rating, p.review_count,
                       MATCH(p.name, p.description) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance_score
                FROM products p
                WHERE MATCH(p.name, p.description) AGAINST(%s IN NATURAL LANGUAGE MODE)
                  AND p.active = 1
                ORDER BY relevance_score DESC, p.rating DESC
                LIMIT %s
                """
                params = (search_term, search_term, limit)

            return self.db.execute_query(search_query, params)
```

This comprehensive Serverless Performance Optimization document provides advanced techniques for cold start mitigation, memory and CPU optimization, intelligent performance analysis, and database access optimization essential for building high-performance serverless applications.