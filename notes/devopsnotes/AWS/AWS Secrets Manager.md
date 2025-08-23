# AWS Secrets Manager: Enterprise Security & DevOps Secret Management Platform

> **Service Type:** Security, Identity & Compliance | **Scope:** Regional | **Serverless:** Yes

## Overview

AWS Secrets Manager is a comprehensive enterprise-grade secret management service designed for protecting and automating the lifecycle of sensitive information across complex DevOps environments. It provides advanced encryption, automated rotation, fine-grained access control, and seamless integration with CI/CD pipelines, enabling zero-trust security architectures and compliance-driven secret management at scale.

## Enterprise Secrets Manager Framework

### 1. Advanced Enterprise Secret Management System

```python
import boto3
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecretType(Enum):
    DATABASE_CREDENTIALS = "database_credentials"
    API_KEYS = "api_keys"
    CERTIFICATES = "certificates"
    OAUTH_TOKENS = "oauth_tokens"
    SSH_KEYS = "ssh_keys"
    APPLICATION_CONFIG = "application_config"
    ENCRYPTION_KEYS = "encryption_keys"
    SERVICE_ACCOUNTS = "service_accounts"

class RotationStatus(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"

class ComplianceLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"

@dataclass
class SecretPolicy:
    max_age_days: int
    rotation_enabled: bool
    rotation_interval_days: int
    access_logging_required: bool
    encryption_required: bool
    cross_region_replication: bool
    compliance_level: ComplianceLevel
    approved_principals: List[str] = field(default_factory=list)
    blackout_windows: List[Dict[str, str]] = field(default_factory=list)
    notification_topics: List[str] = field(default_factory=list)

@dataclass
class SecretMetadata:
    secret_arn: str
    secret_name: str
    secret_type: SecretType
    environment: str
    application: str
    owner: str
    created_date: datetime
    last_accessed: Optional[datetime]
    last_rotated: Optional[datetime]
    next_rotation: Optional[datetime]
    access_count: int
    compliance_level: ComplianceLevel
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class SecretAuditEvent:
    event_id: str
    secret_arn: str
    action: str
    principal: str
    source_ip: str
    user_agent: str
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)

class EnterpriseSecretsManager:
    """
    Enterprise-grade AWS Secrets Manager with advanced security policies,
    compliance automation, audit trails, and DevOps integration.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.secrets_client = boto3.client('secretsmanager', region_name=region)
        self.kms_client = boto3.client('kms', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.cloudtrail = boto3.client('cloudtrail', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.region = region
        self.logger = self._setup_logging()
        
        # Enterprise management state
        self.secret_policies = {}
        self.audit_table = None
        self.compliance_rules = {}
        self.secret_inventory = {}
        self.rotation_schedules = {}
        self.access_patterns = {}
        
        # Initialize audit table
        self._initialize_audit_infrastructure()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging for secrets operations"""
        logger = logging.getLogger('secrets_manager')
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(secret_name)s - %(action)s - %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _initialize_audit_infrastructure(self):
        """Initialize audit and compliance infrastructure"""
        
        try:
            # Create audit table if not exists
            table_name = 'enterprise-secrets-audit'
            
            try:
                self.audit_table = self.dynamodb.Table(table_name)
                self.audit_table.load()  # Test if table exists
            except:
                # Create audit table
                self.audit_table = self.dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'secret_arn', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'secret_arn', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                        {'AttributeName': 'action', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'action-timestamp-index',
                            'KeySchema': [
                                {'AttributeName': 'action', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'BillingMode': 'PAY_PER_REQUEST'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST',
                    Tags=[
                        {'Key': 'Purpose', 'Value': 'SecretsAudit'},
                        {'Key': 'ManagedBy', 'Value': 'EnterpriseSecretsManager'}
                    ]
                )
                
                # Wait for table to be created
                self.audit_table.wait_until_exists()
                
            self.logger.info("Audit infrastructure initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audit infrastructure: {e}")
            raise
    
    def create_enterprise_secret(self, 
                               secret_name: str,
                               secret_value: Union[str, Dict[str, Any]],
                               secret_type: SecretType,
                               environment: str,
                               application: str,
                               owner: str,
                               policy: SecretPolicy,
                               description: Optional[str] = None,
                               kms_key_id: Optional[str] = None) -> Dict[str, Any]:
        """Create enterprise secret with comprehensive security policies"""
        
        # Validate secret according to compliance requirements
        self._validate_secret_compliance(secret_value, policy.compliance_level)
        
        # Prepare secret value
        if isinstance(secret_value, dict):
            secret_string = json.dumps(secret_value)
        else:
            secret_string = str(secret_value)
        
        # Enhance with enterprise metadata
        enterprise_tags = {
            'SecretType': secret_type.value,
            'Environment': environment,
            'Application': application,
            'Owner': owner,
            'ComplianceLevel': policy.compliance_level.value,
            'CreatedBy': 'EnterpriseSecretsManager',
            'CreatedAt': datetime.utcnow().isoformat(),
            'RotationEnabled': str(policy.rotation_enabled),
            'DataClassification': policy.compliance_level.value
        }
        
        # Add custom tags
        enterprise_tags.update(policy.approved_principals)
        
        try:
            # Create the secret
            response = self.secrets_client.create_secret(
                Name=secret_name,
                Description=description or f"Enterprise {secret_type.value} for {application}",
                SecretString=secret_string,
                KmsKeyId=kms_key_id or self._get_compliance_kms_key(policy.compliance_level),
                ReplicaRegions=self._get_replica_regions(policy) if policy.cross_region_replication else [],
                Tags=[
                    {'Key': k, 'Value': v} for k, v in enterprise_tags.items()
                ]
            )
            
            secret_arn = response['ARN']
            
            # Store secret metadata
            metadata = SecretMetadata(
                secret_arn=secret_arn,
                secret_name=secret_name,
                secret_type=secret_type,
                environment=environment,
                application=application,
                owner=owner,
                created_date=datetime.utcnow(),
                last_accessed=None,
                last_rotated=None,
                next_rotation=None,
                access_count=0,
                compliance_level=policy.compliance_level,
                tags=enterprise_tags
            )
            
            self.secret_inventory[secret_arn] = metadata
            self.secret_policies[secret_arn] = policy
            
            # Set up resource policy
            resource_policy = self._create_secret_resource_policy(
                secret_arn,
                policy
            )
            
            self.secrets_client.put_resource_policy(
                SecretId=secret_arn,
                ResourcePolicy=json.dumps(resource_policy),
                BlockPublicPolicy=True
            )
            
            # Configure rotation if enabled
            if policy.rotation_enabled:
                self._setup_secret_rotation(
                    secret_arn,
                    secret_type,
                    policy.rotation_interval_days
                )
            
            # Configure monitoring and alerting
            self._setup_secret_monitoring(secret_arn, policy)
            
            # Record audit event
            await self._record_audit_event(
                SecretAuditEvent(
                    event_id=str(uuid.uuid4()),
                    secret_arn=secret_arn,
                    action='CREATE_SECRET',
                    principal='system',
                    source_ip='internal',
                    user_agent='EnterpriseSecretsManager',
                    timestamp=datetime.utcnow(),
                    success=True,
                    additional_context={
                        'secret_type': secret_type.value,
                        'environment': environment,
                        'application': application,
                        'compliance_level': policy.compliance_level.value
                    }
                )
            )
            
            self.logger.info(
                f"Enterprise secret created: {secret_name}",
                extra={'secret_name': secret_name, 'action': 'create'}
            )
            
            return {
                'secret_arn': secret_arn,
                'secret_name': secret_name,
                'version_id': response['VersionId'],
                'status': 'created',
                'rotation_enabled': policy.rotation_enabled,
                'compliance_level': policy.compliance_level.value,
                'monitoring_enabled': True
            }
            
        except Exception as e:
            # Record failed audit event
            await self._record_audit_event(
                SecretAuditEvent(
                    event_id=str(uuid.uuid4()),
                    secret_arn='unknown',
                    action='CREATE_SECRET',
                    principal='system',
                    source_ip='internal',
                    user_agent='EnterpriseSecretsManager',
                    timestamp=datetime.utcnow(),
                    success=False,
                    error_message=str(e)
                )
            )
            
            self.logger.error(
                f"Failed to create secret: {e}",
                extra={'secret_name': secret_name, 'action': 'create'}
            )
            raise
    
    def _validate_secret_compliance(self, 
                                  secret_value: Union[str, Dict[str, Any]],
                                  compliance_level: ComplianceLevel):
        """Validate secret meets compliance requirements"""
        
        if isinstance(secret_value, dict):
            secret_str = json.dumps(secret_value)
        else:
            secret_str = str(secret_value)
        
        # Check for prohibited patterns
        prohibited_patterns = [
            'password123',
            'admin',
            'root',
            'test',
            'demo'
        ]
        
        secret_lower = secret_str.lower()
        for pattern in prohibited_patterns:
            if pattern in secret_lower:
                raise ValueError(f"Secret contains prohibited pattern: {pattern}")
        
        # Compliance-specific validation
        if compliance_level in [ComplianceLevel.RESTRICTED, ComplianceLevel.TOP_SECRET]:
            # Enhanced validation for high-security secrets
            if len(secret_str) < 20:
                raise ValueError("High-security secrets must be at least 20 characters")
            
            # Check for complexity requirements
            if isinstance(secret_value, str):
                if not self._check_password_complexity(secret_value):
                    raise ValueError("Secret does not meet complexity requirements")
        
        # Check for PII or sensitive data patterns
        self._check_for_sensitive_data(secret_str)
    
    def _check_password_complexity(self, password: str) -> bool:
        """Check password complexity requirements"""
        
        import re
        
        # At least 12 characters
        if len(password) < 12:
            return False
        
        # Contains uppercase, lowercase, digit, and special character
        patterns = [
            r'[A-Z]',  # uppercase
            r'[a-z]',  # lowercase
            r'\d',     # digit
            r'[!@#$%^&*(),.?":{}|<>]'  # special character
        ]
        
        return all(re.search(pattern, password) for pattern in patterns)
    
    def _check_for_sensitive_data(self, secret_str: str):
        """Check for potential PII or sensitive data patterns"""
        
        import re
        
        # Social Security Number pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, secret_str):
            self.logger.warning("Potential SSN detected in secret")
        
        # Credit card pattern
        cc_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        if re.search(cc_pattern, secret_str):
            self.logger.warning("Potential credit card number detected in secret")
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, secret_str):
            self.logger.warning("Email address detected in secret")
    
    def _get_compliance_kms_key(self, compliance_level: ComplianceLevel) -> str:
        """Get appropriate KMS key based on compliance level"""
        
        compliance_key_map = {
            ComplianceLevel.PUBLIC: 'alias/secrets-public',
            ComplianceLevel.INTERNAL: 'alias/secrets-internal',
            ComplianceLevel.CONFIDENTIAL: 'alias/secrets-confidential',
            ComplianceLevel.RESTRICTED: 'alias/secrets-restricted',
            ComplianceLevel.TOP_SECRET: 'alias/secrets-top-secret'
        }
        
        return compliance_key_map.get(compliance_level, 'alias/secrets-default')
    
    def _create_secret_resource_policy(self, 
                                     secret_arn: str,
                                     policy: SecretPolicy) -> Dict[str, Any]:
        """Create resource policy for secret access control"""
        
        statements = []
        
        # Allow access to approved principals
        if policy.approved_principals:
            statements.append({
                "Sid": "AllowApprovedPrincipals",
                "Effect": "Allow",
                "Principal": {
                    "AWS": policy.approved_principals
                },
                "Action": [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "secretsmanager:VersionStage": "AWSCURRENT"
                    }
                }
            })
        
        # Add time-based restrictions if specified
        if policy.blackout_windows:
            # This would require more complex condition logic
            # For demonstration, we'll add a basic time restriction
            statements.append({
                "Sid": "DenyOutsideBusinessHours",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "secretsmanager:GetSecretValue",
                "Resource": "*",
                "Condition": {
                    "DateGreaterThan": {
                        "aws:CurrentTime": "18:00Z"
                    },
                    "DateLessThan": {
                        "aws:CurrentTime": "08:00Z"
                    }
                }
            })
        
        # Require MFA for high-security secrets
        if policy.compliance_level in [ComplianceLevel.RESTRICTED, ComplianceLevel.TOP_SECRET]:
            statements.append({
                "Sid": "RequireMFA",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "secretsmanager:GetSecretValue",
                "Resource": "*",
                "Condition": {
                    "Bool": {
                        "aws:MultiFactorAuthPresent": "false"
                    }
                }
            })
        
        return {
            "Version": "2012-10-17",
            "Statement": statements
        }
    
    async def retrieve_secret_securely(self, 
                                     secret_identifier: str,
                                     version_stage: str = 'AWSCURRENT',
                                     requesting_principal: str = None,
                                     source_ip: str = None,
                                     purpose: str = None) -> Dict[str, Any]:
        """Securely retrieve secret with comprehensive audit logging"""
        
        start_time = time.time()
        
        try:
            # Pre-access validation
            secret_metadata = await self._get_secret_metadata(secret_identifier)
            
            if not secret_metadata:
                raise ValueError(f"Secret not found: {secret_identifier}")
            
            # Check access policy compliance
            self._validate_access_request(
                secret_metadata,
                requesting_principal,
                source_ip
            )
            
            # Retrieve secret value
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.secrets_client.get_secret_value(
                    SecretId=secret_identifier,
                    VersionStage=version_stage
                )
            )
            
            secret_arn = response['ARN']
            secret_value = response['SecretString']
            
            # Update access metrics
            await self._update_access_metrics(secret_arn)
            
            # Record audit event
            await self._record_audit_event(
                SecretAuditEvent(
                    event_id=str(uuid.uuid4()),
                    secret_arn=secret_arn,
                    action='GET_SECRET_VALUE',
                    principal=requesting_principal or 'unknown',
                    source_ip=source_ip or 'unknown',
                    user_agent='EnterpriseSecretsManager',
                    timestamp=datetime.utcnow(),
                    success=True,
                    additional_context={
                        'version_stage': version_stage,
                        'purpose': purpose,
                        'response_time_ms': (time.time() - start_time) * 1000
                    }
                )
            )
            
            # Parse secret value if JSON
            try:
                parsed_value = json.loads(secret_value)
            except json.JSONDecodeError:
                parsed_value = secret_value
            
            self.logger.info(
                f"Secret retrieved successfully: {secret_metadata.secret_name}",
                extra={'secret_name': secret_metadata.secret_name, 'action': 'retrieve'}
            )
            
            return {
                'secret_arn': secret_arn,
                'secret_name': secret_metadata.secret_name,
                'secret_value': parsed_value,
                'version_id': response['VersionId'],
                'version_stages': response.get('VersionStages', []),
                'created_date': response['CreatedDate'],
                'metadata': {
                    'secret_type': secret_metadata.secret_type.value,
                    'environment': secret_metadata.environment,
                    'application': secret_metadata.application,
                    'compliance_level': secret_metadata.compliance_level.value
                }
            }
            
        except Exception as e:
            # Record failed audit event
            await self._record_audit_event(
                SecretAuditEvent(
                    event_id=str(uuid.uuid4()),
                    secret_arn=secret_identifier,
                    action='GET_SECRET_VALUE',
                    principal=requesting_principal or 'unknown',
                    source_ip=source_ip or 'unknown',
                    user_agent='EnterpriseSecretsManager',
                    timestamp=datetime.utcnow(),
                    success=False,
                    error_message=str(e),
                    additional_context={
                        'version_stage': version_stage,
                        'purpose': purpose
                    }
                )
            )
            
            self.logger.error(
                f"Failed to retrieve secret: {e}",
                extra={'secret_name': secret_identifier, 'action': 'retrieve'}
            )
            raise
    
    async def _record_audit_event(self, event: SecretAuditEvent):
        """Record audit event to DynamoDB"""
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.audit_table.put_item(
                    Item={
                        'secret_arn': event.secret_arn,
                        'timestamp': event.timestamp.isoformat(),
                        'event_id': event.event_id,
                        'action': event.action,
                        'principal': event.principal,
                        'source_ip': event.source_ip,
                        'user_agent': event.user_agent,
                        'success': event.success,
                        'error_message': event.error_message,
                        'additional_context': event.additional_context,
                        'ttl': int((datetime.utcnow() + timedelta(days=2555)).timestamp())  # 7 years retention
                    }
                )
            )
        except Exception as e:
            self.logger.error(f"Failed to record audit event: {e}")
    
    def setup_enterprise_rotation_framework(self) -> Dict[str, Any]:
        """Set up comprehensive secret rotation framework"""
        
        rotation_functions = {
            SecretType.DATABASE_CREDENTIALS: self._create_database_rotation_function(),
            SecretType.API_KEYS: self._create_api_key_rotation_function(),
            SecretType.CERTIFICATES: self._create_certificate_rotation_function(),
            SecretType.OAUTH_TOKENS: self._create_oauth_rotation_function(),
            SecretType.SSH_KEYS: self._create_ssh_key_rotation_function()
        }
        
        # Create rotation monitoring
        monitoring_config = self._setup_rotation_monitoring()
        
        # Create rotation scheduler
        scheduler_config = self._create_rotation_scheduler()
        
        return {
            'rotation_functions': len(rotation_functions),
            'monitoring_enabled': monitoring_config['enabled'],
            'scheduler_enabled': scheduler_config['enabled'],
            'supported_secret_types': [st.value for st in rotation_functions.keys()]
        }
    
    def generate_compliance_report(self, 
                                 compliance_level: Optional[ComplianceLevel] = None,
                                 environment: Optional[str] = None,
                                 days_back: int = 30) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        report_start_time = datetime.utcnow()
        report_end_time = report_start_time - timedelta(days=days_back)
        
        # Get all secrets matching criteria
        filtered_secrets = []
        for arn, metadata in self.secret_inventory.items():
            if compliance_level and metadata.compliance_level != compliance_level:
                continue
            if environment and metadata.environment != environment:
                continue
            filtered_secrets.append(metadata)
        
        # Analyze compliance posture
        compliance_analysis = {
            'total_secrets': len(filtered_secrets),
            'by_compliance_level': {},
            'by_environment': {},
            'by_secret_type': {},
            'rotation_status': {
                'enabled': 0,
                'disabled': 0,
                'overdue': 0
            },
            'access_patterns': {},
            'security_violations': [],
            'recommendations': []
        }
        
        # Analyze secrets
        for metadata in filtered_secrets:
            # Group by compliance level
            level = metadata.compliance_level.value
            compliance_analysis['by_compliance_level'][level] = \
                compliance_analysis['by_compliance_level'].get(level, 0) + 1
            
            # Group by environment
            env = metadata.environment
            compliance_analysis['by_environment'][env] = \
                compliance_analysis['by_environment'].get(env, 0) + 1
            
            # Group by secret type
            stype = metadata.secret_type.value
            compliance_analysis['by_secret_type'][stype] = \
                compliance_analysis['by_secret_type'].get(stype, 0) + 1
            
            # Check rotation status
            policy = self.secret_policies.get(metadata.secret_arn)
            if policy and policy.rotation_enabled:
                compliance_analysis['rotation_status']['enabled'] += 1
                
                # Check if overdue
                if metadata.next_rotation and metadata.next_rotation < datetime.utcnow():
                    compliance_analysis['rotation_status']['overdue'] += 1
            else:
                compliance_analysis['rotation_status']['disabled'] += 1
        
        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(compliance_analysis)
        compliance_analysis['recommendations'] = recommendations
        
        return {
            'report_generated_at': report_start_time.isoformat(),
            'report_period_days': days_back,
            'filters': {
                'compliance_level': compliance_level.value if compliance_level else 'all',
                'environment': environment or 'all'
            },
            'compliance_analysis': compliance_analysis,
            'executive_summary': self._generate_executive_summary(compliance_analysis)
        }

# Usage Example
if __name__ == "__main__":
    # Initialize enterprise secrets manager
    secrets_mgr = EnterpriseSecretsManager()
    
    # Define enterprise security policy
    high_security_policy = SecretPolicy(
        max_age_days=90,
        rotation_enabled=True,
        rotation_interval_days=30,
        access_logging_required=True,
        encryption_required=True,
        cross_region_replication=True,
        compliance_level=ComplianceLevel.CONFIDENTIAL,
        approved_principals=[
            "arn:aws:iam::123456789012:role/ProductionAppRole",
            "arn:aws:iam::123456789012:role/DevOpsRole"
        ],
        blackout_windows=[
            {"start": "18:00", "end": "08:00", "timezone": "UTC"}
        ],
        notification_topics=[
            "arn:aws:sns:us-east-1:123456789012:secrets-alerts"
        ]
    )
    
    # Create enterprise database secret
    database_secret = {
        "username": "app_user",
        "password": "SecureP@ssw0rd123!ComplexEnough",
        "engine": "postgresql",
        "host": "prod-db.cluster-xyz.us-east-1.rds.amazonaws.com",
        "port": 5432,
        "dbname": "production_app",
        "ssl_mode": "require"
    }
    
    result = secrets_mgr.create_enterprise_secret(
        secret_name="prod/webapp/database-credentials",
        secret_value=database_secret,
        secret_type=SecretType.DATABASE_CREDENTIALS,
        environment="production",
        application="webapp",
        owner="platform-team@enterprise.com",
        policy=high_security_policy,
        description="Production database credentials for web application"
    )
    
    print(f"Enterprise secret created: {result['secret_name']}")
    print(f"Compliance level: {result['compliance_level']}")
    print(f"Rotation enabled: {result['rotation_enabled']}")
    
    # Set up enterprise rotation framework
    rotation_setup = secrets_mgr.setup_enterprise_rotation_framework()
    print(f"Rotation framework configured for {rotation_setup['rotation_functions']} secret types")
    
    # Generate compliance report
    compliance_report = secrets_mgr.generate_compliance_report(
        compliance_level=ComplianceLevel.CONFIDENTIAL,
        environment="production",
        days_back=30
    )
    
    print(f"\nCompliance Report Summary:")
    print(f"Total secrets analyzed: {compliance_report['compliance_analysis']['total_secrets']}")
    print(f"Rotation enabled: {compliance_report['compliance_analysis']['rotation_status']['enabled']}")
    print(f"Overdue rotations: {compliance_report['compliance_analysis']['rotation_status']['overdue']}")
    
    # Demonstrate secure secret retrieval
    async def retrieve_secret_example():
        secret_data = await secrets_mgr.retrieve_secret_securely(
            secret_identifier="prod/webapp/database-credentials",
            requesting_principal="arn:aws:iam::123456789012:role/ProductionAppRole",
            source_ip="10.0.1.100",
            purpose="database_connection"
        )
        
        print(f"\nSecret retrieved: {secret_data['secret_name']}")
        print(f"Environment: {secret_data['metadata']['environment']}")
        print(f"Secret type: {secret_data['metadata']['secret_type']}")
        
        return secret_data
    
    # Run the async example
    import asyncio
    retrieved_secret = asyncio.run(retrieve_secret_example())
```

