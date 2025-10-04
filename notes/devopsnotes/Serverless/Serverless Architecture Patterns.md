# Serverless Architecture Patterns

**Serverless Architecture Patterns** provide proven architectural blueprints and design patterns for building scalable, resilient, and cost-effective serverless applications using event-driven architectures, microservices patterns, and cloud-native design principles.

## Event-Driven Architecture Patterns

### Event Sourcing with Serverless

#### AWS Event Sourcing Implementation
```yaml
aws_event_sourcing:
  lambda_functions:
    command_handler: |
      # serverless.yml - Command Handler
      service: event-sourcing-commands

      provider:
        name: aws
        runtime: python3.9
        region: us-east-1
        environment:
          EVENT_STORE_TABLE: ${self:service}-event-store-${self:provider.stage}
          AGGREGATE_TABLE: ${self:service}-aggregates-${self:provider.stage}

      functions:
        createOrder:
          handler: handlers/order_commands.create_order
          events:
            - http:
                path: /orders
                method: post
                cors: true
          environment:
            AGGREGATE_TYPE: Order

        updateOrder:
          handler: handlers/order_commands.update_order
          events:
            - http:
                path: /orders/{orderId}
                method: put
                cors: true

        processPayment:
          handler: handlers/payment_commands.process_payment
          events:
            - http:
                path: /orders/{orderId}/payment
                method: post
                cors: true

    event_projections: |
      # Event Projection Handlers
      orderProjection:
        handler: handlers/projections.order_projection
        events:
          - stream:
              type: dynamodb
              arn:
                Fn::GetAtt: [EventStoreTable, StreamArn]
              batchSize: 10
              startingPosition: LATEST
              filterPatterns:
                - eventType: [OrderCreated, OrderUpdated, OrderCancelled]

      inventoryProjection:
        handler: handlers/projections.inventory_projection
        events:
          - stream:
              type: dynamodb
              arn:
                Fn::GetAtt: [EventStoreTable, StreamArn]
              batchSize: 5
              startingPosition: LATEST
              filterPatterns:
                - eventType: [OrderCreated, OrderCancelled, ProductAdded]

  python_implementation: |
    # handlers/order_commands.py
    import json
    import uuid
    import boto3
    from datetime import datetime
    from typing import Dict, Any

    dynamodb = boto3.resource('dynamodb')
    event_store = dynamodb.Table(os.environ['EVENT_STORE_TABLE'])
    aggregate_store = dynamodb.Table(os.environ['AGGREGATE_TABLE'])

    class OrderAggregate:
        def __init__(self, order_id: str):
            self.order_id = order_id
            self.version = 0
            self.status = 'PENDING'
            self.items = []
            self.total_amount = 0
            self.events = []

        def create_order(self, customer_id: str, items: list):
            if self.version > 0:
                raise ValueError("Order already exists")

            event = {
                'event_id': str(uuid.uuid4()),
                'aggregate_id': self.order_id,
                'aggregate_type': 'Order',
                'event_type': 'OrderCreated',
                'event_version': 1,
                'event_data': {
                    'customer_id': customer_id,
                    'items': items,
                    'total_amount': sum(item['price'] * item['quantity'] for item in items),
                    'created_at': datetime.utcnow().isoformat()
                },
                'timestamp': datetime.utcnow().isoformat()
            }

            self.apply_event(event)
            return event

        def update_order(self, items: list):
            if self.status != 'PENDING':
                raise ValueError(f"Cannot update order in {self.status} status")

            event = {
                'event_id': str(uuid.uuid4()),
                'aggregate_id': self.order_id,
                'aggregate_type': 'Order',
                'event_type': 'OrderUpdated',
                'event_version': self.version + 1,
                'event_data': {
                    'items': items,
                    'total_amount': sum(item['price'] * item['quantity'] for item in items),
                    'updated_at': datetime.utcnow().isoformat()
                },
                'timestamp': datetime.utcnow().isoformat()
            }

            self.apply_event(event)
            return event

        def apply_event(self, event: Dict[str, Any]):
            if event['event_type'] == 'OrderCreated':
                self.status = 'PENDING'
                self.items = event['event_data']['items']
                self.total_amount = event['event_data']['total_amount']
            elif event['event_type'] == 'OrderUpdated':
                self.items = event['event_data']['items']
                self.total_amount = event['event_data']['total_amount']
            elif event['event_type'] == 'OrderCancelled':
                self.status = 'CANCELLED'

            self.version += 1
            self.events.append(event)

    def create_order(event, context):
        try:
            body = json.loads(event['body'])
            order_id = str(uuid.uuid4())

            # Create aggregate
            order = OrderAggregate(order_id)
            order_event = order.create_order(
                body['customer_id'],
                body['items']
            )

            # Save event to event store
            event_store.put_item(Item={
                'partition_key': f"Order#{order_id}",
                'sort_key': f"v{order_event['event_version']}",
                **order_event
            })

            # Save aggregate snapshot
            aggregate_store.put_item(Item={
                'aggregate_id': order_id,
                'aggregate_type': 'Order',
                'version': order.version,
                'data': {
                    'status': order.status,
                    'items': order.items,
                    'total_amount': order.total_amount
                },
                'updated_at': datetime.utcnow().isoformat()
            })

            return {
                'statusCode': 201,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'order_id': order_id,
                    'status': order.status,
                    'total_amount': order.total_amount
                })
            }

        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }

  infrastructure: |
    # resources/dynamodb.yml
    Resources:
      EventStoreTable:
        Type: AWS::DynamoDB::Table
        Properties:
          TableName: ${self:service}-event-store-${self:provider.stage}
          BillingMode: PAY_PER_REQUEST
          AttributeDefinitions:
            - AttributeName: partition_key
              AttributeType: S
            - AttributeName: sort_key
              AttributeType: S
          KeySchema:
            - AttributeName: partition_key
              KeyType: HASH
            - AttributeName: sort_key
              KeyType: RANGE
          StreamSpecification:
            StreamViewType: NEW_AND_OLD_IMAGES
          PointInTimeRecoverySpecification:
            PointInTimeRecoveryEnabled: true
          Tags:
            - Key: Environment
              Value: ${self:provider.stage}
            - Key: Service
              Value: ${self:service}

      AggregateTable:
        Type: AWS::DynamoDB::Table
        Properties:
          TableName: ${self:service}-aggregates-${self:provider.stage}
          BillingMode: PAY_PER_REQUEST
          AttributeDefinitions:
            - AttributeName: aggregate_id
              AttributeType: S
          KeySchema:
            - AttributeName: aggregate_id
              KeyType: HASH
          Tags:
            - Key: Environment
              Value: ${self:provider.stage}
            - Key: Service
              Value: ${self:service}
```

