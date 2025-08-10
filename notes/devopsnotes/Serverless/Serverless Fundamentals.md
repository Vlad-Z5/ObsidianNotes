## Production Serverless Implementation

### AWS Lambda Production Patterns

#### Function Configuration and Deployment
```yaml
# serverless/aws-lambda/serverless.yml
service: production-api

provider:
  name: aws
  runtime: python3.9
  region: us-east-1
  stage: ${opt:stage, 'prod'}
  memorySize: 1024
  timeout: 30
  
  # Enhanced monitoring and observability
  tracing:
    lambda: true
    apiGateway: true
  
  logs:
    restApi:
      accessLogging: true
      executionLogging: true
      level: INFO
      fullExecutionData: true
  
  # IAM permissions
  iamRoleStatements:
    - Effect: Allow
      Action:
        - logs:CreateLogGroup
        - logs:CreateLogStream
        - logs:PutLogEvents
      Resource: "arn:aws:logs:*:*:*"
    - Effect: Allow
      Action:
        - xray:PutTraceSegments
        - xray:PutTelemetryRecords
      Resource: "*"
    - Effect: Allow
      Action:
        - secretsmanager:GetSecretValue
      Resource: "arn:aws:secretsmanager:${self:provider.region}:*:secret:${self:service}-${self:provider.stage}/*"
  
  # Environment variables
  environment:
    STAGE: ${self:provider.stage}
    LOG_LEVEL: ${env:LOG_LEVEL, 'INFO'}
    DATABASE_SECRET_ARN: ${ssm:/prod/database/secret-arn}
    REDIS_ENDPOINT: ${ssm:/prod/redis/endpoint}
    
  # VPC configuration for database access
  vpc:
    securityGroupIds:
      - ${ssm:/prod/security-groups/lambda}
    subnetIds:
      - ${ssm:/prod/subnets/private-a}
      - ${ssm:/prod/subnets/private-b}

# Lambda functions
functions:
  api:
    handler: handlers/api.handler
    reservedConcurrency: 50  # Limit concurrent executions
    provisionedConcurrency: 5  # Pre-warm instances
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors:
            origin: '*'
            headers:
              - Content-Type
              - X-Amz-Date
              - Authorization
              - X-Api-Key
              - X-Request-ID
    destinations:
      onFailure:
        type: sqs
        arn: ${ssm:/prod/dlq/arn}
    deadLetterQueue:
      targetArn: ${ssm:/prod/dlq/arn}
    
  background-processor:
    handler: handlers/background.handler
    timeout: 300  # 5 minutes for longer processing
    memorySize: 2048
    events:
      - sqs:
          arn: ${ssm:/prod/processing-queue/arn}
          batchSize: 10
          maximumBatchingWindowInSeconds: 20
    reservedConcurrency: 10
    
  scheduled-tasks:
    handler: handlers/scheduler.handler
    events:
      - schedule:
          rate: rate(5 minutes)
          name: health-check
          description: 'Periodic health check'
          input:
            task_type: health_check
      - schedule:
          rate: cron(0 2 * * ? *)  # Daily at 2 AM
          name: daily-cleanup
          description: 'Daily cleanup tasks'
          input:
            task_type: cleanup

# Resources
resources:
  Resources:
    # DynamoDB table with proper configuration
    ApiTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:service}-${self:provider.stage}-api-data
        BillingMode: PAY_PER_REQUEST
        AttributeDefinitions:
          - AttributeName: id
            AttributeType: S
          - AttributeName: gsi1pk
            AttributeType: S
          - AttributeName: gsi1sk
            AttributeType: S
        KeySchema:
          - AttributeName: id
            KeyType: HASH
        GlobalSecondaryIndexes:
          - IndexName: GSI1
            KeySchema:
              - AttributeName: gsi1pk
                KeyType: HASH
              - AttributeName: gsi1sk
                KeyType: RANGE
            Projection:
              ProjectionType: ALL
        PointInTimeRecoverySpecification:
          PointInTimeRecoveryEnabled: true
        SSESpecification:
          SSEEnabled: true
        StreamSpecification:
          StreamViewType: NEW_AND_OLD_IMAGES
        Tags:
          - Key: Environment
            Value: ${self:provider.stage}
          - Key: Service
            Value: ${self:service}

# Plugins for enhanced functionality
plugins:
  - serverless-python-requirements
  - serverless-plugin-tracing
  - serverless-prune-plugin
  - serverless-domain-manager
  - serverless-associate-waf

# Custom configuration
custom:
  pythonRequirements:
    dockerizePip: true
    slim: true
    strip: false
    
  prune:
    automatic: true
    number: 5  # Keep 5 versions
    
  customDomain:
    domainName: api.company.com
    stage: ${self:provider.stage}
    certificateName: '*.company.com'
    createRoute53Record: true
    endpointType: 'regional'
    
  associateWaf:
    name: ${self:service}-${self:provider.stage}-waf
    version: V2
```