### 2. DevOps Pipeline Security Integration

```python
import boto3
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from enum import Enum

class PipelineStage(Enum):
    BUILD = "build"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"
    ROLLBACK = "rollback"

class SecretScope(Enum):
    GLOBAL = "global"
    ENVIRONMENT = "environment"
    APPLICATION = "application"
    PIPELINE = "pipeline"

@dataclass
class PipelineSecretConfig:
    secret_name: str
    secret_scope: SecretScope
    required_stages: List[PipelineStage]
    environment_variable_name: str
    masked_in_logs: bool = True
    rotation_safe: bool = True
    validation_required: bool = True

class DevOpsPipelineSecretsManager:
    """
    DevOps pipeline-specific secrets management with automated
    injection, validation, and secure handling across CI/CD stages.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.secrets_client = boto3.client('secretsmanager', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        self.codebuild = boto3.client('codebuild', region_name=region)
        self.codepipeline = boto3.client('codepipeline', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
        self.pipeline_configs = {}
        self.secret_mappings = {}
        self.validation_functions = {}
        
    def setup_pipeline_secrets_framework(self, 
                                       pipeline_name: str,
                                       environment: str,
                                       secret_configs: List[PipelineSecretConfig]) -> Dict[str, Any]:
        """Set up comprehensive secrets framework for CI/CD pipeline"""
        
        try:
            # Create secret injection Lambda function
            injection_function = self._create_secret_injection_function(
                pipeline_name,
                environment
            )
            
            # Create secret validation Lambda function
            validation_function = self._create_secret_validation_function(
                pipeline_name,
                environment
            )
            
            # Configure CodeBuild projects with secret injection
            build_configs = self._configure_codebuild_secrets(
                pipeline_name,
                environment,
                secret_configs
            )
            
            # Set up secret rotation notifications for pipeline
            rotation_notifications = self._setup_pipeline_rotation_notifications(
                pipeline_name,
                environment,
                secret_configs
            )
            
            # Create secret deployment automation
            deployment_automation = self._create_secret_deployment_automation(
                pipeline_name,
                environment,
                secret_configs
            )
            
            # Store pipeline configuration
            pipeline_key = f"{pipeline_name}:{environment}"
            self.pipeline_configs[pipeline_key] = {
                'pipeline_name': pipeline_name,
                'environment': environment,
                'secret_configs': secret_configs,
                'injection_function_arn': injection_function['FunctionArn'],
                'validation_function_arn': validation_function['FunctionArn'],
                'build_configs': build_configs,
                'created_at': datetime.utcnow()
            }
            
            return {
                'pipeline_name': pipeline_name,
                'environment': environment,
                'secrets_configured': len(secret_configs),
                'injection_function_arn': injection_function['FunctionArn'],
                'validation_function_arn': validation_function['FunctionArn'],
                'build_projects_updated': len(build_configs),
                'rotation_notifications_enabled': len(rotation_notifications)
            }
            
        except Exception as e:
            raise Exception(f"Failed to setup pipeline secrets framework: {e}")
    
    def _create_secret_injection_function(self, 
                                        pipeline_name: str,
                                        environment: str) -> Dict[str, Any]:
        """Create Lambda function for secure secret injection"""
        
        function_code = '''
import boto3
import json
import os
from typing import Dict, Any

def lambda_handler(event, context):
    """Securely inject secrets into pipeline environment"""
    
    secrets_client = boto3.client('secretsmanager')
    
    try:
        # Get pipeline configuration from event
        pipeline_name = event['pipeline_name']
        stage = event['stage']
        secret_configs = event['secret_configs']
        
        # Prepare environment variables
        environment_vars = {}
        
        for config in secret_configs:
            if stage in config['required_stages']:
                # Retrieve secret
                secret_response = secrets_client.get_secret_value(
                    SecretId=config['secret_name']
                )
                
                secret_value = secret_response['SecretString']
                
                # Validate secret if required
                if config.get('validation_required', False):
                    validation_result = validate_secret(
                        config['secret_name'],
                        secret_value,
                        config
                    )
                    
                    if not validation_result['valid']:
                        raise Exception(f"Secret validation failed: {validation_result['error']}")
                
                # Add to environment variables
                environment_vars[config['environment_variable_name']] = secret_value
        
        return {
            'statusCode': 200,
            'body': {
                'environment_variables': environment_vars,
                'secrets_injected': len(environment_vars)
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }

def validate_secret(secret_name: str, secret_value: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate secret value meets requirements"""
    
    try:
        # Basic validation
        if not secret_value:
            return {'valid': False, 'error': 'Secret value is empty'}
        
        # Type-specific validation
        if 'database' in secret_name.lower():
            return validate_database_secret(secret_value)
        elif 'api' in secret_name.lower():
            return validate_api_secret(secret_value)
        else:
            return {'valid': True}
            
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def validate_database_secret(secret_value: str) -> Dict[str, Any]:
    """Validate database secret format"""
    
    try:
        secret_data = json.loads(secret_value)
        required_fields = ['username', 'password', 'host', 'port']
        
        for field in required_fields:
            if field not in secret_data:
                return {'valid': False, 'error': f'Missing required field: {field}'}
        
        return {'valid': True}
        
    except json.JSONDecodeError:
        return {'valid': False, 'error': 'Invalid JSON format'}

def validate_api_secret(secret_value: str) -> Dict[str, Any]:
    """Validate API secret format"""
    
    try:
        # For JSON secrets
        if secret_value.startswith('{'):
            secret_data = json.loads(secret_value)
            if 'api_key' not in secret_data:
                return {'valid': False, 'error': 'Missing api_key field'}
        
        # For plain text API keys
        elif len(secret_value) < 20:
            return {'valid': False, 'error': 'API key too short'}
        
        return {'valid': True}
        
    except json.JSONDecodeError:
        return {'valid': False, 'error': 'Invalid JSON format'}
'''
        
        function_name = f"pipeline-secret-injection-{pipeline_name}-{environment}"
        
        # Create Lambda function
        response = self.lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=f'arn:aws:iam::123456789012:role/PipelineSecretsLambdaRole',
            Handler='index.lambda_handler',
            Code={
                'ZipFile': function_code.encode('utf-8')
            },
            Description=f'Secret injection for {pipeline_name} pipeline',
            Timeout=60,
            Environment={
                'Variables': {
                    'PIPELINE_NAME': pipeline_name,
                    'ENVIRONMENT': environment
                }
            },
            Tags={
                'Pipeline': pipeline_name,
                'Environment': environment,
                'Purpose': 'SecretInjection'
            }
        )
        
        return response
    
    def create_secure_buildspec(self, 
                              pipeline_name: str,
                              environment: str,
                              base_buildspec: Dict[str, Any],
                              secret_configs: List[PipelineSecretConfig]) -> Dict[str, Any]:
        """Create secure buildspec with secret injection and masking"""
        
        # Clone base buildspec
        secure_buildspec = json.loads(json.dumps(base_buildspec))
        
        # Add secret injection to pre_build phase
        if 'phases' not in secure_buildspec:
            secure_buildspec['phases'] = {}
        
        if 'pre_build' not in secure_buildspec['phases']:
            secure_buildspec['phases']['pre_build'] = {'commands': []}
        
        # Add secret injection commands
        secret_injection_commands = [
            '# Secure secret injection',
            'echo "Injecting secrets securely..."',
            f'SECRET_INJECTION_RESULT=$(aws lambda invoke --function-name pipeline-secret-injection-{pipeline_name}-{environment} --payload \'{{"pipeline_name":"{pipeline_name}","stage":"build","secret_configs":{json.dumps([config.__dict__ for config in secret_configs])}}}\' --output text /tmp/secret-response.json)',
            'if [ $? -ne 0 ]; then echo "Secret injection failed" && exit 1; fi',
            'SECRETS_JSON=$(cat /tmp/secret-response.json | jq -r ".body.environment_variables")',
            'if [ "$SECRETS_JSON" = "null" ]; then echo "No secrets to inject" && exit 1; fi'
        ]
        
        # Add environment variable exports
        for config in secret_configs:
            if PipelineStage.BUILD in config.required_stages:
                var_name = config.environment_variable_name
                secret_injection_commands.append(
                    f'export {var_name}=$(echo "$SECRETS_JSON" | jq -r ".{var_name}")'
                )
                
                # Add masking for logs if required
                if config.masked_in_logs:
                    secure_buildspec.setdefault('env', {}).setdefault('variables', {})[f'{var_name}_MASKED'] = 'true'
        
        # Add cleanup command
        secret_injection_commands.extend([
            'rm -f /tmp/secret-response.json',
            'echo "Secret injection completed securely"'
        ])
        
        # Prepend to existing pre_build commands
        secure_buildspec['phases']['pre_build']['commands'] = \
            secret_injection_commands + secure_buildspec['phases']['pre_build']['commands']
        
        # Add secret cleanup to post_build
        if 'post_build' not in secure_buildspec['phases']:
            secure_buildspec['phases']['post_build'] = {'commands': []}
        
        cleanup_commands = [
            '# Secure secret cleanup',
            'echo "Cleaning up secrets..."'
        ]
        
        # Unset environment variables
        for config in secret_configs:
            if PipelineStage.BUILD in config.required_stages:
                var_name = config.environment_variable_name
                cleanup_commands.append(f'unset {var_name}')
        
        cleanup_commands.append('echo "Secret cleanup completed"')
        
        # Append to existing post_build commands
        secure_buildspec['phases']['post_build']['commands'].extend(cleanup_commands)
        
        # Add security-specific environment variables
        secure_buildspec.setdefault('env', {}).setdefault('variables', {}).update({
            'SECRETS_MANAGER_ENDPOINT': f'https://secretsmanager.{self.secrets_client._client_config.region_name}.amazonaws.com',
            'SECRET_MASKING_ENABLED': 'true',
            'PIPELINE_SECURITY_MODE': 'enterprise'
        })
        
        return secure_buildspec
    
    def setup_secret_rotation_pipeline_integration(self, 
                                                  pipeline_name: str,
                                                  environment: str) -> Dict[str, Any]:
        """Set up integration between secret rotation and CI/CD pipeline"""
        
        try:
            # Create EventBridge rule for secret rotation events
            events_client = boto3.client('events')
            
            rule_name = f"secret-rotation-{pipeline_name}-{environment}"
            
            # Create rule for secret rotation completion
            rule_response = events_client.put_rule(
                Name=rule_name,
                EventPattern=json.dumps({
                    "source": ["aws.secretsmanager"],
                    "detail-type": ["AWS API Call via CloudTrail"],
                    "detail": {
                        "eventSource": ["secretsmanager.amazonaws.com"],
                        "eventName": ["RotateSecret"],
                        "responseElements": {
                            "arn": [{
                                "prefix": f"arn:aws:secretsmanager:{self.secrets_client._client_config.region_name}:*:secret:{environment}/{pipeline_name}/"
                            }]
                        }
                    }
                }),
                State='ENABLED',
                Description=f'Trigger pipeline validation when secrets rotate for {pipeline_name}'
            )
            
            # Create Lambda function to handle rotation events
            rotation_handler = self._create_rotation_event_handler(
                pipeline_name,
                environment
            )
            
            # Add Lambda as target for EventBridge rule
            events_client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': rotation_handler['FunctionArn'],
                        'InputTransformer': {
                            'InputPathsMap': {
                                'secret_arn': '$.detail.responseElements.arn',
                                'event_time': '$.time'
                            },
                            'InputTemplate': json.dumps({
                                'pipeline_name': pipeline_name,
                                'environment': environment,
                                'secret_arn': '<secret_arn>',
                                'rotation_time': '<event_time>',
                                'action': 'validate_after_rotation'
                            })
                        }
                    }
                ]
            )
            
            # Create pipeline trigger for critical secret rotations
            trigger_config = self._create_pipeline_trigger_for_rotation(
                pipeline_name,
                environment
            )
            
            return {
                'rule_arn': rule_response['RuleArn'],
                'handler_function_arn': rotation_handler['FunctionArn'],
                'trigger_pipeline_enabled': trigger_config['enabled'],
                'monitoring_enabled': True
            }
            
        except Exception as e:
            raise Exception(f"Failed to setup rotation pipeline integration: {e}")

# Usage Example
if __name__ == "__main__":
    # Initialize DevOps pipeline secrets manager
    pipeline_secrets = DevOpsPipelineSecretsManager()
    
    # Define pipeline secret configurations
    secret_configs = [
        PipelineSecretConfig(
            secret_name="prod/webapp/database-credentials",
            secret_scope=SecretScope.APPLICATION,
            required_stages=[PipelineStage.STAGING, PipelineStage.PRODUCTION],
            environment_variable_name="DATABASE_URL",
            masked_in_logs=True,
            rotation_safe=True,
            validation_required=True
        ),
        PipelineSecretConfig(
            secret_name="prod/webapp/stripe-api-key",
            secret_scope=SecretScope.APPLICATION,
            required_stages=[PipelineStage.TEST, PipelineStage.STAGING, PipelineStage.PRODUCTION],
            environment_variable_name="STRIPE_API_KEY",
            masked_in_logs=True,
            rotation_safe=True,
            validation_required=True
        ),
        PipelineSecretConfig(
            secret_name="global/docker-registry-credentials",
            secret_scope=SecretScope.GLOBAL,
            required_stages=[PipelineStage.BUILD, PipelineStage.STAGING, PipelineStage.PRODUCTION],
            environment_variable_name="DOCKER_REGISTRY_TOKEN",
            masked_in_logs=True,
            rotation_safe=False,
            validation_required=True
        )
    ]
    
    # Set up pipeline secrets framework
    framework_result = pipeline_secrets.setup_pipeline_secrets_framework(
        pipeline_name="webapp-ci-cd",
        environment="production",
        secret_configs=secret_configs
    )
    
    print(f"Pipeline secrets framework configured:")
    print(f"  Pipeline: {framework_result['pipeline_name']}")
    print(f"  Environment: {framework_result['environment']}")
    print(f"  Secrets configured: {framework_result['secrets_configured']}")
    print(f"  Build projects updated: {framework_result['build_projects_updated']}")
    
    # Create secure buildspec
    base_buildspec = {
        "version": 0.2,
        "phases": {
            "install": {
                "runtime-versions": {
                    "nodejs": 18
                }
            },
            "pre_build": {
                "commands": [
                    "echo Logging in to Amazon ECR...",
                    "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
                ]
            },
            "build": {
                "commands": [
                    "echo Build started on `date`",
                    "npm ci",
                    "npm run build",
                    "npm test"
                ]
            },
            "post_build": {
                "commands": [
                    "echo Build completed on `date`"
                ]
            }
        },
        "artifacts": {
            "files": [
                "**/*"
            ],
            "base-directory": "dist"
        }
    }
    
    secure_buildspec = pipeline_secrets.create_secure_buildspec(
        pipeline_name="webapp-ci-cd",
        environment="production",
        base_buildspec=base_buildspec,
        secret_configs=secret_configs
    )
    
    print(f"\nSecure buildspec created with {len(secret_configs)} secret injections")
    
    # Set up rotation integration
    rotation_integration = pipeline_secrets.setup_secret_rotation_pipeline_integration(
        pipeline_name="webapp-ci-cd",
        environment="production"
    )
    
    print(f"\nRotation pipeline integration configured:")
    print(f"  EventBridge rule: {rotation_integration['rule_arn']}")
    print(f"  Handler function: {rotation_integration['handler_function_arn']}")
    print(f"  Monitoring enabled: {rotation_integration['monitoring_enabled']}")
```