### CQRS (Command Query Responsibility Segregation)

#### Serverless CQRS Implementation
```yaml
serverless_cqrs:
  command_side: |
    # Command Side - Write Operations
    service: cqrs-commands

    provider:
      name: aws
      runtime: python3.9
      environment:
        COMMAND_STORE_TABLE: ${self:service}-commands-${self:provider.stage}
        EVENT_BUS_NAME: ${self:service}-event-bus-${self:provider.stage}

    functions:
      createUser:
        handler: commands/user_commands.create_user
        events:
          - http:
              path: /commands/users
              method: post
              cors: true

      updateUser:
        handler: commands/user_commands.update_user
        events:
          - http:
              path: /commands/users/{userId}
              method: put
              cors: true

      deleteUser:
        handler: commands/user_commands.delete_user
        events:
          - http:
              path: /commands/users/{userId}
              method: delete
              cors: true

  query_side: |
    # Query Side - Read Operations
    service: cqrs-queries

    provider:
      name: aws
      runtime: python3.9
      environment:
        READ_MODEL_TABLE: ${self:service}-read-models-${self:provider.stage}
        SEARCH_DOMAIN: ${self:service}-search-${self:provider.stage}

    functions:
      getUser:
        handler: queries/user_queries.get_user
        events:
          - http:
              path: /queries/users/{userId}
              method: get
              cors: true

      getUsersList:
        handler: queries/user_queries.get_users_list
        events:
          - http:
              path: /queries/users
              method: get
              cors: true

      searchUsers:
        handler: queries/user_queries.search_users
        events:
          - http:
              path: /queries/users/search
              method: get
              cors: true

      # Event Handlers for Read Model Updates
      userEventHandler:
        handler: queries/event_handlers.user_event_handler
        events:
          - eventBridge:
              eventBus: ${self:provider.environment.EVENT_BUS_NAME}
              pattern:
                source: ["user.service"]
                detail-type: ["User Created", "User Updated", "User Deleted"]

  command_implementation: |
    # commands/user_commands.py
    import json
    import boto3
    from datetime import datetime
    from typing import Dict, Any

    eventbridge = boto3.client('events')

    def create_user(event, context):
        try:
            body = json.loads(event['body'])
            user_id = str(uuid.uuid4())

            # Validate command
            validation_result = validate_create_user_command(body)
            if not validation_result['valid']:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'errors': validation_result['errors']})
                }

            # Execute command
            command_result = execute_create_user_command(user_id, body)

            # Publish event
            event_detail = {
                'user_id': user_id,
                'email': body['email'],
                'name': body['name'],
                'created_at': datetime.utcnow().isoformat()
            }

            eventbridge.put_events(
                Entries=[{
                    'Source': 'user.service',
                    'DetailType': 'User Created',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': os.environ['EVENT_BUS_NAME']
                }]
            )

            return {
                'statusCode': 201,
                'body': json.dumps({
                    'user_id': user_id,
                    'message': 'User created successfully'
                })
            }

        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

    def validate_create_user_command(data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []

        if 'email' not in data or not data['email']:
            errors.append('Email is required')
        elif not is_valid_email(data['email']):
            errors.append('Invalid email format')

        if 'name' not in data or not data['name']:
            errors.append('Name is required')

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

  query_implementation: |
    # queries/user_queries.py
    import json
    import boto3
    from boto3.dynamodb.conditions import Key, Attr

    dynamodb = boto3.resource('dynamodb')
    read_model_table = dynamodb.Table(os.environ['READ_MODEL_TABLE'])

    def get_user(event, context):
        try:
            user_id = event['pathParameters']['userId']

            response = read_model_table.get_item(
                Key={'pk': f'USER#{user_id}', 'sk': 'PROFILE'}
            )

            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'User not found'})
                }

            user_data = response['Item']

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'user_id': user_data['user_id'],
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'created_at': user_data['created_at'],
                    'updated_at': user_data.get('updated_at')
                })
            }

        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

    def get_users_list(event, context):
        try:
            # Parse query parameters
            params = event.get('queryStringParameters', {}) or {}
            limit = int(params.get('limit', 20))
            last_key = params.get('lastKey')

            scan_kwargs = {
                'FilterExpression': Attr('entity_type').eq('USER'),
                'Limit': limit
            }

            if last_key:
                scan_kwargs['ExclusiveStartKey'] = json.loads(last_key)

            response = read_model_table.scan(**scan_kwargs)

            users = []
            for item in response['Items']:
                users.append({
                    'user_id': item['user_id'],
                    'email': item['email'],
                    'name': item['name'],
                    'created_at': item['created_at']
                })

            result = {'users': users}

            if 'LastEvaluatedKey' in response:
                result['lastKey'] = json.dumps(response['LastEvaluatedKey'])
                result['hasMore'] = True
            else:
                result['hasMore'] = False

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }

        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

  event_handlers: |
    # queries/event_handlers.py
    import json
    import boto3
    from datetime import datetime

    dynamodb = boto3.resource('dynamodb')
    read_model_table = dynamodb.Table(os.environ['READ_MODEL_TABLE'])

    def user_event_handler(event, context):
        try:
            for record in event['Records']:
                event_detail = json.loads(record['body'])
                detail_type = event_detail['detail-type']
                detail = event_detail['detail']

                if detail_type == 'User Created':
                    handle_user_created(detail)
                elif detail_type == 'User Updated':
                    handle_user_updated(detail)
                elif detail_type == 'User Deleted':
                    handle_user_deleted(detail)

            return {'statusCode': 200}

        except Exception as e:
            print(f"Error processing event: {str(e)}")
            raise

    def handle_user_created(detail):
        read_model_table.put_item(Item={
            'pk': f"USER#{detail['user_id']}",
            'sk': 'PROFILE',
            'entity_type': 'USER',
            'user_id': detail['user_id'],
            'email': detail['email'],
            'name': detail['name'],
            'created_at': detail['created_at'],
            'ttl': int((datetime.utcnow().timestamp() + 31536000))  # 1 year TTL
        })

    def handle_user_updated(detail):
        read_model_table.update_item(
            Key={'pk': f"USER#{detail['user_id']}", 'sk': 'PROFILE'},
            UpdateExpression='SET #name = :name, updated_at = :updated_at',
            ExpressionAttributeNames={'#name': 'name'},
            ExpressionAttributeValues={
                ':name': detail['name'],
                ':updated_at': detail['updated_at']
            }
        )

    def handle_user_deleted(detail):
        read_model_table.delete_item(
            Key={'pk': f"USER#{detail['user_id']}", 'sk': 'PROFILE'}
        )
```