### Production Lambda Handler Implementation

```python
# handlers/api.py - Production Lambda API handler
import json
import logging
import os
import time
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
import asyncio
import aiohttp

# Initialize AWS Lambda Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# AWS clients with proper configuration
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')
ssm = boto3.client('ssm')

# Configuration
TABLE_NAME = os.environ['TABLE_NAME']
DATABASE_SECRET_ARN = os.environ.get('DATABASE_SECRET_ARN')
REDIS_ENDPOINT = os.environ.get('REDIS_ENDPOINT')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Set logging level
logger.setLevel(LOG_LEVEL)

class ProductionError(Exception):
    """Base exception for production errors"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class DatabaseConnectionPool:
    """Connection pool manager for database connections"""
    
    def __init__(self):
        self._connection = None
        self._credentials = None
        self._credentials_expiry = None
    
    async def get_connection(self):
        """Get database connection with credential rotation support"""
        if self._credentials_expiry and datetime.utcnow() < self._credentials_expiry:
            # Credentials still valid
            return self._connection
        
        try:
            # Refresh credentials from Secrets Manager
            response = secrets_manager.get_secret_value(SecretId=DATABASE_SECRET_ARN)
            self._credentials = json.loads(response['SecretString'])
            
            # Connection logic here (placeholder)
            # In practice, implement your database connection logic
            logger.info("Database credentials refreshed")
            
        except Exception as e:
            logger.error(f"Failed to refresh database credentials: {str(e)}")
            raise ProductionError("Database connection failed", 503, "DB_CONNECTION_ERROR")
        
        return self._connection

# Global connection pool
db_pool = DatabaseConnectionPool()

@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context) -> dict:
    """Main Lambda handler with comprehensive error handling and monitoring"""
    
    start_time = time.time()
    
    try:
        # Parse the event
        api_event = APIGatewayProxyEvent(event)
        
        # Log incoming request
        logger.info("Processing request", extra={
            "path": api_event.path,
            "method": api_event.http_method,
            "user_agent": api_event.headers.get("User-Agent"),
            "request_id": api_event.request_context.request_id
        })
        
        # Route the request
        response = route_request(api_event, context)
        
        # Add metrics
        metrics.add_metric(name="RequestSuccess", unit=MetricUnit.Count, value=1)
        processing_time = time.time() - start_time
        metrics.add_metric(name="ProcessingTime", unit=MetricUnit.Seconds, value=processing_time)
        
        logger.info("Request completed successfully", extra={
            "processing_time": processing_time,
            "status_code": response["statusCode"]
        })
        
        return response
        
    except ProductionError as e:
        # Handle known production errors
        metrics.add_metric(name="RequestError", unit=MetricUnit.Count, value=1)
        metrics.add_metadata(key="error_code", value=e.error_code)
        
        logger.error("Production error occurred", extra={
            "error_code": e.error_code,
            "error_message": e.message,
            "status_code": e.status_code
        })
        
        return {
            "statusCode": e.status_code,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "request_id": context.aws_request_id
                }
            })
        }
        
    except Exception as e:
        # Handle unexpected errors
        metrics.add_metric(name="RequestError", unit=MetricUnit.Count, value=1)
        metrics.add_metadata(key="error_type", value="UNEXPECTED_ERROR")
        
        logger.error("Unexpected error occurred", extra={
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": context.aws_request_id
                }
            })
        }

@tracer.capture_method
def route_request(event: APIGatewayProxyEvent, context) -> dict:
    """Route requests to appropriate handlers"""
    
    method = event.http_method
    path = event.path
    
    # Health check endpoint
    if path == "/health":
        return handle_health_check(event, context)
    
    # API routes
    if path.startswith("/api/v1/"):
        if method == "GET" and path == "/api/v1/items":
            return handle_get_items(event, context)
        elif method == "POST" and path == "/api/v1/items":
            return handle_create_item(event, context)
        elif method == "GET" and path.startswith("/api/v1/items/"):
            item_id = path.split("/")[-1]
            return handle_get_item(event, context, item_id)
        elif method == "PUT" and path.startswith("/api/v1/items/"):
            item_id = path.split("/")[-1]
            return handle_update_item(event, context, item_id)
        elif method == "DELETE" and path.startswith("/api/v1/items/"):
            item_id = path.split("/")[-1]
            return handle_delete_item(event, context, item_id)
    
    # Return 404 for unknown routes
    raise ProductionError("Not Found", 404, "ROUTE_NOT_FOUND")

@tracer.capture_method
def handle_health_check(event: APIGatewayProxyEvent, context) -> dict:
    """Health check endpoint with comprehensive checks"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.environ.get("VERSION", "unknown"),
        "checks": {}
    }
    
    # Check DynamoDB
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.meta.client.describe_table(TableName=TABLE_NAME)
        health_status["checks"]["dynamodb"] = "healthy"
    except Exception as e:
        health_status["checks"]["dynamodb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check external dependencies
    try:
        # Placeholder for external service checks
        health_status["checks"]["external_api"] = "healthy"
    except Exception as e:
        health_status["checks"]["external_api"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return {
        "statusCode": status_code,
        "headers": get_cors_headers(),
        "body": json.dumps(health_status)
    }

@tracer.capture_method
def handle_get_items(event: APIGatewayProxyEvent, context) -> dict:
    """Get items with pagination and filtering"""
    
    # Parse query parameters
    query_params = event.query_string_parameters or {}
    limit = min(int(query_params.get("limit", 20)), 100)  # Max 100 items
    last_key = query_params.get("last_key")
    filter_status = query_params.get("status")
    
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Build scan/query parameters
        scan_params = {"Limit": limit}
        
        if last_key:
            scan_params["ExclusiveStartKey"] = {"id": last_key}
        
        if filter_status:
            scan_params["FilterExpression"] = "attribute_exists(#status) AND #status = :status"
            scan_params["ExpressionAttributeNames"] = {"#status": "status"}
            scan_params["ExpressionAttributeValues"] = {":status": filter_status}
        
        # Execute scan
        response = table.scan(**scan_params)
        
        # Format response
        result = {
            "items": response.get("Items", []),
            "count": len(response.get("Items", [])),
            "last_key": response.get("LastEvaluatedKey", {}).get("id") if response.get("LastEvaluatedKey") else None
        }
        
        metrics.add_metric(name="ItemsRetrieved", unit=MetricUnit.Count, value=len(result["items"]))
        
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(result, default=str)
        }
        
    except Exception as e:
        logger.error(f"Failed to get items: {str(e)}")
        raise ProductionError("Failed to retrieve items", 500, "DB_READ_ERROR")

@tracer.capture_method
def handle_create_item(event: APIGatewayProxyEvent, context) -> dict:
    """Create new item with validation"""
    
    try:
        # Parse and validate request body
        if not event.body:
            raise ProductionError("Request body is required", 400, "MISSING_BODY")
        
        try:
            data = json.loads(event.body)
        except json.JSONDecodeError:
            raise ProductionError("Invalid JSON in request body", 400, "INVALID_JSON")
        
        # Validate required fields
        required_fields = ["name", "type"]
        for field in required_fields:
            if field not in data:
                raise ProductionError(f"Missing required field: {field}", 400, "MISSING_FIELD")
        
        # Generate item
        item_id = generate_id()
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            "id": item_id,
            "name": data["name"],
            "type": data["type"],
            "description": data.get("description", ""),
            "status": "active",
            "created_at": timestamp,
            "updated_at": timestamp,
            "gsi1pk": f"TYPE#{data['type']}",
            "gsi1sk": timestamp
        }
        
        # Save to DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=item)
        
        metrics.add_metric(name="ItemCreated", unit=MetricUnit.Count, value=1)
        
        return {
            "statusCode": 201,
            "headers": get_cors_headers(),
            "body": json.dumps({"item": item}, default=str)
        }
        
    except ProductionError:
        raise
    except Exception as e:
        logger.error(f"Failed to create item: {str(e)}")
        raise ProductionError("Failed to create item", 500, "DB_WRITE_ERROR")

def get_cors_headers() -> dict:
    """Get CORS headers for API responses"""
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Request-ID",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }

def generate_id() -> str:
    """Generate unique ID for items"""
    import uuid
    return str(uuid.uuid4())

# Additional handlers would be implemented here...
# handle_get_item, handle_update_item, handle_delete_item, etc.
```