## Advanced Enterprise Use Cases

### Zero-Trust Security Architecture
- **Identity-Based Secret Access**: User and service identity verification
- **Just-In-Time Access**: Temporary secret access with automatic revocation
- **Network Segmentation**: VPC endpoint-based secret access
- **Continuous Verification**: Real-time access validation and monitoring

### Multi-Cloud Secret Management
- **Cross-Cloud Synchronization**: Secrets replication across AWS, Azure, GCP
- **Hybrid Deployments**: On-premises and cloud secret coordination
- **Cloud-Agnostic APIs**: Unified secret management interface
- **Migration Strategies**: Seamless cloud provider transitions

### AI-Powered Security Intelligence
- **Anomaly Detection**: ML-based unusual access pattern identification
- **Predictive Rotation**: AI-driven optimal rotation scheduling
- **Risk Scoring**: Dynamic risk assessment for secret access
- **Behavioral Analysis**: User and service behavior profiling

### Regulatory Compliance Automation
- **SOX Compliance**: Automated segregation of duties and audit trails
- **PCI DSS**: Payment card data protection automation
- **GDPR**: Privacy-preserving secret management
- **HIPAA**: Healthcare data secret protection
- **SOC 2**: Security control automation and reporting

## Enterprise DevOps Use Cases

### Application Security Management
- **Database credentials** automatic rotation without application downtime
- **API keys** centralized storage and access control for third-party integrations
- **Application secrets** secure distribution to containers and Lambda functions
- **Cross-environment management** with environment-specific secret versions

