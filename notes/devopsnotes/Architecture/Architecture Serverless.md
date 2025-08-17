# Architecture Serverless

## Core Concepts

Serverless architecture is a cloud computing model where the cloud provider manages the infrastructure, automatically scaling resources based on demand. Applications are broken down into stateless functions that are triggered by events, with developers focusing purely on business logic rather than infrastructure management.

### Function-as-a-Service (FaaS)

**Definition:** A serverless computing service that executes functions in response to events without requiring server management.

**Key Characteristics:**
- **Stateless Functions:** Each function execution is independent
- **Event-Driven:** Functions triggered by events (HTTP requests, database changes, file uploads)
- **Auto-scaling:** Automatic scaling from zero to thousands of concurrent executions
- **Pay-per-execution:** Only pay for actual function execution time
- **Managed Runtime:** Cloud provider handles infrastructure, OS, and runtime

**Example - AWS Lambda Order Processing Function:**
```python
import json
import boto3
from decimal import Decimal
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS services
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    AWS Lambda function to process incoming orders
    Triggered by API Gateway HTTP POST requests
    """
    
    try:
        # Extract order data from event
        order_data = json.loads(event['body'])
        
        # Validate order data
        validation_result = validate_order(order_data)
        if not validation_result['valid']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid order data',
                    'details': validation_result['errors']
                })
            }
        
        # Generate order ID
        order_id = generate_order_id()
        
        # Create order record
        order = {
            'order_id': order_id,
            'customer_id': order_data['customer_id'],
            'items': order_data['items'],
            'total_amount': Decimal(str(calculate_total(order_data['items']))),
            'status': 'PENDING',
            'created_at': datetime.utcnow().isoformat(),
            'shipping_address': order_data['shipping_address'],
            'payment_method': order_data['payment_method']
        }
        
        # Save to DynamoDB
        orders_table = dynamodb.Table('Orders')
        orders_table.put_item(Item=order)
        
        logger.info(f"Order {order_id} created successfully")
        
        # Send order to processing queue
        await send_to_processing_queue(order)
        
        # Send confirmation notification
        await send_order_confirmation(order)
        
        # Return success response
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'order_id': order_id,
                'status': 'created',
                'message': 'Order created successfully'
            })
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(400, "Validation failed", str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return error_response(500, "Internal server error", "Order processing failed")

def validate_order(order_data):
    """Validate order data structure and business rules"""
    errors = []
    
    # Required fields
    required_fields = ['customer_id', 'items', 'shipping_address', 'payment_method']
    for field in required_fields:
        if field not in order_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate items
    if 'items' in order_data:
        if not isinstance(order_data['items'], list) or len(order_data['items']) == 0:
            errors.append("Order must contain at least one item")
        
        for i, item in enumerate(order_data['items']):
            if 'product_id' not in item:
                errors.append(f"Item {i}: Missing product_id")
            if 'quantity' not in item or item['quantity'] <= 0:
                errors.append(f"Item {i}: Invalid quantity")
            if 'price' not in item or item['price'] <= 0:
                errors.append(f"Item {i}: Invalid price")
    
    # Validate total amount
    if 'items' in order_data:
        calculated_total = calculate_total(order_data['items'])
        if calculated_total <= 0:
            errors.append("Order total must be greater than zero")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def calculate_total(items):
    """Calculate order total from items"""
    return sum(item['quantity'] * item['price'] for item in items)

def generate_order_id():
    """Generate unique order ID"""
    import uuid
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"

async def send_to_processing_queue(order):
    """Send order to SQS queue for further processing"""
    queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789/order-processing-queue'
    
    message = {
        'order_id': order['order_id'],
        'customer_id': order['customer_id'],
        'total_amount': float(order['total_amount']),
        'items': order['items']
    }
    
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message),
        MessageAttributes={
            'OrderType': {
                'StringValue': 'standard',
                'DataType': 'String'
            },
            'Priority': {
                'StringValue': 'normal',
                'DataType': 'String'
            }
        }
    )

async def send_order_confirmation(order):
    """Send order confirmation via SNS"""
    topic_arn = 'arn:aws:sns:us-east-1:123456789:order-confirmations'
    
    message = {
        'order_id': order['order_id'],
        'customer_id': order['customer_id'],
        'total_amount': float(order['total_amount']),
        'status': 'confirmed'
    }
    
    sns.publish(
        TopicArn=topic_arn,
        Message=json.dumps(message),
        Subject=f"Order Confirmation - {order['order_id']}"
    )

def error_response(status_code, error, message):
    """Return formatted error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': error,
            'message': message
        })
    }
```

**Cold Start Optimization:**
```python
# Global variables for connection reuse (outside handler)
import boto3
from datetime import datetime

# Initialize connections globally to reuse across invocations
dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table('Orders')

# Connection pooling for external APIs
import httpx
http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
    timeout=httpx.Timeout(10.0)
)

# Cache expensive computations
CONFIG_CACHE = {}

def lambda_handler(event, context):
    """Optimized handler with minimal cold start impact"""
    
    # Use pre-initialized connections
    # Reuse cached data where possible
    
    start_time = datetime.utcnow()
    
    try:
        # Business logic here
        result = process_request(event)
        
        # Log performance metrics
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        print(f"Execution time: {execution_time:.3f}s")
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

def process_request(event):
    """Process the actual request"""
    # Implementation here
    pass

# Provisioned Concurrency Configuration (serverless.yml)
"""
service: order-processing

provider:
  name: aws
  runtime: python3.9
  environment:
    ORDERS_TABLE: ${self:service}-orders-${self:provider.stage}
    
functions:
  processOrder:
    handler: handler.lambda_handler
    events:
      - http:
          path: /orders
          method: post
    provisionedConcurrency: 2  # Keep 2 instances warm
    reservedConcurrency: 100   # Limit max concurrent executions
    timeout: 30
    memorySize: 512
"""
```