## Microservices Patterns

### Serverless Microservices Architecture

#### Service Decomposition Strategy
```yaml
microservices_decomposition:
  domain_driven_design:
    bounded_contexts:
      user_management:
        services:
          - user-registration
          - user-authentication
          - user-profile
        events:
          - UserRegistered
          - UserAuthenticated
          - ProfileUpdated
        data_stores:
          - user-dynamodb-table
          - user-cognito-pool

      order_management:
        services:
          - order-creation
          - order-processing
          - order-fulfillment
        events:
          - OrderCreated
          - OrderProcessed
          - OrderShipped
        data_stores:
          - order-dynamodb-table
          - order-event-store

      inventory_management:
        services:
          - inventory-tracking
          - stock-updates
          - reorder-alerts
        events:
          - StockUpdated
          - ReorderRequired
          - InventoryAlert
        data_stores:
          - inventory-dynamodb-table
          - metrics-timestream

  service_mesh_pattern: |
    # Service Mesh with AWS App Mesh
    service: order-microservice

    provider:
      name: aws
      runtime: python3.9

    custom:
      appMesh:
        meshName: ${self:service}-mesh
        virtualNodeName: ${self:service}-node
        virtualServiceName: ${self:service}-service

    functions:
      createOrder:
        handler: src/handlers/orders.create_order
        events:
          - http:
              path: /orders
              method: post
        environment:
          MESH_ENDPOINT: ${self:custom.appMesh.virtualServiceName}

    resources:
      Resources:
        AppMesh:
          Type: AWS::AppMesh::Mesh
          Properties:
            MeshName: ${self:custom.appMesh.meshName}

        VirtualNode:
          Type: AWS::AppMesh::VirtualNode
          Properties:
            MeshName: !Ref AppMesh
            VirtualNodeName: ${self:custom.appMesh.virtualNodeName}
            Spec:
              ServiceDiscovery:
                CloudMap:
                  ServiceName: ${self:service}
                  NamespaceName: ${self:service}-namespace
              Listeners:
                - PortMapping:
                    Port: 80
                    Protocol: http
                  HealthCheck:
                    Protocol: http
                    Path: /health
                    HealthyThreshold: 2
                    UnhealthyThreshold: 3
                    TimeoutMillis: 2000
                    IntervalMillis: 5000
              Backends:
                - VirtualService:
                    VirtualServiceName: inventory-service
                - VirtualService:
                    VirtualServiceName: payment-service

  api_gateway_pattern: |
    # API Gateway as Service Gateway
    service: api-gateway

    provider:
      name: aws
      runtime: python3.9

    functions:
      authorizer:
        handler: src/authorizer.handler

      proxy:
        handler: src/proxy.handler
        events:
          - http:
              path: /{proxy+}
              method: ANY
              authorizer:
                name: authorizer
                resultTtlInSeconds: 300
                identitySource: method.request.header.Authorization
                type: request

    custom:
      routes:
        - path: /users/*
          service: user-service
          upstream: https://user-service.company.com
        - path: /orders/*
          service: order-service
          upstream: https://order-service.company.com
        - path: /inventory/*
          service: inventory-service
          upstream: https://inventory-service.company.com

  circuit_breaker_pattern: |
    # Circuit Breaker Implementation
    import time
    import logging
    from enum import Enum
    from typing import Callable, Any
    from dataclasses import dataclass, field

    class CircuitState(Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"

    @dataclass
    class CircuitBreakerConfig:
        failure_threshold: int = 5
        recovery_timeout: int = 30
        expected_exception: type = Exception
        success_threshold: int = 3  # For half-open state

    @dataclass
    class CircuitBreakerStats:
        failure_count: int = 0
        success_count: int = 0
        last_failure_time: float = 0
        state: CircuitState = CircuitState.CLOSED

    class CircuitBreaker:
        def __init__(self, config: CircuitBreakerConfig):
            self.config = config
            self.stats = CircuitBreakerStats()
            self.logger = logging.getLogger(__name__)

        def __call__(self, func: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> Any:
                if self.stats.state == CircuitState.OPEN:
                    if self._should_try_reset():
                        self._set_half_open()
                    else:
                        raise Exception("Circuit breaker is OPEN")

                try:
                    result = func(*args, **kwargs)
                    self._on_success()
                    return result
                except self.config.expected_exception as e:
                    self._on_failure()
                    raise e

            return wrapper

        def _should_try_reset(self) -> bool:
            return (time.time() - self.stats.last_failure_time) >= self.config.recovery_timeout

        def _set_half_open(self):
            self.stats.state = CircuitState.HALF_OPEN
            self.stats.success_count = 0
            self.logger.info("Circuit breaker state changed to HALF_OPEN")

        def _on_success(self):
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.success_count += 1
                if self.stats.success_count >= self.config.success_threshold:
                    self._close_circuit()
            else:
                self.stats.failure_count = 0

        def _on_failure(self):
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()

            if self.stats.failure_count >= self.config.failure_threshold:
                self._open_circuit()

        def _close_circuit(self):
            self.stats.state = CircuitState.CLOSED
            self.stats.failure_count = 0
            self.stats.success_count = 0
            self.logger.info("Circuit breaker state changed to CLOSED")

        def _open_circuit(self):
            self.stats.state = CircuitState.OPEN
            self.logger.warning("Circuit breaker state changed to OPEN")

    # Usage in Lambda function
    circuit_breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=requests.RequestException
    ))

    @circuit_breaker
    def call_external_service(url: str, data: dict):
        response = requests.post(url, json=data, timeout=5)
        response.raise_for_status()
        return response.json()
```