### CI/CD Pipeline Security
- **Build secrets** secure access to private repositories and registries
- **Deployment credentials** automated secret injection during deployments
- **Third-party integrations** secure storage of CI/CD tool authentication
- **Multi-environment promotion** with automated secret synchronization

### Infrastructure Automation
- **Terraform secrets** secure variable management for IaC deployments
- **Configuration management** dynamic secret injection for applications
- **Container orchestration** seamless secret mounting in ECS and EKS
- **Serverless applications** Lambda environment variable encryption

### Compliance and Governance
- **Audit trails** comprehensive logging of secret access and modifications
- **Access control** fine-grained IAM policies for secret permissions
- **Encryption** end-to-end encryption with customer-managed KMS keys
- **Compliance reporting** automated secret usage and rotation tracking

### DevOps Automation
- **Automatic rotation** for database, SSH, and API credentials
- **Zero-downtime updates** application secret rotation without restarts
- **Secret lifecycle management** automated expiration and renewal
- **Cross-service integration** with RDS, DocumentDB, and Redshift

## Core Features

### Secret Storage and Management
- **Multiple secret types** text, binary, and structured JSON secrets
- **Version control** automatic versioning with labels (AWSCURRENT, AWSPENDING)
- **Encryption** at rest and in transit using AWS KMS
- **Cross-region replication** for disaster recovery and global applications