### Backend-as-a-Service (BaaS)

**Definition:** Cloud services that provide backend functionality as managed services, eliminating the need to build and maintain backend infrastructure.

**Example - Serverless E-commerce Backend:**
```yaml
# serverless.yml - Complete BaaS setup
service: ecommerce-backend

provider:
  name: aws
  runtime: python3.9
  stage: ${opt:stage, 'dev'}
  region: us-east-1
  
  environment:
    ORDERS_TABLE: ${self:service}-orders-${self:provider.stage}
    USERS_TABLE: ${self:service}-users-${self:provider.stage}
    PRODUCTS_TABLE: ${self:service}-products-${self:provider.stage}
    S3_BUCKET: ${self:service}-uploads-${self:provider.stage}
    
  iamRoleStatements:
    - Effect: Allow
      Action:
        - dynamodb:Query
        - dynamodb:Scan
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:UpdateItem
        - dynamodb:DeleteItem
      Resource:
        - "arn:aws:dynamodb:${self:provider.region}:*:table/${self:provider.environment.ORDERS_TABLE}"
        - "arn:aws:dynamodb:${self:provider.region}:*:table/${self:provider.environment.USERS_TABLE}"
        - "arn:aws:dynamodb:${self:provider.region}:*:table/${self:provider.environment.PRODUCTS_TABLE}"
    - Effect: Allow
      Action:
        - s3:GetObject
        - s3:PutObject
        - s3:DeleteObject
      Resource:
        - "arn:aws:s3:::${self:provider.environment.S3_BUCKET}/*"
    - Effect: Allow
      Action:
        - sns:Publish
      Resource:
        - "arn:aws:sns:${self:provider.region}:*:*"
    - Effect: Allow
      Action:
        - sqs:SendMessage
        - sqs:ReceiveMessage
        - sqs:DeleteMessage
      Resource:
        - "arn:aws:sqs:${self:provider.region}:*:*"

functions:
  # User Management Functions
  createUser:
    handler: users.create
    events:
      - http:
          path: /users
          method: post
          cors: true
  
  getUser:
    handler: users.get
    events:
      - http:
          path: /users/{id}
          method: get
          cors: true
          authorizer: aws_iam
  
  # Product Management Functions  
  listProducts:
    handler: products.list
    events:
      - http:
          path: /products
          method: get
          cors: true
  
  getProduct:
    handler: products.get
    events:
      - http:
          path: /products/{id}
          method: get
          cors: true
  
  # Order Management Functions
  createOrder:
    handler: orders.create
    events:
      - http:
          path: /orders
          method: post
          cors: true
          authorizer: aws_iam
  
  processOrder:
    handler: orders.process
    events:
      - sqs:
          arn:
            Fn::GetAtt:
              - OrderProcessingQueue
              - Arn
  
  # File Upload Functions
  uploadFile:
    handler: files.upload
    events:
      - http:
          path: /upload
          method: post
          cors: true
          authorizer: aws_iam
  
  # Notification Functions
  sendNotification:
    handler: notifications.send
    events:
      - sns:
          arn:
            Ref: NotificationTopic

resources:
  Resources:
    # DynamoDB Tables
    OrdersTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:provider.environment.ORDERS_TABLE}
        AttributeDefinitions:
          - AttributeName: order_id
            AttributeType: S
          - AttributeName: customer_id
            AttributeType: S
          - AttributeName: created_at
            AttributeType: S
        KeySchema:
          - AttributeName: order_id
            KeyType: HASH
        GlobalSecondaryIndexes:
          - IndexName: CustomerOrdersIndex
            KeySchema:
              - AttributeName: customer_id
                KeyType: HASH
              - AttributeName: created_at
                KeyType: RANGE
            Projection:
              ProjectionType: ALL
            ProvisionedThroughput:
              ReadCapacityUnits: 5
              WriteCapacityUnits: 5
        BillingMode: PAY_PER_REQUEST
    
    UsersTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:provider.environment.USERS_TABLE}
        AttributeDefinitions:
          - AttributeName: user_id
            AttributeType: S
          - AttributeName: email
            AttributeType: S
        KeySchema:
          - AttributeName: user_id
            KeyType: HASH
        GlobalSecondaryIndexes:
          - IndexName: EmailIndex
            KeySchema:
              - AttributeName: email
                KeyType: HASH
            Projection:
              ProjectionType: ALL
            ProvisionedThroughput:
              ReadCapacityUnits: 5
              WriteCapacityUnits: 5
        BillingMode: PAY_PER_REQUEST
    
    ProductsTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:provider.environment.PRODUCTS_TABLE}
        AttributeDefinitions:
          - AttributeName: product_id
            AttributeType: S
          - AttributeName: category
            AttributeType: S
        KeySchema:
          - AttributeName: product_id
            KeyType: HASH
        GlobalSecondaryIndexes:
          - IndexName: CategoryIndex
            KeySchema:
              - AttributeName: category
                KeyType: HASH
            Projection:
              ProjectionType: ALL
            ProvisionedThroughput:
              ReadCapacityUnits: 5
              WriteCapacityUnits: 5
        BillingMode: PAY_PER_REQUEST
    
    # S3 Bucket for File Storage
    FileUploadBucket:
      Type: AWS::S3::Bucket
      Properties:
        BucketName: ${self:provider.environment.S3_BUCKET}
        CorsConfiguration:
          CorsRules:
            - AllowedOrigins:
                - "*"
              AllowedMethods:
                - GET
                - PUT
                - POST
              AllowedHeaders:
                - "*"
    
    # SQS Queue for Order Processing
    OrderProcessingQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: ${self:service}-order-processing-${self:provider.stage}
        VisibilityTimeoutSeconds: 300
        MessageRetentionPeriod: 1209600  # 14 days
        RedrivePolicy:
          deadLetterTargetArn:
            Fn::GetAtt:
              - OrderProcessingDLQ
              - Arn
          maxReceiveCount: 3
    
    # Dead Letter Queue
    OrderProcessingDLQ:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: ${self:service}-order-processing-dlq-${self:provider.stage}
        MessageRetentionPeriod: 1209600  # 14 days
    
    # SNS Topic for Notifications
    NotificationTopic:
      Type: AWS::SNS::Topic
      Properties:
        TopicName: ${self:service}-notifications-${self:provider.stage}
        DisplayName: "E-commerce Notifications"
    
    # CloudWatch Log Groups
    LogGroup:
      Type: AWS::Logs::LogGroup
      Properties:
        LogGroupName: /aws/lambda/${self:service}-${self:provider.stage}
        RetentionInDays: 14

plugins:
  - serverless-python-requirements
  - serverless-offline
  - serverless-domain-manager

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true
  
  customDomain:
    domainName: api.${self:provider.stage}.example.com
    basePath: 'v1'
    stage: ${self:provider.stage}
    createRoute53Record: true
```