### Serverless Monitoring and Observability

```bash
#!/bin/bash
# scripts/serverless-monitoring.sh - Production serverless monitoring

set -euo pipefail

readonly SERVICE_NAME="production-api"
readonly STAGE="prod"
readonly REGION="us-east-1"

log_info() { echo -e "[$(date '+%H:%M:%S')] INFO: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] SUCCESS: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] WARN: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ERROR: $*"; }

# Monitor Lambda function metrics
monitor_lambda_metrics() {
    local function_name="$1"
    local duration="${2:-300}"  # 5 minutes default
    
    log_info "Monitoring Lambda function metrics: $function_name for ${duration}s"
    
    local end_time=$(($(date +%s) + duration))
    local check_interval=30
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local start_time_iso=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)
        local end_time_iso=$(date -u +%Y-%m-%dT%H:%M:%S)
        
        # Get invocation count
        local invocations
        invocations=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/Lambda" \
            --metric-name "Invocations" \
            --dimensions Name=FunctionName,Value="$function_name" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        # Get error count
        local errors
        errors=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/Lambda" \
            --metric-name "Errors" \
            --dimensions Name=FunctionName,Value="$function_name" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        # Get duration
        local avg_duration
        avg_duration=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/Lambda" \
            --metric-name "Duration" \
            --dimensions Name=FunctionName,Value="$function_name" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Average \
            --query 'Datapoints[0].Average' \
            --output text 2>/dev/null || echo "0")
        
        # Get throttles
        local throttles
        throttles=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/Lambda" \
            --metric-name "Throttles" \
            --dimensions Name=FunctionName,Value="$function_name" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        # Calculate error rate
        local error_rate=0
        if [[ "$invocations" != "0" ]] && [[ "$invocations" != "None" ]]; then
            error_rate=$(echo "scale=2; $errors * 100 / $invocations" | bc 2>/dev/null || echo "0")
        fi
        
        log_info "Metrics: Invocations=$invocations, Errors=$errors ($error_rate%), AvgDuration=${avg_duration}ms, Throttles=$throttles"
        
        # Alert on high error rate
        if (( $(echo "$error_rate > 5.0" | bc -l) )); then
            log_warn "High error rate detected: $error_rate%"
            send_lambda_alert "$function_name" "HIGH_ERROR_RATE" "$error_rate"
        fi
        
        # Alert on throttling
        if [[ "$throttles" != "0" ]] && [[ "$throttles" != "None" ]]; then
            log_warn "Lambda throttling detected: $throttles throttles"
            send_lambda_alert "$function_name" "THROTTLING" "$throttles"
        fi
        
        sleep $check_interval
    done
}

# Monitor API Gateway metrics
monitor_api_gateway_metrics() {
    local api_name="$1"
    local stage="$2"
    local duration="${3:-300}"
    
    log_info "Monitoring API Gateway metrics: $api_name ($stage) for ${duration}s"
    
    local end_time=$(($(date +%s) + duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local start_time_iso=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)
        local end_time_iso=$(date -u +%Y-%m-%dT%H:%M:%S)
        
        # Get request count
        local requests
        requests=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/ApiGateway" \
            --metric-name "Count" \
            --dimensions Name=ApiName,Value="$api_name" Name=Stage,Value="$stage" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        # Get 4xx errors
        local errors_4xx
        errors_4xx=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/ApiGateway" \
            --metric-name "4XXError" \
            --dimensions Name=ApiName,Value="$api_name" Name=Stage,Value="$stage" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        # Get 5xx errors
        local errors_5xx
        errors_5xx=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/ApiGateway" \
            --metric-name "5XXError" \
            --dimensions Name=ApiName,Value="$api_name" Name=Stage,Value="$stage" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        # Get latency
        local latency
        latency=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/ApiGateway" \
            --metric-name "Latency" \
            --dimensions Name=ApiName,Value="$api_name" Name=Stage,Value="$stage" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Average \
            --query 'Datapoints[0].Average' \
            --output text 2>/dev/null || echo "0")
        
        log_info "API Metrics: Requests=$requests, 4xx=$errors_4xx, 5xx=$errors_5xx, AvgLatency=${latency}ms"
        
        # Alert on high 5xx error rate
        local error_5xx_rate=0
        if [[ "$requests" != "0" ]] && [[ "$requests" != "None" ]]; then
            error_5xx_rate=$(echo "scale=2; $errors_5xx * 100 / $requests" | bc 2>/dev/null || echo "0")
        fi
        
        if (( $(echo "$error_5xx_rate > 1.0" | bc -l) )); then
            log_warn "High 5xx error rate: $error_5xx_rate%"
            send_api_alert "$api_name" "HIGH_5XX_ERROR_RATE" "$error_5xx_rate"
        fi
        
        sleep 30
    done
}

# Check Lambda function health
check_lambda_health() {
    local function_name="$1"
    
    log_info "Checking Lambda function health: $function_name"
    
    # Test function with health check payload
    local test_payload='{"httpMethod":"GET","path":"/health","headers":{}}'
    
    local response
    response=$(aws lambda invoke \
        --function-name "$function_name" \
        --payload "$test_payload" \
        /tmp/lambda-response.json 2>&1)
    
    if echo "$response" | grep -q "StatusCode.*200"; then
        local response_body
        response_body=$(cat /tmp/lambda-response.json 2>/dev/null || echo "{}")
        
        # Check if response indicates healthy status
        if echo "$response_body" | jq -e '.body' >/dev/null 2>&1; then
            local body
            body=$(echo "$response_body" | jq -r '.body' | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
            
            if [[ "$body" == "healthy" ]]; then
                log_success "Lambda health check passed"
                return 0
            else
                log_warn "Lambda health check returned status: $body"
                return 1
            fi
        else
            log_warn "Lambda health check response format unexpected"
            return 1
        fi
    else
        log_error "Lambda health check failed: $response"
        return 1
    fi
}

# Monitor DynamoDB metrics
monitor_dynamodb_metrics() {
    local table_name="$1"
    local duration="${2:-300}"
    
    log_info "Monitoring DynamoDB metrics: $table_name for ${duration}s"
    
    local end_time=$(($(date +%s) + duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local start_time_iso=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)
        local end_time_iso=$(date -u +%Y-%m-%dT%H:%M:%S)
        
        # Get consumed read/write capacity
        local read_capacity
        read_capacity=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/DynamoDB" \
            --metric-name "ConsumedReadCapacityUnits" \
            --dimensions Name=TableName,Value="$table_name" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Average \
            --query 'Datapoints[0].Average' \
            --output text 2>/dev/null || echo "0")
        
        local write_capacity
        write_capacity=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/DynamoDB" \
            --metric-name "ConsumedWriteCapacityUnits" \
            --dimensions Name=TableName,Value="$table_name" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Average \
            --query 'Datapoints[0].Average' \
            --output text 2>/dev/null || echo "0")
        
        # Get throttled requests
        local throttled_reads
        throttled_reads=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/DynamoDB" \
            --metric-name "ReadThrottledEvents" \
            --dimensions Name=TableName,Value="$table_name" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        local throttled_writes
        throttled_writes=$(aws cloudwatch get-metric-statistics \
            --namespace "AWS/DynamoDB" \
            --metric-name "WriteThrottledEvents" \
            --dimensions Name=TableName,Value="$table_name" \
            --start-time "$start_time_iso" \
            --end-time "$end_time_iso" \
            --period 300 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text 2>/dev/null || echo "0")
        
        log_info "DynamoDB Metrics: ReadCapacity=$read_capacity, WriteCapacity=$write_capacity, ThrottledReads=$throttled_reads, ThrottledWrites=$throttled_writes"
        
        # Alert on throttling
        if [[ "$throttled_reads" != "0" ]] && [[ "$throttled_reads" != "None" ]] || 
           [[ "$throttled_writes" != "0" ]] && [[ "$throttled_writes" != "None" ]]; then
            log_warn "DynamoDB throttling detected"
            send_dynamodb_alert "$table_name" "THROTTLING" "Reads: $throttled_reads, Writes: $throttled_writes"
        fi
        
        sleep 30
    done
}

# Send alerts
send_lambda_alert() {
    local function_name="$1"
    local alert_type="$2"
    local metric_value="$3"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "warning",
            "title": "⚠️ Lambda Alert: $function_name",
            "fields": [
                {
                    "title": "Alert Type",
                    "value": "$alert_type",
                    "short": true
                },
                {
                    "title": "Metric Value",
                    "value": "$metric_value",
                    "short": true
                },
                {
                    "title": "Function",
                    "value": "$function_name",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date)",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
}

send_api_alert() {
    local api_name="$1"
    local alert_type="$2"
    local metric_value="$3"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "danger",
            "title": "🚨 API Gateway Alert: $api_name",
            "fields": [
                {
                    "title": "Alert Type",
                    "value": "$alert_type",
                    "short": true
                },
                {
                    "title": "Error Rate",
                    "value": "${metric_value}%",
                    "short": true
                },
                {
                    "title": "API",
                    "value": "$api_name ($STAGE)",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date)",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
}

send_dynamodb_alert() {
    local table_name="$1"
    local alert_type="$2"
    local details="$3"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "warning",
            "title": "⚠️ DynamoDB Alert: $table_name",
            "fields": [
                {
                    "title": "Alert Type",
                    "value": "$alert_type",
                    "short": true
                },
                {
                    "title": "Details",
                    "value": "$details",
                    "short": false
                },
                {
                    "title": "Table",
                    "value": "$table_name",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date)",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
}

# Main function
main() {
    local command="${1:-monitor}"
    local resource_name="${2:-}"
    
    case "$command" in
        "monitor-lambda")
            [[ -z "$resource_name" ]] && { log_error "Lambda function name required"; exit 1; }
            monitor_lambda_metrics "$resource_name" "${3:-300}"
            ;;
        "monitor-api")
            [[ -z "$resource_name" ]] && { log_error "API name required"; exit 1; }
            monitor_api_gateway_metrics "$resource_name" "$STAGE" "${3:-300}"
            ;;
        "monitor-dynamodb")
            [[ -z "$resource_name" ]] && { log_error "DynamoDB table name required"; exit 1; }
            monitor_dynamodb_metrics "$resource_name" "${3:-300}"
            ;;
        "health-check")
            [[ -z "$resource_name" ]] && { log_error "Lambda function name required"; exit 1; }
            check_lambda_health "$resource_name"
            ;;
        "monitor-all")
            log_info "Starting comprehensive serverless monitoring..."
            
            # Get function names
            local lambda_functions
            lambda_functions=$(aws lambda list-functions \
                --query "Functions[?starts_with(FunctionName, '${SERVICE_NAME}-${STAGE}-')].FunctionName" \
                --output text)
            
            for func in $lambda_functions; do
                log_info "Starting monitoring for function: $func"
                monitor_lambda_metrics "$func" 300 &
            done
            
            # Monitor API Gateway
            monitor_api_gateway_metrics "$SERVICE_NAME" "$STAGE" 300 &
            
            # Monitor DynamoDB tables
            local dynamodb_tables
            dynamodb_tables=$(aws dynamodb list-tables \
                --query "TableNames[?starts_with(@, '${SERVICE_NAME}-${STAGE}-')]" \
                --output text)
            
            for table in $dynamodb_tables; do
                log_info "Starting monitoring for table: $table"
                monitor_dynamodb_metrics "$table" 300 &
            done
            
            # Wait for all monitoring to complete
            wait
            ;;
        *)
            cat <<EOF
Serverless Monitoring Tool

Usage: $0 <command> [options]

Commands:
  monitor-lambda <function-name> [duration]    - Monitor Lambda function metrics
  monitor-api <api-name> [duration]            - Monitor API Gateway metrics  
  monitor-dynamodb <table-name> [duration]     - Monitor DynamoDB metrics
  health-check <function-name>                 - Check Lambda function health
  monitor-all                                  - Monitor all serverless resources

Examples:
  $0 monitor-lambda production-api-prod-api 600
  $0 monitor-api production-api 300
  $0 health-check production-api-prod-api
  $0 monitor-all
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive production serverless implementation with AWS Lambda, proper monitoring, error handling, and operational scripts for managing serverless applications at scale.