### Automatic Rotation
- **Database rotation** built-in rotation for RDS, Aurora, DocumentDB, Redshift
- **Custom rotation** Lambda-based rotation for custom applications
- **Rotation schedules** configurable rotation intervals and windows
- **Multi-user rotation** alternating between database users for zero downtime

### Access Control and Security
- **IAM integration** resource-based and identity-based policies
- **VPC endpoints** private network access without internet connectivity
- **Resource policies** cross-account access with fine-grained controls
- **Condition keys** time-based and IP-based access restrictions

### Integration Capabilities
- **AWS SDKs** native integration across all programming languages
- **Parameter Store** seamless migration path from Systems Manager
- **ECS/EKS integration** automatic secret mounting and environment injection
- **Lambda integration** environment variable and code-based access

## Secret Types and Structure

### Database Secrets

```json
{
  "username": "admin",
  "password": "super-secret-password",
  "engine": "mysql",
  "host": "mydb.cluster-abc123.us-west-2.rds.amazonaws.com",
  "port": 3306,
  "dbname": "production"
}
```

### API Key Secrets

```json
{
  "api_key": "ak_1234567890abcdef",
  "api_secret": "as_abcdef1234567890",
  "endpoint": "https://api.example.com/v1",
  "environment": "production"
}
```

### Application Configuration