**Authentication Service Integration:**
```python
# auth.py - Serverless authentication
import json
import jwt
import boto3
from datetime import datetime, timedelta
import bcrypt

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('ecommerce-backend-users-dev')

def register(event, context):
    """Register new user with Cognito and DynamoDB"""
    
    try:
        user_data = json.loads(event['body'])
        
        # Validate input
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if field not in user_data:
                return error_response(400, f"Missing field: {field}")
        
        # Create user in Cognito
        cognito_response = cognito.admin_create_user(
            UserPoolId='us-east-1_XXXXXXXXX',
            Username=user_data['email'],
            UserAttributes=[
                {'Name': 'email', 'Value': user_data['email']},
                {'Name': 'name', 'Value': user_data['name']},
                {'Name': 'email_verified', 'Value': 'false'}
            ],
            TemporaryPassword=user_data['password'],
            MessageAction='SUPPRESS'  # Don't send welcome email
        )
        
        # Generate user ID
        user_id = cognito_response['User']['Username']
        
        # Store additional user data in DynamoDB
        user_profile = {
            'user_id': user_id,
            'email': user_data['email'],
            'name': user_data['name'],
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending_verification',
            'preferences': {
                'notifications': True,
                'marketing_emails': user_data.get('marketing_emails', False)
            }
        }
        
        users_table.put_item(Item=user_profile)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'user_id': user_id,
                'email': user_data['email'],
                'message': 'User registered successfully'
            })
        }
        
    except cognito.exceptions.UsernameExistsException:
        return error_response(409, "User already exists")
    
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return error_response(500, "Registration failed")

def login(event, context):
    """Authenticate user and return JWT token"""
    
    try:
        credentials = json.loads(event['body'])
        
        # Authenticate with Cognito
        response = cognito.admin_initiate_auth(
            UserPoolId='us-east-1_XXXXXXXXX',
            ClientId='XXXXXXXXXXXXXXXXXXXXXXXXXX',
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': credentials['email'],
                'PASSWORD': credentials['password']
            }
        )
        
        # Get user details
        user_details = cognito.admin_get_user(
            UserPoolId='us-east-1_XXXXXXXXX',
            Username=credentials['email']
        )
        
        # Get user profile from DynamoDB
        user_profile = users_table.get_item(
            Key={'user_id': user_details['Username']}
        ).get('Item')
        
        # Prepare token payload
        token_payload = {
            'user_id': user_details['Username'],
            'email': credentials['email'],
            'name': user_profile.get('name', ''),
            'roles': user_profile.get('roles', ['user']),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        # Generate JWT token
        token = jwt.encode(
            token_payload, 
            'your-secret-key', 
            algorithm='HS256'
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'access_token': token,
                'token_type': 'Bearer',
                'expires_in': 86400,  # 24 hours
                'user': {
                    'user_id': user_details['Username'],
                    'email': credentials['email'],
                    'name': user_profile.get('name', '')
                }
            })
        }
        
    except cognito.exceptions.NotAuthorizedException:
        return error_response(401, "Invalid credentials")
    
    except Exception as e:
        print(f"Login error: {str(e)}")
        return error_response(500, "Login failed")

def verify_token(event, context):
    """Verify JWT token for API Gateway authorizer"""
    
    try:
        # Extract token from authorization header
        token = event['authorizationToken'].replace('Bearer ', '')
        
        # Decode and verify token
        payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
        
        # Generate policy
        policy = {
            'principalId': payload['user_id'],
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Action': 'execute-api:Invoke',
                        'Effect': 'Allow',
                        'Resource': event['methodArn']
                    }
                ]
            },
            'context': {
                'user_id': payload['user_id'],
                'email': payload['email'],
                'roles': ','.join(payload['roles'])
            }
        }
        
        return policy
        
    except jwt.ExpiredSignatureError:
        raise Exception('Unauthorized: Token expired')
    
    except jwt.InvalidTokenError:
        raise Exception('Unauthorized: Invalid token')
    
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        raise Exception('Unauthorized')

def error_response(status_code, message):
    """Return formatted error response"""
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }
```