## Serverless Data Patterns

### Event Streaming Patterns

#### Kinesis-based Event Streaming
```yaml
kinesis_event_streaming:
  kinesis_analytics: |
    # Real-time Analytics with Kinesis
    service: event-analytics

    provider:
      name: aws
      runtime: python3.9

    functions:
      eventProducer:
        handler: src/producer.handler
        events:
          - http:
              path: /events
              method: post
        environment:
          KINESIS_STREAM_NAME: ${self:service}-events-${self:provider.stage}

      eventProcessor:
        handler: src/processor.handler
        events:
          - stream:
              type: kinesis
              arn:
                Fn::GetAtt: [EventStream, Arn]
              batchSize: 100
              startingPosition: LATEST
              maximumBatchingWindowInSeconds: 5
              parallelizationFactor: 10

      analyticsProcessor:
        handler: src/analytics.handler
        events:
          - stream:
              type: kinesis
              arn:
                Fn::GetAtt: [AnalyticsStream, Arn]
              batchSize: 1000
              startingPosition: LATEST
              maximumBatchingWindowInSeconds: 30

    resources:
      Resources:
        EventStream:
          Type: AWS::Kinesis::Stream
          Properties:
            Name: ${self:service}-events-${self:provider.stage}
            ShardCount: 5
            StreamModeDetails:
              StreamMode: PROVISIONED
            StreamEncryption:
              EncryptionType: KMS
              KeyId: alias/aws/kinesis
            Tags:
              - Key: Environment
                Value: ${self:provider.stage}

        AnalyticsApplication:
          Type: AWS::KinesisAnalyticsV2::Application
          Properties:
            ApplicationName: ${self:service}-analytics
            RuntimeEnvironment: FLINK-1_13
            ServiceExecutionRole: !GetAtt AnalyticsRole.Arn
            ApplicationConfiguration:
              FlinkApplicationConfiguration:
                CheckpointConfiguration:
                  ConfigurationType: DEFAULT
                MonitoringConfiguration:
                  ConfigurationType: DEFAULT
                  LogLevel: INFO
                  MetricsLevel: APPLICATION
                ParallelismConfiguration:
                  ConfigurationType: DEFAULT
                  Parallelism: 4
                  ParallelismPerKPU: 1
                  AutoScalingEnabled: true

  event_producer: |
    # src/producer.py
    import json
    import boto3
    import uuid
    from datetime import datetime
    from typing import Dict, Any

    kinesis = boto3.client('kinesis')

    def handler(event, context):
        try:
            body = json.loads(event['body'])

            # Enrich event with metadata
            enriched_event = {
                'event_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'source': body.get('source', 'unknown'),
                'event_type': body.get('event_type'),
                'data': body.get('data', {}),
                'correlation_id': body.get('correlation_id', str(uuid.uuid4())),
                'version': '1.0'
            }

            # Determine partition key for event ordering
            partition_key = body.get('partition_key', enriched_event['correlation_id'])

            # Put record to Kinesis
            response = kinesis.put_record(
                StreamName=os.environ['KINESIS_STREAM_NAME'],
                Data=json.dumps(enriched_event),
                PartitionKey=partition_key
            )

            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'event_id': enriched_event['event_id'],
                    'shard_id': response['ShardId'],
                    'sequence_number': response['SequenceNumber']
                })
            }

        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

  event_processor: |
    # src/processor.py
    import json
    import boto3
    from typing import List, Dict, Any

    dynamodb = boto3.resource('dynamodb')
    sns = boto3.client('sns')

    def handler(event, context):
        processed_events = []
        failed_events = []

        for record in event['Records']:
            try:
                # Decode Kinesis record
                payload = json.loads(record['kinesis']['data'])

                # Process based on event type
                result = process_event(payload)

                if result['success']:
                    processed_events.append({
                        'eventId': payload['event_id'],
                        'status': 'processed'
                    })
                else:
                    failed_events.append({
                        'eventId': payload['event_id'],
                        'error': result['error']
                    })

            except Exception as e:
                failed_events.append({
                    'recordId': record['kinesis']['sequenceNumber'],
                    'error': str(e)
                })

        # Send processing metrics
        send_processing_metrics(len(processed_events), len(failed_events))

        return {
            'processed': len(processed_events),
            'failed': len(failed_events),
            'details': {
                'processed': processed_events,
                'failed': failed_events
            }
        }

    def process_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            event_type = event_data['event_type']

            if event_type == 'user.created':
                return process_user_created(event_data)
            elif event_type == 'order.placed':
                return process_order_placed(event_data)
            elif event_type == 'payment.processed':
                return process_payment_processed(event_data)
            else:
                return {'success': False, 'error': f'Unknown event type: {event_type}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def process_user_created(event_data: Dict[str, Any]) -> Dict[str, Any]:
        # Store user data in DynamoDB
        user_table = dynamodb.Table('users')

        user_table.put_item(Item={
            'user_id': event_data['data']['user_id'],
            'email': event_data['data']['email'],
            'created_at': event_data['timestamp'],
            'status': 'active'
        })

        # Send welcome notification
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:ACCOUNT:user-notifications',
            Message=json.dumps({
                'type': 'welcome_email',
                'user_id': event_data['data']['user_id'],
                'email': event_data['data']['email']
            })
        )

        return {'success': True}
```

This comprehensive Serverless Architecture Patterns document provides advanced architectural blueprints including event sourcing, CQRS, microservices patterns, circuit breakers, and event streaming patterns essential for building enterprise-grade serverless applications.