```json
{
  "database_url": "postgresql://user:pass@host:5432/db",
  "redis_url": "redis://redis.example.com:6379",
  "encryption_key": "base64-encoded-key",
  "jwt_secret": "jwt-signing-secret",
  "third_party_tokens": {
    "slack": "xoxb-token",
    "github": "ghp_token"
  }
}
```

## Practical CLI Examples

### Secret Management Operations

```bash
# Create a database secret
aws secretsmanager create-secret \
  --name "prod/myapp/database" \
  --description "Production database credentials for MyApp" \
  --secret-string '{
    "username": "dbadmin",
    "password": "MySecureP@ssw0rd123!",
    "engine": "postgres",
    "host": "myapp-prod.cluster-abc123.us-west-2.rds.amazonaws.com",
    "port": 5432,
    "dbname": "myapp_production"
  }' \
  --kms-key-id alias/secrets-manager-key \
  --tags '[
    {"Key": "Environment", "Value": "Production"},
    {"Key": "Application", "Value": "MyApp"},
    {"Key": "Owner", "Value": "DevOps"}
  ]'

# Create API key secret
aws secretsmanager create-secret \
  --name "prod/myapp/stripe-api" \
  --description "Stripe API credentials" \
  --secret-string '{
    "publishable_key": "pk_live_1234567890abcdef",
    "secret_key": "sk_live_abcdef1234567890",
    "webhook_secret": "whsec_1234567890abcdef"
  }'

# Update secret value
aws secretsmanager update-secret \
  --secret-id "prod/myapp/database" \
  --secret-string '{
    "username": "dbadmin",
    "password": "NewSecureP@ssw0rd456!",
    "engine": "postgres",
    "host": "myapp-prod.cluster-abc123.us-west-2.rds.amazonaws.com",
    "port": 5432,
    "dbname": "myapp_production"
  }'

# Put secret value with version stage
aws secretsmanager put-secret-value \
  --secret-id "prod/myapp/api-key" \
  --secret-string "new-api-key-value" \
  --version-stages AWSPENDING

# Promote pending version to current
aws secretsmanager update-secret-version-stage \
  --secret-id "prod/myapp/api-key" \
  --version-stage AWSCURRENT \
  --move-to-version-id "$(aws secretsmanager describe-secret --secret-id prod/myapp/api-key --query 'VersionIdsToStages | to_entries(@)[?value[0]==`AWSPENDING`] | [0].key' --output text)"
```

### Secret Retrieval Operations

```bash
# Get secret value
aws secretsmanager get-secret-value \
  --secret-id "prod/myapp/database" \
  --query 'SecretString' \
  --output text

# Get specific version
aws secretsmanager get-secret-value \
  --secret-id "prod/myapp/database" \
  --version-stage AWSPENDING

# Get secret metadata
aws secretsmanager describe-secret \
  --secret-id "prod/myapp/database"

# List all secrets
aws secretsmanager list-secrets \
  --filter Key="tag-key",Values="Environment" \
  --sort-order asc

# Batch retrieve secrets
aws secretsmanager batch-get-secret-value \
  --secret-id-list "prod/myapp/database" "prod/myapp/stripe-api" "prod/myapp/jwt-secret"
```

### Rotation Management

```bash
# Enable automatic rotation
aws secretsmanager rotate-secret \
  --secret-id "prod/myapp/database" \
  --rotation-lambda-arn "arn:aws:lambda:us-west-2:123456789012:function:rds-postgres-rotation" \
  --rotation-rules AutomaticallyAfterDays=30

# Configure rotation for RDS
aws secretsmanager update-secret \
  --secret-id "prod/myapp/database" \
  --rotation-lambda-arn "arn:aws:lambda:us-west-2:123456789012:function:SecretsManagerRDSPostgreSQLRotationSingleUser" \
  --rotation-rules '{
    "AutomaticallyAfterDays": 30
  }'

# Immediately rotate secret
aws secretsmanager rotate-secret \
  --secret-id "prod/myapp/database" \
  --force-rotate-immediately

# Cancel in-progress rotation
aws secretsmanager cancel-rotate-secret \
  --secret-id "prod/myapp/database"

# Get rotation status
aws secretsmanager describe-secret \
  --secret-id "prod/myapp/database" \
  --query '{
    Name: Name,
    RotationEnabled: RotationEnabled,
    RotationLambdaARN: RotationLambdaARN,
    RotationRules: RotationRules,
    LastRotatedDate: LastRotatedDate,
    NextRotationDate: NextRotationDate
  }'
```

### Access Control Management

```bash
# Set resource policy
cat > secret-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/MyAppRole"
      },
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "secretsmanager:VersionStage": "AWSCURRENT"
        }
      }
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/DevOpsRole"
      },
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws secretsmanager put-resource-policy \
  --secret-id "prod/myapp/database" \
  --resource-policy file://secret-policy.json \
  --block-public-policy

# Remove resource policy
aws secretsmanager delete-resource-policy \
  --secret-id "prod/myapp/database"

# Get resource policy
aws secretsmanager get-resource-policy \
  --secret-id "prod/myapp/database"
```

## DevOps Automation Scripts

### Secret Provisioning and Management

```bash
#!/bin/bash
# provision-secrets.sh - Automated secret provisioning for new environments

ENVIRONMENT=$1
APP_NAME=$2
CONFIG_FILE=$3

if [ $# -ne 3 ]; then
    echo "Usage: $0 <environment> <app-name> <config-file>"
    exit 1
fi

echo "Provisioning secrets for ${APP_NAME} in ${ENVIRONMENT} environment"

# Validate configuration file
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Read configuration
CONFIG=$(cat "$CONFIG_FILE")

# Create KMS key for environment if it doesn't exist
KMS_KEY_ALIAS="alias/secrets-manager-${ENVIRONMENT}"
if ! aws kms describe-key --key-id "$KMS_KEY_ALIAS" >/dev/null 2>&1; then
    echo "Creating KMS key for environment: $ENVIRONMENT"
    
    KMS_KEY_ID=$(aws kms create-key \
        --description "Secrets Manager key for ${ENVIRONMENT} environment" \
        --key-usage ENCRYPT_DECRYPT \
        --key-spec SYMMETRIC_DEFAULT \
        --query 'KeyMetadata.KeyId' \
        --output text)
    
    aws kms create-alias \
        --alias-name "$KMS_KEY_ALIAS" \
        --target-key-id "$KMS_KEY_ID"
    
    echo "Created KMS key: $KMS_KEY_ID"
fi

# Process each secret from configuration
echo "$CONFIG" | jq -r '.secrets[] | @base64' | while IFS= read -r secret_data; do
    secret_json=$(echo "$secret_data" | base64 -d)
    
    secret_name=$(echo "$secret_json" | jq -r '.name')
    secret_description=$(echo "$secret_json" | jq -r '.description')
    secret_value=$(echo "$secret_json" | jq -r '.value')
    secret_type=$(echo "$secret_json" | jq -r '.type // "string"')
    rotation_enabled=$(echo "$secret_json" | jq -r '.rotation_enabled // false')
    rotation_days=$(echo "$secret_json" | jq -r '.rotation_days // 30')
    
    # Construct full secret name
    FULL_SECRET_NAME="${ENVIRONMENT}/${APP_NAME}/${secret_name}"
    
    echo "Processing secret: $FULL_SECRET_NAME"
    
    # Check if secret exists
    if aws secretsmanager describe-secret --secret-id "$FULL_SECRET_NAME" >/dev/null 2>&1; then
        echo "Secret $FULL_SECRET_NAME already exists, updating..."
        
        aws secretsmanager update-secret \
            --secret-id "$FULL_SECRET_NAME" \
            --description "$secret_description" \
            --secret-string "$secret_value" \
            --kms-key-id "$KMS_KEY_ALIAS"
    else
        echo "Creating new secret: $FULL_SECRET_NAME"
        
        aws secretsmanager create-secret \
            --name "$FULL_SECRET_NAME" \
            --description "$secret_description" \
            --secret-string "$secret_value" \
            --kms-key-id "$KMS_KEY_ALIAS" \
            --tags "[
                {\"Key\": \"Environment\", \"Value\": \"$ENVIRONMENT\"},
                {\"Key\": \"Application\", \"Value\": \"$APP_NAME\"},
                {\"Key\": \"Type\", \"Value\": \"$secret_type\"},
                {\"Key\": \"ManagedBy\", \"Value\": \"automation\"}
            ]"
    fi
    
    # Configure rotation if enabled
    if [ "$rotation_enabled" = "true" ]; then
        echo "Configuring rotation for $FULL_SECRET_NAME"
        
        # Determine rotation function based on secret type
        case $secret_type in
            "database")
                ROTATION_FUNCTION="arn:aws:lambda:us-west-2:123456789012:function:SecretsManagerRDSPostgreSQLRotationSingleUser"
                ;;
            "api_key")
                ROTATION_FUNCTION="arn:aws:lambda:us-west-2:123456789012:function:custom-api-key-rotation"
                ;;
            *)
                echo "No rotation function available for type: $secret_type"
                continue
                ;;
        esac
        
        aws secretsmanager update-secret \
            --secret-id "$FULL_SECRET_NAME" \
            --rotation-lambda-arn "$ROTATION_FUNCTION" \
            --rotation-rules "AutomaticallyAfterDays=$rotation_days"
    fi
    
    echo "Successfully processed: $FULL_SECRET_NAME"
done

echo "Secret provisioning completed for ${APP_NAME} in ${ENVIRONMENT}"
```