## Advanced Serverless Patterns

### Step Functions Orchestration

**Definition:** AWS Step Functions provide serverless workflow orchestration for complex business processes using state machines.

**Example - Order Processing Workflow:**
```json
{
  "Comment": "E-commerce order processing workflow",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:validateOrder",
      "Next": "CheckInventory",
      "Catch": [{
        "ErrorEquals": ["ValidationError"],
        "Next": "OrderValidationFailed"
      }]
    },
    "CheckInventory": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:checkInventory",
      "Next": "ProcessPayment",
      "Catch": [{
        "ErrorEquals": ["InsufficientInventory"],
        "Next": "NotifyOutOfStock"
      }]
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:processPayment",
      "Next": "PaymentChoice",
      "Retry": [{
        "ErrorEquals": ["PaymentGatewayTimeout"],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2.0
      }]
    },
    "PaymentChoice": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.paymentStatus",
        "StringEquals": "success",
        "Next": "FulfillOrder"
      }, {
        "Variable": "$.paymentStatus",
        "StringEquals": "failed",
        "Next": "PaymentFailed"
      }],
      "Default": "PaymentPending"
    },
    "FulfillOrder": {
      "Type": "Parallel",
      "Branches": [{
        "StartAt": "ReserveInventory",
        "States": {
          "ReserveInventory": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789:function:reserveInventory",
            "End": true
          }
        }
      }, {
        "StartAt": "SendConfirmation",
        "States": {
          "SendConfirmation": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789:function:sendConfirmation",
            "End": true
          }
        }
      }, {
        "StartAt": "ScheduleShipping",
        "States": {
          "ScheduleShipping": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789:function:scheduleShipping",
            "End": true
          }
        }
      }],
      "Next": "OrderCompleted"
    },
    "OrderCompleted": {
      "Type": "Succeed",
      "Comment": "Order processing completed successfully"
    },
    "OrderValidationFailed": {
      "Type": "Fail",
      "Cause": "Order validation failed",
      "Error": "ValidationError"
    },
    "NotifyOutOfStock": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:notifyOutOfStock",
      "Next": "OrderFailed"
    },
    "PaymentFailed": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:handlePaymentFailure",
      "Next": "OrderFailed"
    },
    "PaymentPending": {
      "Type": "Wait",
      "Seconds": 300,
      "Next": "CheckPaymentStatus"
    },
    "CheckPaymentStatus": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:checkPaymentStatus",
      "Next": "PaymentChoice"
    },
    "OrderFailed": {
      "Type": "Fail",
      "Cause": "Order processing failed",
      "Error": "OrderProcessingError"
    }
  }
}
```

**Step Functions State Management:**
```python
import boto3
import json
from typing import Dict, Any

class StepFunctionsOrchestrator:
    """Step Functions workflow orchestrator"""
    
    def __init__(self, state_machine_arn: str):
        self.stepfunctions = boto3.client('stepfunctions')
        self.state_machine_arn = state_machine_arn
    
    def start_execution(self, execution_name: str, input_data: Dict[str, Any]) -> str:
        """Start workflow execution"""
        
        response = self.stepfunctions.start_execution(
            stateMachineArn=self.state_machine_arn,
            name=execution_name,
            input=json.dumps(input_data)
        )
        
        return response['executionArn']
    
    def get_execution_status(self, execution_arn: str) -> Dict[str, Any]:
        """Get execution status and results"""
        
        response = self.stepfunctions.describe_execution(
            executionArn=execution_arn
        )
        
        return {
            'status': response['status'],
            'start_date': response['startDate'].isoformat(),
            'stop_date': response.get('stopDate', '').isoformat() if response.get('stopDate') else None,
            'input': json.loads(response['input']),
            'output': json.loads(response.get('output', '{}'))
        }
    
    def handle_workflow_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Step Functions workflow events"""
        
        execution_arn = event['detail']['executionArn']
        status = event['detail']['status']
        
        if status == 'SUCCEEDED':
            return self._handle_success(execution_arn)
        elif status == 'FAILED':
            return self._handle_failure(execution_arn)
        elif status == 'TIMED_OUT':
            return self._handle_timeout(execution_arn)
        
        return {'status': 'unknown'}
    
    def _handle_success(self, execution_arn: str) -> Dict[str, Any]:
        """Handle successful workflow completion"""
        execution_details = self.get_execution_status(execution_arn)
        
        # Send success notification
        output = execution_details['output']
        
        return {
            'status': 'success',
            'execution_arn': execution_arn,
            'result': output
        }
    
    def _handle_failure(self, execution_arn: str) -> Dict[str, Any]:
        """Handle workflow failure"""
        execution_details = self.get_execution_status(execution_arn)
        
        # Log failure and send alert
        error_details = execution_details.get('error', 'Unknown error')
        
        return {
            'status': 'failed',
            'execution_arn': execution_arn,
            'error': error_details
        }
    
    def _handle_timeout(self, execution_arn: str) -> Dict[str, Any]:
        """Handle workflow timeout"""
        return {
            'status': 'timeout',
            'execution_arn': execution_arn,
            'message': 'Workflow execution timed out'
        }

# Workflow state implementations
def validate_order(event, context):
    """Validate order data"""
    order = event['order']
    
    # Validate required fields
    required_fields = ['customer_id', 'items', 'shipping_address']
    for field in required_fields:
        if field not in order:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate business rules
    if not order['items']:
        raise ValidationError("Order must contain at least one item")
    
    total = sum(item['price'] * item['quantity'] for item in order['items'])
    if total <= 0:
        raise ValidationError("Order total must be greater than zero")
    
    return {
        **event,
        'validation_status': 'passed',
        'order_total': total
    }

def check_inventory(event, context):
    """Check item availability"""
    order = event['order']
    
    # Check each item availability
    availability = []
    for item in order['items']:
        # Simulate inventory check
        available_quantity = get_available_quantity(item['product_id'])
        
        if available_quantity >= item['quantity']:
            availability.append({
                'product_id': item['product_id'],
                'requested': item['quantity'],
                'available': available_quantity,
                'status': 'available'
            })
        else:
            availability.append({
                'product_id': item['product_id'],
                'requested': item['quantity'],
                'available': available_quantity,
                'status': 'insufficient'
            })
    
    # Check if all items are available
    all_available = all(item['status'] == 'available' for item in availability)
    
    if not all_available:
        raise InsufficientInventoryError("Some items are out of stock")
    
    return {
        **event,
        'inventory_check': 'passed',
        'availability': availability
    }

def get_available_quantity(product_id: str) -> int:
    """Get available quantity for product"""
    # Simulate database lookup
    inventory = {
        'PROD001': 100,
        'PROD002': 50,
        'PROD003': 0
    }
    return inventory.get(product_id, 0)

class ValidationError(Exception):
    pass

class InsufficientInventoryError(Exception):
    pass
```

