# Serverless Security and Monitoring

**Serverless Security and Monitoring** encompasses comprehensive strategies for securing serverless applications, implementing robust monitoring and observability, managing secrets and access controls, and ensuring compliance while maintaining the scalability and cost benefits of serverless architectures.

## Serverless Security Framework

### Identity and Access Management

#### AWS IAM Best Practices for Serverless
```yaml
serverless_iam_security:
  function_level_permissions: |
    # serverless.yml - Principle of Least Privilege
    service: secure-serverless-app

    provider:
      name: aws
      runtime: python3.9
      region: us-east-1

    functions:
      getUserData:
        handler: src/handlers/users.get_user
        iamRoleStatements:
          - Effect: Allow
            Action:
              - dynamodb:GetItem
            Resource:
              - "arn:aws:dynamodb:${self:provider.region}:*:table/users"
          - Effect: Allow
            Action:
              - logs:CreateLogGroup
              - logs:CreateLogStream
              - logs:PutLogEvents
            Resource:
              - "arn:aws:logs:${self:provider.region}:*:*"

      createUser:
        handler: src/handlers/users.create_user
        iamRoleStatements:
          - Effect: Allow
            Action:
              - dynamodb:PutItem
            Resource:
              - "arn:aws:dynamodb:${self:provider.region}:*:table/users"
          - Effect: Allow
            Action:
              - secretsmanager:GetSecretValue
            Resource:
              - "arn:aws:secretsmanager:${self:provider.region}:*:secret:${self:service}/*"
          - Effect: Allow
            Action:
              - kms:Decrypt
            Resource:
              - "arn:aws:kms:${self:provider.region}:*:key/*"
            Condition:
              StringEquals:
                'kms:ViaService': 'secretsmanager.${self:provider.region}.amazonaws.com'

      processPayment:
        handler: src/handlers/payments.process_payment
        iamRoleStatements:
          - Effect: Allow
            Action:
              - dynamodb:UpdateItem
              - dynamodb:GetItem
            Resource:
              - "arn:aws:dynamodb:${self:provider.region}:*:table/orders"
              - "arn:aws:dynamodb:${self:provider.region}:*:table/payments"
          - Effect: Allow
            Action:
              - sqs:SendMessage
            Resource:
              - "arn:aws:sqs:${self:provider.region}:*:payment-processing-queue"
          - Effect: Allow
            Action:
              - secretsmanager:GetSecretValue
            Resource:
              - "arn:aws:secretsmanager:${self:provider.region}:*:secret:payment-gateway/*"

  resource_based_policies: |
    # DynamoDB Resource Policy
    Resources:
      UsersTable:
        Type: AWS::DynamoDB::Table
        Properties:
          TableName: users
          AttributeDefinitions:
            - AttributeName: user_id
              AttributeType: S
          KeySchema:
            - AttributeName: user_id
              KeyType: HASH
          BillingMode: PAY_PER_REQUEST
          PointInTimeRecoverySpecification:
            PointInTimeRecoveryEnabled: true
          SSESpecification:
            SSEEnabled: true
            KMSMasterKeyId: !Ref TableEncryptionKey
          Tags:
            - Key: DataClassification
              Value: PII
            - Key: Environment
              Value: ${self:provider.stage}

      TableEncryptionKey:
        Type: AWS::KMS::Key
        Properties:
          Description: KMS Key for DynamoDB encryption
          KeyPolicy:
            Statement:
              - Effect: Allow
                Principal:
                  AWS: !Sub "arn:aws:iam::${AWS::AccountId}:root"
                Action: "kms:*"
                Resource: "*"
              - Effect: Allow
                Principal:
                  Service: dynamodb.amazonaws.com
                Action:
                  - kms:Decrypt
                  - kms:DescribeKey
                Resource: "*"

  cross_account_access: |
    # Cross-Account Access for Multi-Environment Setup
    CrossAccountRole:
      Type: AWS::IAM::Role
      Properties:
        RoleName: ServerlessCrossAccountRole
        AssumeRolePolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Principal:
                AWS:
                  - "arn:aws:iam::PROD-ACCOUNT:role/ServerlessExecutionRole"
                  - "arn:aws:iam::STAGING-ACCOUNT:role/ServerlessExecutionRole"
              Action: sts:AssumeRole
              Condition:
                StringEquals:
                  'sts:ExternalId': '${self:custom.externalId}'
                IpAddress:
                  'aws:SourceIp':
                    - '10.0.0.0/8'
                    - '172.16.0.0/12'
        Policies:
          - PolicyName: CrossAccountDataAccess
            PolicyDocument:
              Version: '2012-10-17'
              Statement:
                - Effect: Allow
                  Action:
                    - dynamodb:GetItem
                    - dynamodb:Query
                    - dynamodb:Scan
                  Resource:
                    - "arn:aws:dynamodb:*:*:table/shared-*"
                - Effect: Allow
                  Action:
                    - s3:GetObject
                  Resource:
                    - "arn:aws:s3:::shared-assets/*"
```