### Secret Rotation Automation

```python
# secret-rotation-manager.py - Automated secret rotation management
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecretRotationManager:
    def __init__(self, region_name: str = 'us-west-2'):
        self.secrets_client = boto3.client('secretsmanager', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.sns_client = boto3.client('sns', region_name=region_name)
        
    def get_secrets_due_for_rotation(self, days_ahead: int = 7) -> List[Dict]:
        """Get secrets that are due for rotation within specified days"""
        
        secrets_due = []
        paginator = self.secrets_client.get_paginator('list_secrets')
        
        for page in paginator.paginate():
            for secret in page['SecretList']:
                if not secret.get('RotationEnabled', False):
                    continue
                
                secret_arn = secret['ARN']
                
                # Get detailed secret information
                try:
                    detail = self.secrets_client.describe_secret(SecretId=secret_arn)
                    
                    next_rotation = detail.get('NextRotationDate')
                    if next_rotation:
                        days_until_rotation = (next_rotation.date() - datetime.now().date()).days
                        
                        if days_until_rotation <= days_ahead:
                            secrets_due.append({
                                'name': detail['Name'],
                                'arn': secret_arn,
                                'next_rotation': next_rotation,
                                'days_until': days_until_rotation,
                                'rotation_lambda': detail.get('RotationLambdaARN'),
                                'rotation_rules': detail.get('RotationRules', {})
                            })
                except Exception as e:
                    logger.error(f"Error getting details for secret {secret_arn}: {e}")
        
        return sorted(secrets_due, key=lambda x: x['days_until'])
    
    def rotate_secret_safely(self, secret_arn: str, force: bool = False) -> bool:
        """Safely rotate a secret with validation and rollback capability"""
        
        try:
            logger.info(f"Starting rotation for secret: {secret_arn}")
            
            # Get current secret value for rollback
            current_secret = self.secrets_client.get_secret_value(
                SecretId=secret_arn,
                VersionStage='AWSCURRENT'
            )
            
            # Perform rotation
            response = self.secrets_client.rotate_secret(
                SecretId=secret_arn,
                ForceRotateImmediately=force
            )
            
            rotation_id = response.get('VersionId')
            logger.info(f"Rotation initiated with version ID: {rotation_id}")
            
            # Monitor rotation progress
            return self._monitor_rotation(secret_arn, rotation_id)
            
        except Exception as e:
            logger.error(f"Failed to rotate secret {secret_arn}: {e}")
            return False
    
    def _monitor_rotation(self, secret_arn: str, rotation_id: str, timeout_minutes: int = 30) -> bool:
        """Monitor rotation progress and handle failures"""
        
        import time
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.now() - start_time < timeout:
            try:
                # Check rotation status
                detail = self.secrets_client.describe_secret(SecretId=secret_arn)
                versions = detail.get('VersionIdsToStages', {})
                
                if rotation_id in versions:
                    stages = versions[rotation_id]
                    
                    if 'AWSCURRENT' in stages:
                        logger.info(f"Rotation completed successfully for {secret_arn}")
                        return True
                    elif 'AWSPENDING' in stages:
                        logger.info(f"Rotation in progress for {secret_arn}")
                    else:
                        logger.warning(f"Unexpected rotation state for {secret_arn}: {stages}")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring rotation for {secret_arn}: {e}")
                return False
        
        logger.error(f"Rotation timeout for {secret_arn}")
        return False
    
    def validate_secret_connectivity(self, secret_arn: str) -> bool:
        """Validate that applications can still connect using the rotated secret"""
        
        try:
            # Get secret details to determine type
            detail = self.secrets_client.describe_secret(SecretId=secret_arn)
            tags = {tag['Key']: tag['Value'] for tag in detail.get('Tags', [])}
            secret_type = tags.get('Type', 'unknown')
            
            # Get current secret value
            secret_value = self.secrets_client.get_secret_value(
                SecretId=secret_arn,
                VersionStage='AWSCURRENT'
            )
            
            secret_data = json.loads(secret_value['SecretString'])
            
            # Validate based on secret type
            if secret_type == 'database':
                return self._validate_database_connectivity(secret_data)
            elif secret_type == 'api_key':
                return self._validate_api_connectivity(secret_data)
            else:
                logger.warning(f"No validation method for secret type: {secret_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error validating secret connectivity for {secret_arn}: {e}")
            return False
    
    def _validate_database_connectivity(self, secret_data: Dict) -> bool:
        """Validate database connectivity"""
        
        try:
            import psycopg2  # For PostgreSQL
            # import pymysql   # For MySQL
            
            conn = psycopg2.connect(
                host=secret_data['host'],
                port=secret_data['port'],
                database=secret_data['dbname'],
                user=secret_data['username'],
                password=secret_data['password']
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            conn.close()
            return result[0] == 1
            
        except Exception as e:
            logger.error(f"Database connectivity validation failed: {e}")
            return False
    
    def _validate_api_connectivity(self, secret_data: Dict) -> bool:
        """Validate API connectivity"""
        
        try:
            import requests
            
            # Simple API health check
            endpoint = secret_data.get('endpoint', '')
            api_key = secret_data.get('api_key', '')
            
            if not endpoint or not api_key:
                logger.warning("Missing endpoint or API key for validation")
                return True
            
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get(f"{endpoint}/health", headers=headers, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"API connectivity validation failed: {e}")
            return False
    
    def generate_rotation_report(self, days_ahead: int = 30) -> Dict:
        """Generate comprehensive rotation report"""
        
        secrets_due = self.get_secrets_due_for_rotation(days_ahead)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'reporting_period_days': days_ahead,
            'total_secrets_due': len(secrets_due),
            'secrets_by_urgency': {
                'overdue': [],
                'due_today': [],
                'due_this_week': [],
                'due_this_month': []
            },
            'rotation_summary': {
                'total_enabled': 0,
                'by_type': {},
                'by_environment': {}
            }
        }
        
        # Categorize secrets by urgency
        today = datetime.now().date()
        
        for secret in secrets_due:
            days_until = secret['days_until']
            
            if days_until < 0:
                report['secrets_by_urgency']['overdue'].append(secret)
            elif days_until == 0:
                report['secrets_by_urgency']['due_today'].append(secret)
            elif days_until <= 7:
                report['secrets_by_urgency']['due_this_week'].append(secret)
            else:
                report['secrets_by_urgency']['due_this_month'].append(secret)
        
        # Get overall statistics
        paginator = self.secrets_client.get_paginator('list_secrets')
        
        for page in paginator.paginate():
            for secret in page['SecretList']:
                if secret.get('RotationEnabled', False):
                    report['rotation_summary']['total_enabled'] += 1
                    
                    # Get tags for categorization
                    try:
                        detail = self.secrets_client.describe_secret(SecretId=secret['ARN'])
                        tags = {tag['Key']: tag['Value'] for tag in detail.get('Tags', [])}
                        
                        secret_type = tags.get('Type', 'unknown')
                        environment = tags.get('Environment', 'unknown')
                        
                        report['rotation_summary']['by_type'][secret_type] = \
                            report['rotation_summary']['by_type'].get(secret_type, 0) + 1
                        
                        report['rotation_summary']['by_environment'][environment] = \
                            report['rotation_summary']['by_environment'].get(environment, 0) + 1
                            
                    except Exception as e:
                        logger.error(f"Error getting details for {secret['ARN']}: {e}")
        
        return report
    
    def send_rotation_notifications(self, report: Dict, sns_topic_arn: str):
        """Send rotation notifications"""
        
        try:
            # Prepare notification message
            overdue_count = len(report['secrets_by_urgency']['overdue'])
            due_today_count = len(report['secrets_by_urgency']['due_today'])
            due_week_count = len(report['secrets_by_urgency']['due_this_week'])
            
            message = f"""
Secret Rotation Report - {report['generated_at']}

URGENT ATTENTION REQUIRED:
- Overdue rotations: {overdue_count}
- Due today: {due_today_count}
- Due this week: {due_week_count}

Summary:
- Total secrets with rotation enabled: {report['rotation_summary']['total_enabled']}
- Secrets due within {report['reporting_period_days']} days: {report['total_secrets_due']}

Overdue Secrets:
"""
            
            for secret in report['secrets_by_urgency']['overdue']:
                message += f"- {secret['name']} (overdue by {abs(secret['days_until'])} days)\n"
            
            if not report['secrets_by_urgency']['overdue']:
                message += "None\n"
            
            # Send notification
            self.sns_client.publish(
                TopicArn=sns_topic_arn,
                Message=message,
                Subject=f"Secret Rotation Report - {overdue_count + due_today_count} urgent items"
            )
            
            logger.info("Rotation report sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send rotation notification: {e}")

def main():
    """Main rotation management workflow"""
    
    # Initialize rotation manager
    rotation_manager = SecretRotationManager()
    
    # Generate rotation report
    report = rotation_manager.generate_rotation_report(days_ahead=30)
    
    print(f"Secret Rotation Report - {report['generated_at']}")
    print(f"Total secrets due for rotation: {report['total_secrets_due']}")
    print(f"Overdue: {len(report['secrets_by_urgency']['overdue'])}")
    print(f"Due today: {len(report['secrets_by_urgency']['due_today'])}")
    print(f"Due this week: {len(report['secrets_by_urgency']['due_this_week'])}")
    
    # Send notifications if configured
    sns_topic = 'arn:aws:sns:us-west-2:123456789012:secret-rotation-alerts'
    rotation_manager.send_rotation_notifications(report, sns_topic)
    
    # Rotate overdue secrets
    for secret in report['secrets_by_urgency']['overdue']:
        print(f"Rotating overdue secret: {secret['name']}")
        success = rotation_manager.rotate_secret_safely(secret['arn'], force=True)
        
        if success:
            # Validate connectivity after rotation
            if rotation_manager.validate_secret_connectivity(secret['arn']):
                print(f"✅ Successfully rotated and validated: {secret['name']}")
            else:
                print(f"⚠️  Rotated but validation failed: {secret['name']}")
        else:
            print(f"❌ Failed to rotate: {secret['name']}")

if __name__ == "__main__":
    main()
```