### EventBridge Event Routing

**Definition:** Amazon EventBridge provides serverless event routing for decoupled architectures with pattern matching and filtering.

**Example - Multi-Service Event Architecture:**
```python
import boto3
import json
from typing import Dict, Any, List
from datetime import datetime

class EventBridgeRouter:
    """EventBridge event routing and management"""
    
    def __init__(self, event_bus_name: str = 'default'):
        self.eventbridge = boto3.client('events')
        self.event_bus_name = event_bus_name
    
    def publish_event(self, source: str, detail_type: str, detail: Dict[str, Any]) -> str:
        """Publish event to EventBridge"""
        
        event_entry = {
            'Source': source,
            'DetailType': detail_type,
            'Detail': json.dumps(detail),
            'EventBusName': self.event_bus_name,
            'Time': datetime.utcnow()
        }
        
        response = self.eventbridge.put_events(
            Entries=[event_entry]
        )
        
        if response['FailedEntryCount'] > 0:
            raise Exception(f"Failed to publish event: {response['Entries'][0]['ErrorMessage']}")
        
        return response['Entries'][0]['EventId']
    
    def create_rule(self, rule_name: str, event_pattern: Dict[str, Any], 
                   targets: List[Dict[str, str]]) -> str:
        """Create EventBridge rule with pattern matching"""
        
        # Create rule
        self.eventbridge.put_rule(
            Name=rule_name,
            EventPattern=json.dumps(event_pattern),
            State='ENABLED',
            EventBusName=self.event_bus_name,
            Description=f"Route events matching pattern: {event_pattern}"
        )
        
        # Add targets
        formatted_targets = []
        for i, target in enumerate(targets):
            formatted_targets.append({
                'Id': str(i + 1),
                'Arn': target['arn'],
                'RoleArn': target.get('role_arn')
            })
        
        self.eventbridge.put_targets(
            Rule=rule_name,
            EventBusName=self.event_bus_name,
            Targets=formatted_targets
        )
        
        return rule_name

# Event publishers
def order_service_events(event, context):
    """Order service event publisher"""
    
    router = EventBridgeRouter('ecommerce-events')
    
    order_data = json.loads(event['body'])
    
    # Publish order created event
    event_detail = {
        'order_id': order_data['order_id'],
        'customer_id': order_data['customer_id'],
        'total_amount': order_data['total_amount'],
        'items': order_data['items'],
        'status': 'created',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    router.publish_event(
        source='ecommerce.orders',
        detail_type='Order Created',
        detail=event_detail
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Order created and event published',
            'order_id': order_data['order_id']
        })
    }

def inventory_service_events(event, context):
    """Inventory service event publisher"""
    
    router = EventBridgeRouter('ecommerce-events')
    
    # Handle order created events
    for record in event['Records']:
        event_detail = json.loads(record['body'])
        
        if event_detail['detail-type'] == 'Order Created':
            order_detail = event_detail['detail']
            
            # Reserve inventory
            reservation_result = reserve_inventory_items(order_detail['items'])
            
            # Publish inventory reserved event
            inventory_event = {
                'order_id': order_detail['order_id'],
                'reservations': reservation_result,
                'status': 'reserved' if reservation_result['success'] else 'failed',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            router.publish_event(
                source='ecommerce.inventory',
                detail_type='Inventory Reserved',
                detail=inventory_event
            )

def payment_service_events(event, context):
    """Payment service event publisher"""
    
    router = EventBridgeRouter('ecommerce-events')
    
    # Handle inventory reserved events
    for record in event['Records']:
        event_detail = json.loads(record['body'])
        
        if event_detail['detail-type'] == 'Inventory Reserved':
            inventory_detail = event_detail['detail']
            
            if inventory_detail['status'] == 'reserved':
                # Process payment
                payment_result = process_payment_for_order(inventory_detail['order_id'])
                
                # Publish payment processed event
                payment_event = {
                    'order_id': inventory_detail['order_id'],
                    'payment_id': payment_result['payment_id'],
                    'amount': payment_result['amount'],
                    'status': payment_result['status'],
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                router.publish_event(
                    source='ecommerce.payments',
                    detail_type='Payment Processed',
                    detail=payment_event
                )

def notification_service_handler(event, context):
    """Notification service event handler"""
    
    # Handle multiple event types
    for record in event['Records']:
        event_detail = json.loads(record['body'])
        detail_type = event_detail['detail-type']
        detail = event_detail['detail']
        
        if detail_type == 'Order Created':
            send_order_confirmation(detail)
        elif detail_type == 'Payment Processed':
            send_payment_notification(detail)
        elif detail_type == 'Inventory Reserved':
            if detail['status'] == 'failed':
                send_out_of_stock_notification(detail)

def reserve_inventory_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Reserve inventory items"""
    # Simulate inventory reservation
    return {
        'success': True,
        'reservations': [{'product_id': item['product_id'], 'quantity': item['quantity']} for item in items]
    }

def process_payment_for_order(order_id: str) -> Dict[str, Any]:
    """Process payment for order"""
    # Simulate payment processing
    return {
        'payment_id': f"PAY-{order_id}",
        'amount': 99.99,
        'status': 'success'
    }

def send_order_confirmation(order_detail: Dict[str, Any]):
    """Send order confirmation notification"""
    print(f"Order confirmation sent for order {order_detail['order_id']}")

def send_payment_notification(payment_detail: Dict[str, Any]):
    """Send payment notification"""
    print(f"Payment notification sent for payment {payment_detail['payment_id']}")

def send_out_of_stock_notification(inventory_detail: Dict[str, Any]):
    """Send out of stock notification"""
    print(f"Out of stock notification sent for order {inventory_detail['order_id']}")
```