### Secrets Management and Encryption

#### AWS Secrets Manager Integration
```python
#!/usr/bin/env python3
"""
Secure Secrets Management for Serverless Applications
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from functools import lru_cache
import os

class SecureSecretsManager:
    def __init__(self, region_name: str = None):
        self.region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        self.secrets_client = boto3.client('secretsmanager', region_name=self.region_name)
        self.kms_client = boto3.client('kms', region_name=self.region_name)
        self.logger = logging.getLogger(__name__)

    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager with caching
        """
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            self.logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise e

    def get_database_credentials(self, environment: str) -> Dict[str, str]:
        """Get database credentials for specific environment"""
        secret_name = f"serverless-app/{environment}/database"
        return self.get_secret(secret_name)

    def get_api_keys(self, service_name: str) -> Dict[str, str]:
        """Get API keys for external services"""
        secret_name = f"serverless-app/api-keys/{service_name}"
        return self.get_secret(secret_name)

    def rotate_secret(self, secret_name: str) -> bool:
        """Trigger secret rotation"""
        try:
            response = self.secrets_client.rotate_secret(
                SecretId=secret_name,
                ForceRotateSecrets=True
            )
            self.logger.info(f"Secret rotation initiated for {secret_name}")
            return True
        except ClientError as e:
            self.logger.error(f"Failed to rotate secret {secret_name}: {e}")
            return False

    def encrypt_sensitive_data(self, data: str, key_id: str) -> str:
        """Encrypt sensitive data using KMS"""
        try:
            response = self.kms_client.encrypt(
                KeyId=key_id,
                Plaintext=data.encode('utf-8')
            )
            return response['CiphertextBlob']
        except ClientError as e:
            self.logger.error(f"Failed to encrypt data: {e}")
            raise e

    def decrypt_sensitive_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data using KMS"""
        try:
            response = self.kms_client.decrypt(CiphertextBlob=encrypted_data)
            return response['Plaintext'].decode('utf-8')
        except ClientError as e:
            self.logger.error(f"Failed to decrypt data: {e}")
            raise e

# Lambda function with secure secrets usage
secrets_manager = SecureSecretsManager()

def secure_lambda_handler(event, context):
    """
    Example Lambda function with secure secrets management
    """
    try:
        # Get database credentials
        db_creds = secrets_manager.get_database_credentials(
            environment=os.environ.get('STAGE', 'dev')
        )

        # Get third-party API keys
        payment_api_keys = secrets_manager.get_api_keys('payment-gateway')

        # Connect to database securely
        connection = create_secure_database_connection(db_creds)

        # Process request with encrypted sensitive data
        result = process_secure_request(event, payment_api_keys)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block'
            },
            'body': json.dumps(result)
        }

    except Exception as e:
        logging.error(f"Error in secure handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def create_secure_database_connection(credentials: Dict[str, str]):
    """Create encrypted database connection"""
    import pymysql

    return pymysql.connect(
        host=credentials['host'],
        port=int(credentials['port']),
        user=credentials['username'],
        password=credentials['password'],
        database=credentials['dbname'],
        ssl_disabled=False,
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30
    )

# Environment-specific secrets configuration
secrets_config = {
    'dev': {
        'database': 'serverless-app/dev/database',
        'api_keys': 'serverless-app/dev/api-keys',
        'encryption_key': 'alias/serverless-app-dev'
    },
    'staging': {
        'database': 'serverless-app/staging/database',
        'api_keys': 'serverless-app/staging/api-keys',
        'encryption_key': 'alias/serverless-app-staging'
    },
    'prod': {
        'database': 'serverless-app/prod/database',
        'api_keys': 'serverless-app/prod/api-keys',
        'encryption_key': 'alias/serverless-app-prod'
    }
}
```