### Application Secret Integration

```bash
#!/bin/bash
# inject-secrets.sh - Inject secrets into application environments

APPLICATION=$1
ENVIRONMENT=$2
OUTPUT_FORMAT=${3:-env}  # env, json, docker

if [ $# -lt 2 ]; then
    echo "Usage: $0 <application> <environment> [output-format]"
    echo "Output formats: env, json, docker"
    exit 1
fi

SECRET_PREFIX="${ENVIRONMENT}/${APPLICATION}"

echo "Retrieving secrets for ${APPLICATION} in ${ENVIRONMENT} environment"

# Get all secrets for the application
SECRETS=$(aws secretsmanager list-secrets \
    --filter Key="name",Values="${SECRET_PREFIX}/" \
    --query 'SecretList[*].Name' \
    --output text)

if [ -z "$SECRETS" ]; then
    echo "No secrets found for ${SECRET_PREFIX}/"
    exit 1
fi

case $OUTPUT_FORMAT in
    "env")
        echo "# Environment variables for ${APPLICATION} (${ENVIRONMENT})"
        echo "# Generated on $(date)"
        echo ""
        
        for secret_name in $SECRETS; do
            # Get secret value
            SECRET_VALUE=$(aws secretsmanager get-secret-value \
                --secret-id "$secret_name" \
                --query 'SecretString' \
                --output text)
            
            # Extract the key name (last part after /)
            KEY_NAME=$(echo "$secret_name" | awk -F'/' '{print $NF}' | tr '[:lower:]' '[:upper:]' | tr '-' '_')
            
            # Check if secret is JSON or plain text
            if echo "$SECRET_VALUE" | jq . >/dev/null 2>&1; then
                # JSON secret - extract each key
                echo "$SECRET_VALUE" | jq -r 'to_entries[] | "\(.key | ascii_upcase | gsub("-"; "_"))=\(.value)"'
            else
                # Plain text secret
                echo "${KEY_NAME}=${SECRET_VALUE}"
            fi
        done
        ;;
        
    "json")
        echo "{"
        FIRST=true
        
        for secret_name in $SECRETS; do
            if [ "$FIRST" = false ]; then
                echo ","
            fi
            FIRST=false
            
            SECRET_VALUE=$(aws secretsmanager get-secret-value \
                --secret-id "$secret_name" \
                --query 'SecretString' \
                --output text)
            
            KEY_NAME=$(echo "$secret_name" | awk -F'/' '{print $NF}')
            
            if echo "$SECRET_VALUE" | jq . >/dev/null 2>&1; then
                echo "  \"$KEY_NAME\": $SECRET_VALUE"
            else
                echo "  \"$KEY_NAME\": \"$SECRET_VALUE\""
            fi
        done
        
        echo ""
        echo "}"
        ;;
        
    "docker")
        echo "# Docker environment file for ${APPLICATION} (${ENVIRONMENT})"
        echo "# Usage: docker run --env-file secrets.env <image>"
        echo ""
        
        for secret_name in $SECRETS; do
            SECRET_VALUE=$(aws secretsmanager get-secret-value \
                --secret-id "$secret_name" \
                --query 'SecretString' \
                --output text)
            
            KEY_NAME=$(echo "$secret_name" | awk -F'/' '{print $NF}' | tr '[:lower:]' '[:upper:]' | tr '-' '_')
            
            if echo "$SECRET_VALUE" | jq . >/dev/null 2>&1; then
                # JSON secret - flatten for Docker env
                echo "$SECRET_VALUE" | jq -r 'to_entries[] | "\(.key | ascii_upcase | gsub("-"; "_"))=\(.value)"'
            else
                echo "${KEY_NAME}=${SECRET_VALUE}"
            fi
        done
        ;;
        
    *)
        echo "Unknown output format: $OUTPUT_FORMAT"
        echo "Supported formats: env, json, docker"
        exit 1
        ;;
esac
```

## Best Practices

### Security Best Practices
- **Encryption:** Use customer-managed KMS keys for sensitive secrets
- **Access control:** Implement least privilege IAM policies with resource-based policies
- **Network security:** Use VPC endpoints for private network access
- **Audit logging:** Enable CloudTrail for all Secrets Manager API calls
- **Secret structure:** Use JSON format for structured secrets with multiple values

### Operational Excellence
- **Naming conventions:** Use consistent hierarchical naming (environment/app/secret-type)
- **Tagging strategy:** Implement comprehensive tagging for organization and automation
- **Rotation schedules:** Align rotation with business requirements and compliance needs
- **Monitoring:** Set up CloudWatch alarms for rotation failures and access patterns
- **Documentation:** Maintain secret inventory and usage documentation

### Cost Optimization
- **Secret consolidation:** Group related secrets to minimize storage costs
- **Retention management:** Delete unused secrets and old versions
- **Cross-region replication:** Use only when necessary for disaster recovery
- **API optimization:** Cache secret values appropriately to reduce API calls
- **Lifecycle management:** Automate secret cleanup for temporary environments

### Integration Best Practices
- **Application design:** Implement secret caching with appropriate TTL
- **Error handling:** Graceful degradation when secrets are unavailable
- **Secret validation:** Verify secret format and connectivity after rotation
- **Environment separation:** Strict isolation between development, staging, and production
- **CI/CD integration:** Automate secret deployment and validation in pipelines