### Serverless Monitoring and Observability

**Definition:** Comprehensive monitoring strategy for serverless applications using CloudWatch, X-Ray, and custom metrics.

**Example - Serverless Observability Stack:**
```python
import boto3
import json
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from typing import Dict, Any
from datetime import datetime
import logging
import time
import functools

# Patch AWS SDK calls for X-Ray tracing
patch_all()

class ServerlessObservability:
    """Comprehensive serverless monitoring and observability"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.logs = boto3.client('logs')
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
    
    def publish_custom_metric(self, metric_name: str, value: float, 
                            unit: str = 'Count', dimensions: Dict[str, str] = None):
        """Publish custom CloudWatch metric"""
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': key, 'Value': value} for key, value in dimensions.items()
            ]
        
        self.cloudwatch.put_metric_data(
            Namespace='ServerlessApp',
            MetricData=[metric_data]
        )
    
    def create_dashboard(self, dashboard_name: str) -> str:
        """Create CloudWatch dashboard for serverless metrics"""
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Duration", "FunctionName", "order-processor"],
                            ["...", "inventory-manager"],
                            ["...", "payment-processor"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Function Duration"
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Errors", "FunctionName", "order-processor"],
                            ["...", "inventory-manager"],
                            ["...", "payment-processor"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Function Errors"
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 12,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["ServerlessApp", "OrdersProcessed"],
                            [".", "PaymentSuccess"],
                            [".", "InventoryReservations"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Business Metrics"
                    }
                }
            ]
        }
        
        self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        return dashboard_name
    
    def create_alarms(self):
        """Create CloudWatch alarms for serverless functions"""
        
        alarms = [
            {
                'name': 'HighErrorRate',
                'metric': 'AWS/Lambda',
                'metric_name': 'Errors',
                'threshold': 5,
                'comparison': 'GreaterThanThreshold'
            },
            {
                'name': 'HighDuration',
                'metric': 'AWS/Lambda',
                'metric_name': 'Duration',
                'threshold': 10000,
                'comparison': 'GreaterThanThreshold'
            },
            {
                'name': 'HighThrottles',
                'metric': 'AWS/Lambda',
                'metric_name': 'Throttles',
                'threshold': 1,
                'comparison': 'GreaterThanOrEqualToThreshold'
            }
        ]
        
        for alarm in alarms:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm['name'],
                ComparisonOperator=alarm['comparison'],
                EvaluationPeriods=2,
                MetricName=alarm['metric_name'],
                Namespace=alarm['metric'],
                Period=300,
                Statistic='Sum',
                Threshold=alarm['threshold'],
                ActionsEnabled=True,
                AlarmActions=[
                    'arn:aws:sns:us-east-1:123456789:serverless-alerts'
                ],
                AlarmDescription=f'Alarm for {alarm["name"]}'
            )

# Monitoring decorators
def monitor_performance(func):
    """Decorator to monitor function performance"""
    
    @functools.wraps(func)
    def wrapper(event, context):
        start_time = time.time()
        observability = ServerlessObservability()
        
        try:
            # Execute function
            result = func(event, context)
            
            # Record success metrics
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            observability.publish_custom_metric(
                'FunctionExecutionTime',
                execution_time,
                'Milliseconds',
                {'FunctionName': context.function_name}
            )
            
            observability.publish_custom_metric(
                'FunctionSuccess',
                1,
                'Count',
                {'FunctionName': context.function_name}
            )
            
            return result
            
        except Exception as e:
            # Record error metrics
            observability.publish_custom_metric(
                'FunctionError',
                1,
                'Count',
                {
                    'FunctionName': context.function_name,
                    'ErrorType': type(e).__name__
                }
            )
            
            logging.error(f"Function {context.function_name} failed: {str(e)}")
            raise
    
    return wrapper

@xray_recorder.capture('lambda_handler')
@monitor_performance
def enhanced_order_processor(event, context):
    """Enhanced order processor with full observability"""
    
    # Create X-Ray subsegment for business logic
    subsegment = xray_recorder.begin_subsegment('order_validation')
    
    try:
        order_data = json.loads(event['body'])
        
        # Add metadata to X-Ray trace
        subsegment.put_metadata('order_id', order_data.get('order_id'))
        subsegment.put_metadata('customer_id', order_data.get('customer_id'))
        subsegment.put_annotation('order_total', order_data.get('total_amount', 0))
        
        # Validate order
        validation_result = validate_order_data(order_data)
        
        if not validation_result['valid']:
            subsegment.add_exception(Exception("Order validation failed"))
            raise ValueError("Invalid order data")
        
        xray_recorder.end_subsegment()
        
        # Process order with tracing
        with xray_recorder.in_subsegment('order_processing'):
            result = process_order(order_data)
        
        # Record business metrics
        observability = ServerlessObservability()
        observability.publish_custom_metric(
            'OrdersProcessed',
            1,
            'Count',
            {'OrderType': order_data.get('type', 'standard')}
        )
        
        observability.publish_custom_metric(
            'OrderValue',
            order_data.get('total_amount', 0),
            'None',
            {'Currency': order_data.get('currency', 'USD')}
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'order_id': result['order_id'],
                'status': 'processed'
            })
        }
        
    except Exception as e:
        if 'subsegment' in locals():
            subsegment.add_exception(e)
            xray_recorder.end_subsegment()
        raise

def validate_order_data(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate order data with detailed logging"""
    
    errors = []
    
    # Validation logic with structured logging
    if not order_data.get('customer_id'):
        errors.append('Missing customer_id')
        logging.warning('Order validation failed: Missing customer_id', extra={
            'order_id': order_data.get('order_id'),
            'validation_error': 'missing_customer_id'
        })
    
    if not order_data.get('items'):
        errors.append('Missing items')
        logging.warning('Order validation failed: Missing items', extra={
            'order_id': order_data.get('order_id'),
            'validation_error': 'missing_items'
        })
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def process_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process order with distributed tracing"""
    
    # Simulate order processing
    order_id = order_data.get('order_id', 'unknown')
    
    logging.info('Processing order', extra={
        'order_id': order_id,
        'customer_id': order_data.get('customer_id'),
        'item_count': len(order_data.get('items', [])),
        'total_amount': order_data.get('total_amount')
    })
    
    return {
        'order_id': order_id,
        'status': 'processed',
        'timestamp': datetime.utcnow().isoformat()
    }
```