### API Security and Authentication

#### JWT-based Authentication with Cognito
```python
#!/usr/bin/env python3
"""
JWT Authentication and Authorization for Serverless APIs
"""

import json
import jwt
import boto3
import requests
from typing import Dict, Any, Optional
from functools import wraps
import time
import logging

class ServerlessAuth:
    def __init__(self, user_pool_id: str, client_id: str, region: str):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        self.logger = logging.getLogger(__name__)

        # Get Cognito public keys for JWT verification
        self.jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        self.public_keys = self._get_public_keys()

    def _get_public_keys(self) -> Dict[str, Any]:
        """Fetch Cognito public keys for JWT verification"""
        try:
            response = requests.get(self.jwks_url)
            jwks = response.json()
            return {key['kid']: key for key in jwks['keys']}
        except Exception as e:
            self.logger.error(f"Failed to fetch JWKS: {e}")
            return {}

    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return claims"""
        try:
            # Decode token header to get key ID
            header = jwt.get_unverified_header(token)
            kid = header['kid']

            if kid not in self.public_keys:
                raise ValueError("Invalid token key ID")

            # Get the public key
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(self.public_keys[kid])

            # Verify and decode the token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Get user permissions from Cognito user attributes"""
        try:
            response = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=user_id
            )

            # Extract permissions from user attributes
            permissions = {}
            for attr in response['UserAttributes']:
                if attr['Name'].startswith('custom:permission_'):
                    permission_type = attr['Name'].replace('custom:permission_', '')
                    permissions[permission_type] = attr['Value'] == 'true'

            return permissions

        except Exception as e:
            self.logger.error(f"Failed to get user permissions: {e}")
            return {}

def require_auth(permissions: list = None):
    """Decorator for requiring authentication and optional permissions"""
    def decorator(func):
        @wraps(func)
        def wrapper(event, context):
            try:
                # Extract token from Authorization header
                auth_header = event.get('headers', {}).get('Authorization', '')
                if not auth_header.startswith('Bearer '):
                    return {
                        'statusCode': 401,
                        'body': json.dumps({'error': 'Missing or invalid authorization header'})
                    }

                token = auth_header.split(' ')[1]

                # Initialize auth handler
                auth = ServerlessAuth(
                    user_pool_id=os.environ['COGNITO_USER_POOL_ID'],
                    client_id=os.environ['COGNITO_CLIENT_ID'],
                    region=os.environ['AWS_REGION']
                )

                # Verify token
                claims = auth.verify_jwt_token(token)
                user_id = claims['sub']

                # Check permissions if required
                if permissions:
                    user_permissions = auth.get_user_permissions(user_id)
                    for required_permission in permissions:
                        if not user_permissions.get(required_permission, False):
                            return {
                                'statusCode': 403,
                                'body': json.dumps({'error': f'Missing permission: {required_permission}'})
                            }

                # Add user context to event
                event['user_context'] = {
                    'user_id': user_id,
                    'email': claims.get('email'),
                    'permissions': user_permissions if permissions else None
                }

                # Call the original function
                return func(event, context)

            except ValueError as e:
                return {
                    'statusCode': 401,
                    'body': json.dumps({'error': str(e)})
                }
            except Exception as e:
                logging.error(f"Authentication error: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Authentication service error'})
                }

        return wrapper
    return decorator

# Example usage
@require_auth(permissions=['read_orders', 'manage_inventory'])
def get_sensitive_data(event, context):
    """Example function requiring authentication and specific permissions"""
    user_context = event['user_context']

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Access granted',
            'user_id': user_context['user_id'],
            'data': 'sensitive information'
        })
    }

# API Key validation for service-to-service communication
def validate_api_key(event, context):
    """Lambda authorizer for API key validation"""
    try:
        api_key = event.get('headers', {}).get('X-API-Key', '')

        if not api_key:
            return generate_policy('Deny', event['methodArn'])

        # Validate API key against DynamoDB or Secrets Manager
        if validate_api_key_in_store(api_key):
            return generate_policy('Allow', event['methodArn'], api_key)
        else:
            return generate_policy('Deny', event['methodArn'])

    except Exception as e:
        logging.error(f"API key validation error: {str(e)}")
        return generate_policy('Deny', event['methodArn'])

def generate_policy(effect: str, resource: str, principal_id: str = 'user') -> Dict[str, Any]:
    """Generate IAM policy for API Gateway"""
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        },
        'context': {
            'api_key': principal_id if effect == 'Allow' else None
        }
    }

def validate_api_key_in_store(api_key: str) -> bool:
    """Validate API key against secure storage"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('api-keys')

        response = table.get_item(Key={'api_key': api_key})

        if 'Item' in response:
            item = response['Item']
            # Check if key is active and not expired
            return (
                item.get('status') == 'active' and
                item.get('expires_at', float('inf')) > time.time()
            )

        return False

    except Exception as e:
        logging.error(f"API key validation error: {str(e)}")
        return False
```

