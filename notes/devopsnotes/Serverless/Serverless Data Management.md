# Serverless Data Management

**Serverless Data Management** encompasses advanced strategies for managing data persistence, implementing efficient data access patterns, handling transactions across distributed systems, and leveraging serverless-native databases and storage solutions while maintaining consistency, performance, and scalability.

## Serverless Database Patterns

### DynamoDB Advanced Patterns

#### Single Table Design Implementation
```yaml
dynamodb_single_table:
  table_structure: |
    # DynamoDB Single Table Design for E-commerce Application
    Resources:
      ApplicationTable:
        Type: AWS::DynamoDB::Table
        Properties:
          TableName: ${self:service}-data-${self:provider.stage}
          BillingMode: PAY_PER_REQUEST
          AttributeDefinitions:
            - AttributeName: PK
              AttributeType: S
            - AttributeName: SK
              AttributeType: S
            - AttributeName: GSI1PK
              AttributeType: S
            - AttributeName: GSI1SK
              AttributeType: S
            - AttributeName: GSI2PK
              AttributeType: S
            - AttributeName: GSI2SK
              AttributeType: S
            - AttributeName: LSI1SK
              AttributeType: S
          KeySchema:
            - AttributeName: PK
              KeyType: HASH
            - AttributeName: SK
              KeyType: RANGE
          GlobalSecondaryIndexes:
            - IndexName: GSI1
              KeySchema:
                - AttributeName: GSI1PK
                  KeyType: HASH
                - AttributeName: GSI1SK
                  KeyType: RANGE
              Projection:
                ProjectionType: ALL
            - IndexName: GSI2
              KeySchema:
                - AttributeName: GSI2PK
                  KeyType: HASH
                - AttributeName: GSI2SK
                  KeyType: RANGE
              Projection:
                ProjectionType: ALL
          LocalSecondaryIndexes:
            - IndexName: LSI1
              KeySchema:
                - AttributeName: PK
                  KeyType: HASH
                - AttributeName: LSI1SK
                  KeyType: RANGE
              Projection:
                ProjectionType: ALL
          StreamSpecification:
            StreamViewType: NEW_AND_OLD_IMAGES
          PointInTimeRecoverySpecification:
            PointInTimeRecoveryEnabled: true
          SSESpecification:
            SSEEnabled: true
          Tags:
            - Key: Environment
              Value: ${self:provider.stage}
            - Key: Service
              Value: ${self:service}

  data_modeling: |
    # Single Table Data Model
    entity_patterns:
      user:
        primary_key:
          PK: "USER#12345"
          SK: "USER#12345"
        attributes:
          user_id: "12345"
          email: "user@example.com"
          name: "John Doe"
          created_at: "2023-01-01T00:00:00Z"
          status: "active"
        gsi1:
          GSI1PK: "USER#EMAIL"
          GSI1SK: "user@example.com"

      user_profile:
        primary_key:
          PK: "USER#12345"
          SK: "PROFILE#12345"
        attributes:
          user_id: "12345"
          phone: "+1234567890"
          address: "123 Main St"
          preferences: {"notifications": true}

      order:
        primary_key:
          PK: "ORDER#67890"
          SK: "ORDER#67890"
        attributes:
          order_id: "67890"
          user_id: "12345"
          total_amount: 99.99
          status: "pending"
          created_at: "2023-01-15T10:30:00Z"
        gsi1:
          GSI1PK: "USER#12345"
          GSI1SK: "ORDER#2023-01-15T10:30:00Z"
        gsi2:
          GSI2PK: "ORDER#STATUS#pending"
          GSI2SK: "2023-01-15T10:30:00Z"

      order_item:
        primary_key:
          PK: "ORDER#67890"
          SK: "ITEM#1"
        attributes:
          order_id: "67890"
          item_id: "1"
          product_id: "PROD123"
          quantity: 2
          price: 49.99

      product:
        primary_key:
          PK: "PRODUCT#PROD123"
          SK: "PRODUCT#PROD123"
        attributes:
          product_id: "PROD123"
          name: "Amazing Product"
          description: "Product description"
          price: 49.99
          category: "electronics"
          stock: 100
        gsi1:
          GSI1PK: "CATEGORY#electronics"
          GSI1SK: "PRODUCT#PROD123"

      product_review:
        primary_key:
          PK: "PRODUCT#PROD123"
          SK: "REVIEW#USER#12345"
        attributes:
          product_id: "PROD123"
          user_id: "12345"
          rating: 5
          comment: "Great product!"
          created_at: "2023-01-20T15:00:00Z"
        gsi1:
          GSI1PK: "USER#12345"
          GSI1SK: "REVIEW#2023-01-20T15:00:00Z"

  implementation: |
    # Python DynamoDB Single Table Implementation
    import boto3
    import json
    import uuid
    from datetime import datetime, timezone
    from typing import Dict, List, Any, Optional
    from boto3.dynamodb.conditions import Key, Attr
    from botocore.exceptions import ClientError

    class DynamoDBSingleTable:
        def __init__(self, table_name: str, region: str = 'us-east-1'):
            self.dynamodb = boto3.resource('dynamodb', region_name=region)
            self.table = self.dynamodb.Table(table_name)

        # User Operations
        def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
            """Create a new user with profile data"""
            user_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()

            user_item = {
                'PK': f'USER#{user_id}',
                'SK': f'USER#{user_id}',
                'entity_type': 'USER',
                'user_id': user_id,
                'email': user_data['email'],
                'name': user_data['name'],
                'created_at': timestamp,
                'status': 'active',
                'GSI1PK': 'USER#EMAIL',
                'GSI1SK': user_data['email']
            }

            profile_item = {
                'PK': f'USER#{user_id}',
                'SK': f'PROFILE#{user_id}',
                'entity_type': 'USER_PROFILE',
                'user_id': user_id,
                'phone': user_data.get('phone'),
                'address': user_data.get('address'),
                'preferences': user_data.get('preferences', {}),
                'updated_at': timestamp
            }

            # Transaction to ensure consistency
            try:
                with self.table.batch_writer() as batch:
                    batch.put_item(Item=user_item)
                    batch.put_item(Item=profile_item)

                return {'user_id': user_id, 'status': 'created'}

            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    raise ValueError('User with this email already exists')
                raise

        def get_user_with_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
            """Get user and profile data in a single query"""
            try:
                response = self.table.query(
                    KeyConditionExpression=Key('PK').eq(f'USER#{user_id}') &
                                         Key('SK').begins_with('USER#')
                )

                if not response['Items']:
                    return None

                user_data = {}
                for item in response['Items']:
                    if item['SK'] == f'USER#{user_id}':
                        user_data.update({
                            'user_id': item['user_id'],
                            'email': item['email'],
                            'name': item['name'],
                            'created_at': item['created_at'],
                            'status': item['status']
                        })
                    elif item['SK'] == f'PROFILE#{user_id}':
                        user_data.update({
                            'phone': item.get('phone'),
                            'address': item.get('address'),
                            'preferences': item.get('preferences', {})
                        })

                return user_data

            except ClientError as e:
                print(f"Error getting user: {e}")
                return None

        # Order Operations
        def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
            """Create order with items using transaction"""
            order_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()

            order_item = {
                'PK': f'ORDER#{order_id}',
                'SK': f'ORDER#{order_id}',
                'entity_type': 'ORDER',
                'order_id': order_id,
                'user_id': order_data['user_id'],
                'total_amount': order_data['total_amount'],
                'status': 'pending',
                'created_at': timestamp,
                'GSI1PK': f"USER#{order_data['user_id']}",
                'GSI1SK': f'ORDER#{timestamp}',
                'GSI2PK': 'ORDER#STATUS#pending',
                'GSI2SK': timestamp
            }

            # Prepare order items
            items_to_write = [order_item]
            for idx, item in enumerate(order_data['items']):
                order_item_data = {
                    'PK': f'ORDER#{order_id}',
                    'SK': f'ITEM#{idx + 1}',
                    'entity_type': 'ORDER_ITEM',
                    'order_id': order_id,
                    'item_id': str(idx + 1),
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'price': item['price']
                }
                items_to_write.append(order_item_data)

            # Write all items in a batch
            try:
                with self.table.batch_writer() as batch:
                    for item in items_to_write:
                        batch.put_item(Item=item)

                return {'order_id': order_id, 'status': 'created'}

            except ClientError as e:
                print(f"Error creating order: {e}")
                raise

        def get_order_with_items(self, order_id: str) -> Optional[Dict[str, Any]]:
            """Get complete order with all items"""
            try:
                response = self.table.query(
                    KeyConditionExpression=Key('PK').eq(f'ORDER#{order_id}')
                )

                if not response['Items']:
                    return None

                order_data = None
                items = []

                for item in response['Items']:
                    if item['entity_type'] == 'ORDER':
                        order_data = {
                            'order_id': item['order_id'],
                            'user_id': item['user_id'],
                            'total_amount': item['total_amount'],
                            'status': item['status'],
                            'created_at': item['created_at']
                        }
                    elif item['entity_type'] == 'ORDER_ITEM':
                        items.append({
                            'item_id': item['item_id'],
                            'product_id': item['product_id'],
                            'quantity': item['quantity'],
                            'price': item['price']
                        })

                if order_data:
                    order_data['items'] = items
                    return order_data

                return None

            except ClientError as e:
                print(f"Error getting order: {e}")
                return None

        def get_user_orders(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
            """Get user's orders using GSI1"""
            try:
                response = self.table.query(
                    IndexName='GSI1',
                    KeyConditionExpression=Key('GSI1PK').eq(f'USER#{user_id}') &
                                         Key('GSI1SK').begins_with('ORDER#'),
                    ScanIndexForward=False,  # Latest orders first
                    Limit=limit
                )

                orders = []
                for item in response['Items']:
                    if item['entity_type'] == 'ORDER':
                        orders.append({
                            'order_id': item['order_id'],
                            'total_amount': item['total_amount'],
                            'status': item['status'],
                            'created_at': item['created_at']
                        })

                return orders

            except ClientError as e:
                print(f"Error getting user orders: {e}")
                return []

        # Product Operations
        def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
            """Create a new product"""
            product_id = product_data.get('product_id') or str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()

            product_item = {
                'PK': f'PRODUCT#{product_id}',
                'SK': f'PRODUCT#{product_id}',
                'entity_type': 'PRODUCT',
                'product_id': product_id,
                'name': product_data['name'],
                'description': product_data['description'],
                'price': product_data['price'],
                'category': product_data['category'],
                'stock': product_data.get('stock', 0),
                'created_at': timestamp,
                'GSI1PK': f"CATEGORY#{product_data['category']}",
                'GSI1SK': f'PRODUCT#{product_id}'
            }

            try:
                self.table.put_item(Item=product_item)
                return {'product_id': product_id, 'status': 'created'}

            except ClientError as e:
                print(f"Error creating product: {e}")
                raise

        def get_products_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
            """Get products by category using GSI1"""
            try:
                response = self.table.query(
                    IndexName='GSI1',
                    KeyConditionExpression=Key('GSI1PK').eq(f'CATEGORY#{category}'),
                    Limit=limit
                )

                products = []
                for item in response['Items']:
                    if item['entity_type'] == 'PRODUCT':
                        products.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'description': item['description'],
                            'price': item['price'],
                            'stock': item['stock']
                        })

                return products

            except ClientError as e:
                print(f"Error getting products by category: {e}")
                return []

        # Advanced Query Patterns
        def get_orders_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
            """Get orders by status using GSI2"""
            try:
                response = self.table.query(
                    IndexName='GSI2',
                    KeyConditionExpression=Key('GSI2PK').eq(f'ORDER#STATUS#{status}'),
                    ScanIndexForward=False,  # Latest first
                    Limit=limit
                )

                orders = []
                for item in response['Items']:
                    orders.append({
                        'order_id': item['order_id'],
                        'user_id': item['user_id'],
                        'total_amount': item['total_amount'],
                        'status': item['status'],
                        'created_at': item['created_at']
                    })

                return orders

            except ClientError as e:
                print(f"Error getting orders by status: {e}")
                return []

        def update_order_status(self, order_id: str, new_status: str) -> bool:
            """Update order status with GSI2 update"""
            timestamp = datetime.now(timezone.utc).isoformat()

            try:
                # Get current order to update GSI2
                current_order = self.table.get_item(
                    Key={'PK': f'ORDER#{order_id}', 'SK': f'ORDER#{order_id}'}
                )

                if 'Item' not in current_order:
                    return False

                old_status = current_order['Item']['status']

                # Update with new GSI2 values
                self.table.update_item(
                    Key={'PK': f'ORDER#{order_id}', 'SK': f'ORDER#{order_id}'},
                    UpdateExpression='SET #status = :new_status, updated_at = :timestamp, GSI2PK = :gsi2pk',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':new_status': new_status,
                        ':timestamp': timestamp,
                        ':gsi2pk': f'ORDER#STATUS#{new_status}'
                    }
                )

                return True

            except ClientError as e:
                print(f"Error updating order status: {e}")
                return False

# Usage example in Lambda function
def lambda_handler(event, context):
    """Example Lambda handler using single table design"""

    db = DynamoDBSingleTable(os.environ['TABLE_NAME'])

    try:
        action = event.get('action')

        if action == 'create_user':
            result = db.create_user(event['user_data'])
            return {
                'statusCode': 201,
                'body': json.dumps(result)
            }

        elif action == 'get_user':
            user = db.get_user_with_profile(event['user_id'])
            if user:
                return {
                    'statusCode': 200,
                    'body': json.dumps(user)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'User not found'})
                }

        elif action == 'create_order':
            result = db.create_order(event['order_data'])
            return {
                'statusCode': 201,
                'body': json.dumps(result)
            }

        elif action == 'get_user_orders':
            orders = db.get_user_orders(event['user_id'])
            return {
                'statusCode': 200,
                'body': json.dumps({'orders': orders})
            }

        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid action'})
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Aurora Serverless and RDS Data API

#### Aurora Serverless V2 Implementation
```yaml
aurora_serverless:
  cluster_configuration: |
    # Aurora Serverless V2 Cluster
    Resources:
      AuroraServerlessCluster:
        Type: AWS::RDS::DBCluster
        Properties:
          DBClusterIdentifier: ${self:service}-aurora-${self:provider.stage}
          Engine: aurora-mysql
          EngineVersion: 8.0.mysql_aurora.3.02.0
          EngineMode: provisioned
          MasterUsername: admin
          MasterUserPassword: !Ref DatabasePassword
          DatabaseName: application_db
          VpcSecurityGroupIds:
            - !Ref AuroraSecurityGroup
          DBSubnetGroupName: !Ref DBSubnetGroup
          BackupRetentionPeriod: 7
          PreferredBackupWindow: "03:00-04:00"
          PreferredMaintenanceWindow: "sun:04:00-sun:05:00"
          DeletionProtection: true
          StorageEncrypted: true
          KmsKeyId: !Ref DatabaseEncryptionKey
          EnableHttpEndpoint: true  # Enable Data API
          Tags:
            - Key: Environment
              Value: ${self:provider.stage}

      AuroraServerlessInstance:
        Type: AWS::RDS::DBInstance
        Properties:
          DBInstanceIdentifier: ${self:service}-aurora-instance-${self:provider.stage}
          DBClusterIdentifier: !Ref AuroraServerlessCluster
          DBInstanceClass: db.serverless
          Engine: aurora-mysql
          PubliclyAccessible: false
          Tags:
            - Key: Environment
              Value: ${self:provider.stage}

      ServerlessV2ScalingConfiguration:
        Type: AWS::RDS::DBCluster
        Properties:
          ServerlessV2ScalingConfiguration:
            MinCapacity: 0.5  # 0.5 ACU minimum
            MaxCapacity: 16   # 16 ACU maximum
            AutoPause: true
            SecondsUntilAutoPause: 300  # 5 minutes

  data_api_implementation: |
    # Aurora Serverless Data API Implementation
    import boto3
    import json
    import uuid
    from typing import Dict, List, Any, Optional
    from datetime import datetime

    class AuroraDataAPI:
        def __init__(self, cluster_arn: str, secret_arn: str, database_name: str, region: str = 'us-east-1'):
            self.rds_data_client = boto3.client('rds-data', region_name=region)
            self.cluster_arn = cluster_arn
            self.secret_arn = secret_arn
            self.database_name = database_name

        def execute_statement(self, sql: str, parameters: List[Dict] = None) -> Dict[str, Any]:
            """Execute SQL statement using Data API"""
            try:
                request_params = {
                    'resourceArn': self.cluster_arn,
                    'secretArn': self.secret_arn,
                    'database': self.database_name,
                    'sql': sql
                }

                if parameters:
                    request_params['parameters'] = parameters

                response = self.rds_data_client.execute_statement(**request_params)
                return response

            except Exception as e:
                print(f"Error executing statement: {e}")
                raise

        def execute_transaction(self, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Execute multiple statements in a transaction"""
            try:
                # Begin transaction
                transaction_response = self.rds_data_client.begin_transaction(
                    resourceArn=self.cluster_arn,
                    secretArn=self.secret_arn,
                    database=self.database_name
                )

                transaction_id = transaction_response['transactionId']
                results = []

                try:
                    # Execute all statements in transaction
                    for statement in statements:
                        request_params = {
                            'resourceArn': self.cluster_arn,
                            'secretArn': self.secret_arn,
                            'database': self.database_name,
                            'sql': statement['sql'],
                            'transactionId': transaction_id
                        }

                        if 'parameters' in statement:
                            request_params['parameters'] = statement['parameters']

                        result = self.rds_data_client.execute_statement(**request_params)
                        results.append(result)

                    # Commit transaction
                    self.rds_data_client.commit_transaction(
                        resourceArn=self.cluster_arn,
                        secretArn=self.secret_arn,
                        transactionId=transaction_id
                    )

                    return {'success': True, 'results': results}

                except Exception as e:
                    # Rollback transaction on error
                    self.rds_data_client.rollback_transaction(
                        resourceArn=self.cluster_arn,
                        secretArn=self.secret_arn,
                        transactionId=transaction_id
                    )
                    raise e

            except Exception as e:
                print(f"Error executing transaction: {e}")
                raise

        def batch_execute_statement(self, sql: str, parameter_sets: List[List[Dict]]) -> Dict[str, Any]:
            """Execute statement with multiple parameter sets"""
            try:
                response = self.rds_data_client.batch_execute_statement(
                    resourceArn=self.cluster_arn,
                    secretArn=self.secret_arn,
                    database=self.database_name,
                    sql=sql,
                    parameterSets=parameter_sets
                )
                return response

            except Exception as e:
                print(f"Error in batch execute: {e}")
                raise

        def create_user(self, user_data: Dict[str, Any]) -> str:
            """Create user with transaction"""
            user_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()

            statements = [
                {
                    'sql': """
                        INSERT INTO users (user_id, email, name, created_at, status)
                        VALUES (:user_id, :email, :name, :created_at, :status)
                    """,
                    'parameters': [
                        {'name': 'user_id', 'value': {'stringValue': user_id}},
                        {'name': 'email', 'value': {'stringValue': user_data['email']}},
                        {'name': 'name', 'value': {'stringValue': user_data['name']}},
                        {'name': 'created_at', 'value': {'stringValue': timestamp.isoformat()}},
                        {'name': 'status', 'value': {'stringValue': 'active'}}
                    ]
                },
                {
                    'sql': """
                        INSERT INTO user_profiles (user_id, phone, address, preferences, created_at)
                        VALUES (:user_id, :phone, :address, :preferences, :created_at)
                    """,
                    'parameters': [
                        {'name': 'user_id', 'value': {'stringValue': user_id}},
                        {'name': 'phone', 'value': {'stringValue': user_data.get('phone', '')}},
                        {'name': 'address', 'value': {'stringValue': user_data.get('address', '')}},
                        {'name': 'preferences', 'value': {'stringValue': json.dumps(user_data.get('preferences', {}))}},
                        {'name': 'created_at', 'value': {'stringValue': timestamp.isoformat()}}
                    ]
                }
            ]

            result = self.execute_transaction(statements)

            if result['success']:
                return user_id
            else:
                raise Exception("Failed to create user")

        def get_user_with_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
            """Get user with profile data using JOIN"""
            sql = """
                SELECT
                    u.user_id, u.email, u.name, u.created_at, u.status,
                    p.phone, p.address, p.preferences
                FROM users u
                LEFT JOIN user_profiles p ON u.user_id = p.user_id
                WHERE u.user_id = :user_id
            """

            parameters = [
                {'name': 'user_id', 'value': {'stringValue': user_id}}
            ]

            response = self.execute_statement(sql, parameters)

            if response['records']:
                record = response['records'][0]
                return {
                    'user_id': record[0]['stringValue'],
                    'email': record[1]['stringValue'],
                    'name': record[2]['stringValue'],
                    'created_at': record[3]['stringValue'],
                    'status': record[4]['stringValue'],
                    'phone': record[5]['stringValue'] if not record[5]['isNull'] else None,
                    'address': record[6]['stringValue'] if not record[6]['isNull'] else None,
                    'preferences': json.loads(record[7]['stringValue']) if not record[7]['isNull'] else {}
                }

            return None

        def create_order_with_items(self, order_data: Dict[str, Any]) -> str:
            """Create order with items using transaction"""
            order_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()

            statements = [
                {
                    'sql': """
                        INSERT INTO orders (order_id, user_id, total_amount, status, created_at)
                        VALUES (:order_id, :user_id, :total_amount, :status, :created_at)
                    """,
                    'parameters': [
                        {'name': 'order_id', 'value': {'stringValue': order_id}},
                        {'name': 'user_id', 'value': {'stringValue': order_data['user_id']}},
                        {'name': 'total_amount', 'value': {'doubleValue': order_data['total_amount']}},
                        {'name': 'status', 'value': {'stringValue': 'pending'}},
                        {'name': 'created_at', 'value': {'stringValue': timestamp.isoformat()}}
                    ]
                }
            ]

            # Add order items
            for item in order_data['items']:
                statements.append({
                    'sql': """
                        INSERT INTO order_items (order_id, product_id, quantity, price)
                        VALUES (:order_id, :product_id, :quantity, :price)
                    """,
                    'parameters': [
                        {'name': 'order_id', 'value': {'stringValue': order_id}},
                        {'name': 'product_id', 'value': {'stringValue': item['product_id']}},
                        {'name': 'quantity', 'value': {'longValue': item['quantity']}},
                        {'name': 'price', 'value': {'doubleValue': item['price']}}
                    ]
                })

                # Update inventory
                statements.append({
                    'sql': """
                        UPDATE products
                        SET stock = stock - :quantity
                        WHERE product_id = :product_id AND stock >= :quantity
                    """,
                    'parameters': [
                        {'name': 'quantity', 'value': {'longValue': item['quantity']}},
                        {'name': 'product_id', 'value': {'stringValue': item['product_id']}}
                    ]
                })

            result = self.execute_transaction(statements)

            if result['success']:
                return order_id
            else:
                raise Exception("Failed to create order")

        def get_analytics_data(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
            """Get analytics data with complex aggregations"""
            sql = """
                SELECT
                    DATE(o.created_at) as order_date,
                    COUNT(DISTINCT o.order_id) as total_orders,
                    COUNT(DISTINCT o.user_id) as unique_customers,
                    SUM(o.total_amount) as total_revenue,
                    AVG(o.total_amount) as avg_order_value,
                    SUM(CASE WHEN o.status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
                    SUM(CASE WHEN o.status = 'completed' THEN o.total_amount ELSE 0 END) as completed_revenue
                FROM orders o
                WHERE o.created_at BETWEEN :start_date AND :end_date
                GROUP BY DATE(o.created_at)
                ORDER BY order_date DESC
            """

            parameters = [
                {'name': 'start_date', 'value': {'stringValue': start_date}},
                {'name': 'end_date', 'value': {'stringValue': end_date}}
            ]

            response = self.execute_statement(sql, parameters)

            results = []
            for record in response['records']:
                results.append({
                    'order_date': record[0]['stringValue'],
                    'total_orders': record[1]['longValue'],
                    'unique_customers': record[2]['longValue'],
                    'total_revenue': record[3]['doubleValue'],
                    'avg_order_value': record[4]['doubleValue'],
                    'completed_orders': record[5]['longValue'],
                    'completed_revenue': record[6]['doubleValue']
                })

            return results

# Lambda handler using Aurora Data API
def aurora_lambda_handler(event, context):
    """Lambda handler using Aurora Serverless Data API"""

    db = AuroraDataAPI(
        cluster_arn=os.environ['CLUSTER_ARN'],
        secret_arn=os.environ['SECRET_ARN'],
        database_name=os.environ['DATABASE_NAME']
    )

    try:
        action = event.get('action')

        if action == 'create_user':
            user_id = db.create_user(event['user_data'])
            return {
                'statusCode': 201,
                'body': json.dumps({'user_id': user_id, 'status': 'created'})
            }

        elif action == 'get_user':
            user = db.get_user_with_profile(event['user_id'])
            if user:
                return {
                    'statusCode': 200,
                    'body': json.dumps(user)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'User not found'})
                }

        elif action == 'create_order':
            order_id = db.create_order_with_items(event['order_data'])
            return {
                'statusCode': 201,
                'body': json.dumps({'order_id': order_id, 'status': 'created'})
            }

        elif action == 'get_analytics':
            analytics = db.get_analytics_data(
                event['start_date'],
                event['end_date']
            )
            return {
                'statusCode': 200,
                'body': json.dumps({'analytics': analytics})
            }

        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid action'})
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

## Data Streaming and Event Processing

### Kinesis Data Streams Integration

#### Real-time Data Processing Pipeline
```python
#!/usr/bin/env python3
"""
Kinesis Data Streams for Real-time Serverless Data Processing
"""

import json
import boto3
import base64
import gzip
from typing import Dict, List, Any
from datetime import datetime, timezone
import logging

class KinesisDataProcessor:
    def __init__(self, region: str = 'us-east-1'):
        self.kinesis_client = boto3.client('kinesis', region_name=region)
        self.firehose_client = boto3.client('firehose', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)

    def process_kinesis_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process Kinesis records from Lambda trigger"""
        processed_records = []
        failed_records = []

        for record in records:
            try:
                # Decode the record
                payload = self.decode_record(record)

                # Process based on event type
                processed_data = self.process_event(payload)

                if processed_data:
                    processed_records.append({
                        'recordId': record['recordId'],
                        'result': 'Ok',
                        'data': processed_data
                    })
                else:
                    failed_records.append({
                        'recordId': record['recordId'],
                        'result': 'ProcessingFailed'
                    })

            except Exception as e:
                logging.error(f"Error processing record {record.get('recordId', 'unknown')}: {str(e)}")
                failed_records.append({
                    'recordId': record['recordId'],
                    'result': 'ProcessingFailed'
                })

        return {
            'records': processed_records + failed_records,
            'processed_count': len(processed_records),
            'failed_count': len(failed_records)
        }

    def decode_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Decode Kinesis record data"""
        # Decode base64 data
        data = base64.b64decode(record['kinesis']['data']).decode('utf-8')

        # Check if data is gzipped
        try:
            if data.startswith('\x1f\x8b'):  # gzip magic number
                data = gzip.decompress(base64.b64decode(record['kinesis']['data'])).decode('utf-8')
        except:
            pass

        return json.loads(data)

    def process_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual event based on type"""
        event_type = event_data.get('event_type')

        if event_type == 'user_activity':
            return self.process_user_activity(event_data)
        elif event_type == 'order_event':
            return self.process_order_event(event_data)
        elif event_type == 'product_view':
            return self.process_product_view(event_data)
        elif event_type == 'system_metric':
            return self.process_system_metric(event_data)
        else:
            logging.warning(f"Unknown event type: {event_type}")
            return None

    def process_user_activity(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user activity events"""
        # Enrich with additional data
        enriched_data = {
            **event_data,
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'session_duration': self.calculate_session_duration(event_data),
            'user_segment': self.determine_user_segment(event_data['user_id'])
        }

        # Store in real-time analytics table
        self.store_user_activity(enriched_data)

        # Update user session state
        self.update_user_session(enriched_data)

        return enriched_data

    def process_order_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process order-related events"""
        order_data = event_data['data']

        # Calculate order metrics
        enriched_data = {
            **event_data,
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'order_hour': datetime.fromisoformat(event_data['timestamp']).hour,
            'order_day_of_week': datetime.fromisoformat(event_data['timestamp']).weekday(),
            'items_count': len(order_data.get('items', [])),
            'avg_item_price': self.calculate_avg_item_price(order_data.get('items', []))
        }

        # Update real-time metrics
        self.update_order_metrics(enriched_data)

        # Trigger downstream processing if needed
        if event_data.get('event_subtype') == 'order_completed':
            self.trigger_fulfillment_process(enriched_data)

        return enriched_data

    def process_product_view(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process product view events for recommendations"""
        # Update product popularity metrics
        product_id = event_data['data']['product_id']
        user_id = event_data.get('user_id')

        enriched_data = {
            **event_data,
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'view_hour': datetime.fromisoformat(event_data['timestamp']).hour,
            'referrer': event_data.get('data', {}).get('referrer'),
            'device_type': event_data.get('data', {}).get('device_type')
        }

        # Update product view counts
        self.update_product_views(product_id, enriched_data)

        # Update user behavior profile
        if user_id:
            self.update_user_behavior(user_id, product_id, enriched_data)

        return enriched_data

    def calculate_session_duration(self, event_data: Dict[str, Any]) -> Optional[float]:
        """Calculate session duration for user activity"""
        user_id = event_data.get('user_id')
        if not user_id:
            return None

        # Get last activity timestamp from DynamoDB
        sessions_table = self.dynamodb.Table('user_sessions')

        try:
            response = sessions_table.get_item(
                Key={'user_id': user_id}
            )

            if 'Item' in response:
                last_activity = datetime.fromisoformat(response['Item']['last_activity'])
                current_time = datetime.fromisoformat(event_data['timestamp'])
                return (current_time - last_activity).total_seconds()

        except Exception as e:
            logging.error(f"Error calculating session duration: {e}")

        return None

    def store_user_activity(self, activity_data: Dict[str, Any]):
        """Store user activity in DynamoDB for real-time analytics"""
        activity_table = self.dynamodb.Table('user_activities')

        try:
            activity_table.put_item(
                Item={
                    'user_id': activity_data['user_id'],
                    'timestamp': activity_data['timestamp'],
                    'activity_type': activity_data['data']['activity_type'],
                    'page_url': activity_data['data'].get('page_url'),
                    'session_duration': activity_data.get('session_duration'),
                    'user_segment': activity_data.get('user_segment'),
                    'ttl': int((datetime.now(timezone.utc).timestamp() + 86400 * 30))  # 30 days TTL
                }
            )

        except Exception as e:
            logging.error(f"Error storing user activity: {e}")

    def update_order_metrics(self, order_data: Dict[str, Any]):
        """Update real-time order metrics"""
        metrics_table = self.dynamodb.Table('order_metrics')

        order_hour = order_data['order_hour']
        order_date = datetime.fromisoformat(order_data['timestamp']).date().isoformat()

        try:
            # Update hourly metrics
            metrics_table.update_item(
                Key={
                    'metric_type': 'hourly_orders',
                    'time_bucket': f"{order_date}#{order_hour:02d}"
                },
                UpdateExpression='ADD order_count :inc, total_revenue :revenue',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':revenue': order_data['data']['total_amount']
                }
            )

            # Update daily metrics
            metrics_table.update_item(
                Key={
                    'metric_type': 'daily_orders',
                    'time_bucket': order_date
                },
                UpdateExpression='ADD order_count :inc, total_revenue :revenue, items_sold :items',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':revenue': order_data['data']['total_amount'],
                    ':items': order_data['items_count']
                }
            )

        except Exception as e:
            logging.error(f"Error updating order metrics: {e}")

    def update_product_views(self, product_id: str, view_data: Dict[str, Any]):
        """Update product view metrics"""
        views_table = self.dynamodb.Table('product_metrics')

        view_hour = view_data['view_hour']
        view_date = datetime.fromisoformat(view_data['timestamp']).date().isoformat()

        try:
            # Update product view count
            views_table.update_item(
                Key={
                    'product_id': product_id,
                    'metric_date': view_date
                },
                UpdateExpression='ADD view_count :inc SET last_viewed = :timestamp',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':timestamp': view_data['timestamp']
                }
            )

            # Update hourly view distribution
            views_table.update_item(
                Key={
                    'product_id': f"{product_id}#HOURLY",
                    'metric_date': view_date
                },
                UpdateExpression=f'ADD hour_{view_hour:02d} :inc',
                ExpressionAttributeValues={':inc': 1}
            )

        except Exception as e:
            logging.error(f"Error updating product views: {e}")

# Lambda handler for Kinesis processing
def kinesis_processor_handler(event, context):
    """Lambda handler for processing Kinesis Data Streams"""

    processor = KinesisDataProcessor()

    try:
        # Process all records from Kinesis
        result = processor.process_kinesis_records(event['Records'])

        logging.info(f"Processed {result['processed_count']} records successfully, {result['failed_count']} failed")

        return {
            'batchItemFailures': [
                {'itemIdentifier': record['recordId']}
                for record in result['records']
                if record['result'] == 'ProcessingFailed'
            ]
        }

    except Exception as e:
        logging.error(f"Error in Kinesis processor: {str(e)}")
        # Return all records as failed for retry
        return {
            'batchItemFailures': [
                {'itemIdentifier': record['kinesis']['sequenceNumber']}
                for record in event['Records']
            ]
        }

# Enhanced Kinesis Analytics
class KinesisAnalytics:
    def __init__(self):
        self.kinesis_analytics = boto3.client('kinesisanalyticsv2')

    def create_analytics_application(self):
        """Create Kinesis Analytics application for real-time processing"""

        sql_query = """
        CREATE OR REPLACE STREAM "DESTINATION_SQL_STREAM" (
            product_id VARCHAR(64),
            view_count INTEGER,
            unique_viewers INTEGER,
            avg_session_duration DOUBLE,
            window_start TIMESTAMP,
            window_end TIMESTAMP
        );

        CREATE OR REPLACE PUMP "STREAM_PUMP" AS INSERT INTO "DESTINATION_SQL_STREAM"
        SELECT STREAM
            product_id,
            COUNT(*) as view_count,
            COUNT(DISTINCT user_id) as unique_viewers,
            AVG(session_duration) as avg_session_duration,
            ROWTIME_TO_TIMESTAMP(ROWTIME - INTERVAL '1' MINUTE) as window_start,
            ROWTIME_TO_TIMESTAMP(ROWTIME) as window_end
        FROM "SOURCE_SQL_STREAM_001"
        WHERE event_type = 'product_view'
        GROUP BY
            product_id,
            RANGE(INTERVAL '1' MINUTE PRECEDING);
        """

        return sql_query
```

This comprehensive Serverless Data Management document provides advanced patterns for DynamoDB single table design, Aurora Serverless with Data API, real-time data processing with Kinesis, and sophisticated data access patterns essential for building scalable serverless data architectures.