### Cost Optimization Strategies

**Definition:** Techniques to optimize serverless costs through efficient resource allocation, function optimization, and usage monitoring.

**Example - Serverless Cost Optimization:**
```python
import boto3
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

class ServerlessCostOptimizer:
    """Serverless cost optimization and analysis"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.lambda_client = boto3.client('lambda')
        self.pricing = boto3.client('pricing', region_name='us-east-1')
    
    def analyze_function_costs(self, function_names: List[str], days: int = 30) -> Dict[str, Any]:
        """Analyze Lambda function costs and usage patterns"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        cost_analysis = {}
        
        for function_name in function_names:
            # Get function configuration
            function_config = self.lambda_client.get_function_configuration(
                FunctionName=function_name
            )
            
            memory_size = function_config['MemorySize']
            
            # Get CloudWatch metrics
            metrics = self._get_function_metrics(function_name, start_time, end_time)
            
            # Calculate costs
            total_duration_ms = sum(metrics['duration'])
            total_invocations = len(metrics['duration'])
            
            # AWS Lambda pricing (as of 2024)
            request_cost = total_invocations * 0.0000002  # $0.20 per 1M requests
            
            # Duration cost calculation
            gb_seconds = (memory_size / 1024) * (total_duration_ms / 1000)
            duration_cost = gb_seconds * 0.0000166667  # $16.67 per 1M GB-seconds
            
            total_cost = request_cost + duration_cost
            
            cost_analysis[function_name] = {
                'memory_size': memory_size,
                'total_invocations': total_invocations,
                'total_duration_ms': total_duration_ms,
                'avg_duration_ms': total_duration_ms / total_invocations if total_invocations > 0 else 0,
                'request_cost': request_cost,
                'duration_cost': duration_cost,
                'total_cost': total_cost,
                'cost_per_invocation': total_cost / total_invocations if total_invocations > 0 else 0
            }
        
        return cost_analysis
    
    def _get_function_metrics(self, function_name: str, start_time: datetime, end_time: datetime) -> Dict[str, List]:
        """Get CloudWatch metrics for function"""
        
        # Get duration metrics
        duration_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Duration',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour
            Statistics=['Average', 'Sum']
        )
        
        # Get invocation metrics
        invocation_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        return {
            'duration': [dp['Average'] for dp in duration_response['Datapoints']],
            'invocations': [dp['Sum'] for dp in invocation_response['Datapoints']]
        }
    
    def optimize_memory_allocation(self, function_name: str) -> Dict[str, Any]:
        """Optimize Lambda function memory allocation"""
        
        # Get current configuration
        current_config = self.lambda_client.get_function_configuration(
            FunctionName=function_name
        )
        
        current_memory = current_config['MemorySize']
        
        # Test different memory configurations
        memory_options = [128, 256, 512, 1024, 1536, 2048, 3008]
        optimization_results = []
        
        for memory_size in memory_options:
            if memory_size == current_memory:
                continue
            
            # Calculate estimated cost with different memory
            estimated_cost = self._estimate_cost_with_memory(function_name, memory_size)
            
            optimization_results.append({
                'memory_size': memory_size,
                'estimated_monthly_cost': estimated_cost,
                'cost_difference': estimated_cost - self._estimate_cost_with_memory(function_name, current_memory)
            })
        
        # Find optimal memory configuration
        optimal_config = min(optimization_results, key=lambda x: x['estimated_monthly_cost'])
        
        return {
            'current_memory': current_memory,
            'recommended_memory': optimal_config['memory_size'],
            'estimated_savings': -optimal_config['cost_difference'],
            'all_options': optimization_results
        }
    
    def _estimate_cost_with_memory(self, function_name: str, memory_size: int) -> float:
        """Estimate monthly cost with given memory configuration"""
        
        # Get historical metrics (simplified estimation)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        metrics = self._get_function_metrics(function_name, start_time, end_time)
        avg_duration = sum(metrics['duration']) / len(metrics['duration']) if metrics['duration'] else 100
        avg_invocations_per_hour = sum(metrics['invocations']) / len(metrics['invocations']) if metrics['invocations'] else 10
        
        # Estimate for 30 days
        monthly_invocations = avg_invocations_per_hour * 24 * 30
        monthly_duration_ms = monthly_invocations * avg_duration
        
        # Calculate costs
        request_cost = monthly_invocations * 0.0000002
        gb_seconds = (memory_size / 1024) * (monthly_duration_ms / 1000)
        duration_cost = gb_seconds * 0.0000166667
        
        return request_cost + duration_cost
    
    def identify_unused_functions(self, days: int = 30) -> List[str]:
        """Identify Lambda functions with no recent invocations"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # List all functions
        functions_response = self.lambda_client.list_functions()
        all_functions = [f['FunctionName'] for f in functions_response['Functions']]
        
        unused_functions = []
        
        for function_name in all_functions:
            # Check for recent invocations
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # 1 day
                    Statistics=['Sum']
                )
                
                total_invocations = sum(dp['Sum'] for dp in response['Datapoints'])
                
                if total_invocations == 0:
                    unused_functions.append(function_name)
                    
            except Exception as e:
                print(f"Error checking function {function_name}: {e}")
        
        return unused_functions
    
    def generate_cost_report(self, function_names: List[str]) -> str:
        """Generate comprehensive cost optimization report"""
        
        cost_analysis = self.analyze_function_costs(function_names)
        unused_functions = self.identify_unused_functions()
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'total_functions_analyzed': len(function_names),
            'cost_analysis': cost_analysis,
            'unused_functions': unused_functions,
            'optimization_recommendations': []
        }
        
        # Generate recommendations
        total_cost = sum(analysis['total_cost'] for analysis in cost_analysis.values())
        
        for function_name, analysis in cost_analysis.items():
            if analysis['avg_duration_ms'] > 5000:  # Long running functions
                report['optimization_recommendations'].append({
                    'function': function_name,
                    'type': 'performance',
                    'recommendation': 'Consider breaking down long-running function or optimizing code',
                    'current_avg_duration': analysis['avg_duration_ms']
                })
            
            if analysis['cost_per_invocation'] > 0.001:  # High cost per invocation
                report['optimization_recommendations'].append({
                    'function': function_name,
                    'type': 'cost',
                    'recommendation': 'High cost per invocation - consider memory optimization',
                    'current_cost_per_invocation': analysis['cost_per_invocation']
                })
        
        if unused_functions:
            report['optimization_recommendations'].append({
                'type': 'cleanup',
                'recommendation': f'Consider removing {len(unused_functions)} unused functions',
                'unused_functions': unused_functions
            })
        
        report['summary'] = {
            'total_monthly_cost_estimate': total_cost * 30,  # Scale to monthly
            'highest_cost_function': max(cost_analysis.items(), key=lambda x: x[1]['total_cost'])[0],
            'total_invocations': sum(analysis['total_invocations'] for analysis in cost_analysis.values()),
            'avg_cost_per_invocation': total_cost / sum(analysis['total_invocations'] for analysis in cost_analysis.values()) if sum(analysis['total_invocations'] for analysis in cost_analysis.values()) > 0 else 0
        }
        
        return json.dumps(report, indent=2)

# Cost optimization Lambda function
def cost_optimizer_function(event, context):
    """Automated cost optimization function"""
    
    optimizer = ServerlessCostOptimizer()
    
    # Get list of functions to analyze
    function_names = event.get('function_names', [])
    
    if not function_names:
        # Get all functions if none specified
        functions_response = boto3.client('lambda').list_functions()
        function_names = [f['FunctionName'] for f in functions_response['Functions']]
    
    # Generate cost report
    report = optimizer.generate_cost_report(function_names)
    
    # Save report to S3
    s3 = boto3.client('s3')
    timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    
    s3.put_object(
        Bucket='serverless-cost-reports',
        Key=f'cost-optimization-report-{timestamp}.json',
        Body=report,
        ContentType='application/json'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Cost optimization report generated',
            'report_location': f's3://serverless-cost-reports/cost-optimization-report-{timestamp}.json'
        })
    }
```

This comprehensive serverless architecture documentation provides production-ready implementations covering advanced patterns like Step Functions orchestration, EventBridge routing, monitoring and observability, and cost optimization. Each pattern includes detailed examples with error handling, best practices, and real-world implementation scenarios for building scalable serverless applications.