## Comprehensive Monitoring and Observability

### CloudWatch Enhanced Monitoring

#### Advanced CloudWatch Configuration
```yaml
cloudwatch_monitoring:
  custom_metrics: |
    # Custom CloudWatch Metrics for Serverless
    service: serverless-monitoring

    provider:
      name: aws
      runtime: python3.9
      environment:
        METRICS_NAMESPACE: ServerlessApp/${self:provider.stage}

    functions:
      businessMetrics:
        handler: src/metrics/business_metrics.handler
        events:
          - schedule: rate(1 minute)
        environment:
          METRIC_FILTERS:
            - order_completion_rate
            - user_registration_rate
            - payment_success_rate

      alertProcessor:
        handler: src/alerts/alert_processor.handler
        events:
          - cloudwatchEvent:
              event:
                source: ["aws.cloudwatch"]
                detail-type: ["CloudWatch Alarm State Change"]
        environment:
          SLACK_WEBHOOK_URL: ${ssm:/serverless-app/slack-webhook}
          PAGERDUTY_API_KEY: ${ssm:/serverless-app/pagerduty-key}

    resources:
      Resources:
        # Custom Dashboard
        ServerlessAppDashboard:
          Type: AWS::CloudWatch::Dashboard
          Properties:
            DashboardName: ServerlessApp-${self:provider.stage}
            DashboardBody: !Sub |
              {
                "widgets": [
                  {
                    "type": "metric",
                    "x": 0, "y": 0, "width": 12, "height": 6,
                    "properties": {
                      "metrics": [
                        ["AWS/Lambda", "Duration", "FunctionName", "${self:service}-${self:provider.stage}-createOrder"],
                        ["AWS/Lambda", "Errors", "FunctionName", "${self:service}-${self:provider.stage}-createOrder"],
                        ["AWS/Lambda", "Invocations", "FunctionName", "${self:service}-${self:provider.stage}-createOrder"]
                      ],
                      "period": 300,
                      "stat": "Average",
                      "region": "${self:provider.region}",
                      "title": "Lambda Performance Metrics"
                    }
                  },
                  {
                    "type": "log",
                    "x": 0, "y": 6, "width": 24, "height": 6,
                    "properties": {
                      "query": "SOURCE '/aws/lambda/${self:service}-${self:provider.stage}-createOrder'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
                      "region": "${self:provider.region}",
                      "title": "Recent Errors",
                      "view": "table"
                    }
                  }
                ]
              }

        # Business Logic Alarms
        OrderCompletionRateAlarm:
          Type: AWS::CloudWatch::Alarm
          Properties:
            AlarmName: Low-Order-Completion-Rate-${self:provider.stage}
            AlarmDescription: Alert when order completion rate drops below 90%
            MetricName: OrderCompletionRate
            Namespace: ${self:provider.environment.METRICS_NAMESPACE}
            Statistic: Average
            Period: 300
            EvaluationPeriods: 2
            Threshold: 90
            ComparisonOperator: LessThanThreshold
            AlarmActions:
              - !Ref BusinessAlertsSnsTopic
            TreatMissingData: breaching

        HighLatencyAlarm:
          Type: AWS::CloudWatch::Alarm
          Properties:
            AlarmName: High-Lambda-Latency-${self:provider.stage}
            AlarmDescription: Alert when Lambda duration exceeds 5 seconds
            MetricName: Duration
            Namespace: AWS/Lambda
            Dimensions:
              - Name: FunctionName
                Value: ${self:service}-${self:provider.stage}-createOrder
            Statistic: Average
            Period: 300
            EvaluationPeriods: 3
            Threshold: 5000
            ComparisonOperator: GreaterThanThreshold
            AlarmActions:
              - !Ref PerformanceAlertsSnsTopic

        BusinessAlertsSnsTopic:
          Type: AWS::SNS::Topic
          Properties:
            TopicName: business-alerts-${self:provider.stage}
            DisplayName: Business Alerts

        PerformanceAlertsSnsTopic:
          Type: AWS::SNS::Topic
          Properties:
            TopicName: performance-alerts-${self:provider.stage}
            DisplayName: Performance Alerts

  metrics_implementation: |
    # src/metrics/business_metrics.py
    import boto3
    import json
    import os
    from datetime import datetime, timedelta
    from typing import Dict, List

    cloudwatch = boto3.client('cloudwatch')
    dynamodb = boto3.resource('dynamodb')

    def handler(event, context):
        """Collect and publish business metrics"""
        try:
            metrics = collect_business_metrics()
            publish_metrics_to_cloudwatch(metrics)

            return {
                'statusCode': 200,
                'body': json.dumps({'metrics_published': len(metrics)})
            }
        except Exception as e:
            print(f"Error collecting metrics: {str(e)}")
            raise

    def collect_business_metrics() -> List[Dict]:
        """Collect business metrics from various sources"""
        metrics = []

        # Order completion rate
        order_metrics = calculate_order_completion_rate()
        metrics.extend(order_metrics)

        # User registration rate
        user_metrics = calculate_user_registration_rate()
        metrics.extend(user_metrics)

        # Payment success rate
        payment_metrics = calculate_payment_success_rate()
        metrics.extend(payment_metrics)

        return metrics

    def calculate_order_completion_rate() -> List[Dict]:
        """Calculate order completion rate from DynamoDB"""
        try:
            orders_table = dynamodb.Table('orders')

            # Get orders from last hour
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)

            # Query orders in time range
            response = orders_table.scan(
                FilterExpression='created_at BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':start': start_time.isoformat(),
                    ':end': end_time.isoformat()
                }
            )

            orders = response['Items']
            total_orders = len(orders)
            completed_orders = len([o for o in orders if o.get('status') == 'completed'])

            completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

            return [{
                'MetricName': 'OrderCompletionRate',
                'Value': completion_rate,
                'Unit': 'Percent',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': os.environ.get('STAGE', 'dev')}
                ]
            }, {
                'MetricName': 'TotalOrders',
                'Value': total_orders,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Environment', 'Value': os.environ.get('STAGE', 'dev')}
                ]
            }]

        except Exception as e:
            print(f"Error calculating order completion rate: {str(e)}")
            return []

    def publish_metrics_to_cloudwatch(metrics: List[Dict]):
        """Publish custom metrics to CloudWatch"""
        if not metrics:
            return

        namespace = os.environ['METRICS_NAMESPACE']

        # CloudWatch accepts max 20 metrics per put_metric_data call
        for i in range(0, len(metrics), 20):
            batch = metrics[i:i+20]

            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[{
                    'MetricName': metric['MetricName'],
                    'Value': metric['Value'],
                    'Unit': metric.get('Unit', 'None'),
                    'Dimensions': metric.get('Dimensions', []),
                    'Timestamp': datetime.utcnow()
                } for metric in batch]
            )

  log_analysis: |
    # CloudWatch Logs Insights Queries
    queries:
      error_analysis: |
        fields @timestamp, @message, @requestId
        | filter @message like /ERROR/
        | stats count() by bin(5m)
        | sort @timestamp desc

      performance_analysis: |
        fields @timestamp, @duration, @requestId
        | filter @type = "REPORT"
        | stats avg(@duration), max(@duration), min(@duration) by bin(5m)
        | sort @timestamp desc

      business_events: |
        fields @timestamp, @message
        | filter @message like /order_completed/ or @message like /payment_processed/
        | parse @message "event=* user_id=* amount=*"
        | stats count() by event, bin(1h)
        | sort @timestamp desc

      cold_start_analysis: |
        fields @timestamp, @duration, @initDuration
        | filter @type = "REPORT"
        | filter ispresent(@initDuration)
        | stats count() as cold_starts, avg(@initDuration) as avg_init_duration by bin(1h)
        | sort @timestamp desc
```

### Distributed Tracing with X-Ray

#### AWS X-Ray Implementation
```python
#!/usr/bin/env python3
"""
AWS X-Ray Distributed Tracing for Serverless Applications
"""

import json
import boto3
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
import requests
import time
from typing import Dict, Any

# Patch AWS SDK and other libraries for automatic tracing
patch_all()

# Initialize X-Ray recorder
xray_recorder.configure(
    context_missing='LOG_ERROR',
    plugins=('EC2Plugin', 'ECSPlugin'),
    daemon_address='127.0.0.1:2000',
    dynamic_naming='*.amazonaws.com'
)

class ServerlessTracing:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.s3_client = boto3.client('s3')
        self.sns_client = boto3.client('sns')

    @xray_recorder.capture('process_order')
    def process_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process order with comprehensive tracing"""

        # Add custom metadata to trace
        xray_recorder.put_metadata('order_data', {
            'order_id': order_data.get('order_id'),
            'customer_id': order_data.get('customer_id'),
            'total_amount': order_data.get('total_amount')
        })

        # Add custom annotation for filtering
        xray_recorder.put_annotation('order_type', order_data.get('type', 'standard'))
        xray_recorder.put_annotation('customer_tier', order_data.get('customer_tier', 'standard'))

        try:
            # Validate order
            validation_result = self.validate_order(order_data)
            if not validation_result['valid']:
                xray_recorder.put_annotation('validation_failed', True)
                raise ValueError(f"Order validation failed: {validation_result['errors']}")

            # Check inventory
            inventory_result = self.check_inventory(order_data['items'])
            if not inventory_result['available']:
                xray_recorder.put_annotation('inventory_insufficient', True)
                raise ValueError("Insufficient inventory")

            # Process payment
            payment_result = self.process_payment(order_data)
            if not payment_result['success']:
                xray_recorder.put_annotation('payment_failed', True)
                raise ValueError("Payment processing failed")

            # Save order
            saved_order = self.save_order(order_data, payment_result)

            # Send notifications
            self.send_order_notifications(saved_order)

            xray_recorder.put_annotation('order_processed', True)
            return {
                'success': True,
                'order_id': saved_order['order_id'],
                'total_amount': saved_order['total_amount']
            }

        except Exception as e:
            xray_recorder.put_annotation('error_occurred', True)
            xray_recorder.put_metadata('error_details', {
                'error_type': type(e).__name__,
                'error_message': str(e)
            })
            raise

    @xray_recorder.capture('validate_order')
    def validate_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order data"""
        subsegment = xray_recorder.current_subsegment()
        subsegment.put_annotation('validation_type', 'order_data')

        errors = []

        # Simulate validation logic
        if not order_data.get('customer_id'):
            errors.append('Customer ID is required')

        if not order_data.get('items'):
            errors.append('Order must contain items')

        # Add custom timing
        start_time = time.time()
        # ... validation logic ...
        validation_time = time.time() - start_time

        subsegment.put_metadata('validation_metrics', {
            'validation_time_ms': validation_time * 1000,
            'rules_checked': 5,
            'errors_found': len(errors)
        })

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    @xray_recorder.capture('check_inventory')
    def check_inventory(self, items: list) -> Dict[str, Any]:
        """Check inventory availability"""
        subsegment = xray_recorder.current_subsegment()
        subsegment.put_annotation('inventory_check', True)

        inventory_table = self.dynamodb.Table('inventory')

        available_items = []
        unavailable_items = []

        for item in items:
            try:
                response = inventory_table.get_item(
                    Key={'product_id': item['product_id']}
                )

                if 'Item' in response:
                    current_stock = response['Item']['quantity']
                    requested_qty = item['quantity']

                    if current_stock >= requested_qty:
                        available_items.append(item)
                    else:
                        unavailable_items.append({
                            **item,
                            'available_stock': current_stock
                        })
                else:
                    unavailable_items.append({
                        **item,
                        'error': 'Product not found'
                    })

            except Exception as e:
                subsegment.add_exception(e)
                unavailable_items.append({
                    **item,
                    'error': str(e)
                })

        subsegment.put_metadata('inventory_check_results', {
            'total_items': len(items),
            'available_items': len(available_items),
            'unavailable_items': len(unavailable_items)
        })

        return {
            'available': len(unavailable_items) == 0,
            'available_items': available_items,
            'unavailable_items': unavailable_items
        }

    @xray_recorder.capture('process_payment')
    def process_payment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment with external service tracing"""
        subsegment = xray_recorder.current_subsegment()
        subsegment.put_annotation('payment_provider', 'stripe')
        subsegment.put_annotation('payment_amount', order_data['total_amount'])

        # Simulate external payment API call
        try:
            # This will be automatically traced by X-Ray
            payment_response = requests.post(
                'https://api.stripe.com/v1/payment_intents',
                headers={
                    'Authorization': 'Bearer sk_test_...',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={
                    'amount': int(order_data['total_amount'] * 100),
                    'currency': 'usd',
                    'customer': order_data['customer_id']
                },
                timeout=30
            )

            payment_response.raise_for_status()
            payment_data = payment_response.json()

            subsegment.put_metadata('payment_response', {
                'payment_intent_id': payment_data.get('id'),
                'status': payment_data.get('status'),
                'amount_received': payment_data.get('amount_received')
            })

            return {
                'success': True,
                'payment_id': payment_data['id'],
                'status': payment_data['status']
            }

        except requests.RequestException as e:
            subsegment.add_exception(e)
            subsegment.put_annotation('payment_error', True)
            return {
                'success': False,
                'error': str(e)
            }

    @xray_recorder.capture('save_order')
    def save_order(self, order_data: Dict[str, Any], payment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Save order to database"""
        orders_table = self.dynamodb.Table('orders')

        order_item = {
            'order_id': order_data['order_id'],
            'customer_id': order_data['customer_id'],
            'items': order_data['items'],
            'total_amount': order_data['total_amount'],
            'payment_id': payment_result['payment_id'],
            'status': 'confirmed',
            'created_at': int(time.time())
        }

        orders_table.put_item(Item=order_item)

        return order_item

    @xray_recorder.capture('send_notifications')
    def send_order_notifications(self, order: Dict[str, Any]):
        """Send order confirmation notifications"""
        subsegment = xray_recorder.current_subsegment()

        # Send SNS notification
        message = {
            'order_id': order['order_id'],
            'customer_id': order['customer_id'],
            'total_amount': order['total_amount'],
            'event_type': 'order_confirmed'
        }

        self.sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:ACCOUNT:order-notifications',
            Message=json.dumps(message),
            Subject='Order Confirmation'
        )

        subsegment.put_annotation('notification_sent', True)

# Lambda handler with X-Ray tracing
@xray_recorder.capture('lambda_handler')
def lambda_handler(event, context):
    """Main Lambda handler with tracing"""

    # Add request information to trace
    xray_recorder.put_annotation('request_id', context.aws_request_id)
    xray_recorder.put_annotation('function_name', context.function_name)
    xray_recorder.put_metadata('request_info', {
        'remaining_time_ms': context.get_remaining_time_in_millis(),
        'memory_limit_mb': context.memory_limit_in_mb
    })

    try:
        body = json.loads(event['body']) if event.get('body') else {}

        # Initialize tracing service
        tracing_service = ServerlessTracing()

        # Process the order
        result = tracing_service.process_order(body)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Trace-Id': xray_recorder.current_segment().trace_id
            },
            'body': json.dumps(result)
        }

    except Exception as e:
        xray_recorder.current_segment().add_exception(e)

        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'trace_id': xray_recorder.current_segment().trace_id
            })
        }
```

This comprehensive Serverless Security and Monitoring document provides enterprise-grade security frameworks, secrets management, authentication patterns, and advanced monitoring and observability solutions essential for production serverless applications.