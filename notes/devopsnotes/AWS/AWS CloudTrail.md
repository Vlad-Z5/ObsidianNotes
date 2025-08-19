# AWS CloudTrail - Enterprise Security Monitoring & Audit Platform

AWS CloudTrail provides comprehensive logging and monitoring of AWS API calls, user activities, and resource changes for enterprise security, compliance, and operational intelligence. This advanced platform enables organizations to maintain detailed audit trails, detect security threats, and ensure regulatory compliance across multi-account environments.

## Enterprise CloudTrail Security Framework

```python
import boto3
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import gzip
import base64

class EventType(Enum):
    MANAGEMENT = "Management"
    DATA = "Data"
    INSIGHT = "Insight"

class ThreatLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityAction(Enum):
    ALERT = "ALERT"
    BLOCK = "BLOCK"
    QUARANTINE = "QUARANTINE"
    INVESTIGATE = "INVESTIGATE"

@dataclass
class SecurityEvent:
    event_id: str
    event_time: datetime
    event_name: str
    user_identity: Dict[str, Any]
    source_ip: str
    user_agent: str
    threat_level: ThreatLevel
    risk_score: float
    indicators: List[str] = field(default_factory=list)
    action_taken: Optional[SecurityAction] = None
    investigation_notes: str = ""

@dataclass
class AuditTrail:
    trail_name: str
    s3_bucket: str
    s3_key_prefix: str
    cloudwatch_log_group: str
    kms_key_id: str
    include_global_events: bool
    multi_region: bool
    event_selectors: List[Dict[str, Any]] = field(default_factory=list)
    insight_selectors: List[Dict[str, Any]] = field(default_factory=list)

class EnterpriseCloudTrailManager:
    """
    Enterprise CloudTrail manager with advanced security monitoring,
    threat detection, compliance automation, and audit trail management.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.cloudtrail_client = boto3.client('cloudtrail', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.kms_client = boto3.client('kms', region_name=region)
        self.sns_client = boto3.client('sns', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.guardduty_client = boto3.client('guardduty', region_name=region)
        self.region = region
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Security event patterns for threat detection
        self.threat_patterns = self._initialize_threat_patterns()
        
    def _initialize_threat_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize threat detection patterns"""
        
        return {
            "root_account_usage": {
                "pattern": {
                    "userIdentity.type": "Root",
                    "eventType": "AwsApiCall"
                },
                "threat_level": ThreatLevel.HIGH,
                "description": "Root account usage detected",
                "recommended_action": SecurityAction.ALERT
            },
            "console_login_without_mfa": {
                "pattern": {
                    "eventName": "ConsoleLogin",
                    "responseElements.ConsoleLogin": "Success",
                    "additionalEventData.MFAUsed": "No"
                },
                "threat_level": ThreatLevel.MEDIUM,
                "description": "Console login without MFA",
                "recommended_action": SecurityAction.ALERT
            },
            "failed_login_attempts": {
                "pattern": {
                    "eventName": "ConsoleLogin",
                    "errorCode": "SigninFailure"
                },
                "threshold": 5,
                "timeframe": 300,  # 5 minutes
                "threat_level": ThreatLevel.MEDIUM,
                "description": "Multiple failed login attempts",
                "recommended_action": SecurityAction.INVESTIGATE
            },
            "unusual_api_calls": {
                "pattern": {
                    "eventName": ["DeleteBucket", "DeleteDBInstance", "TerminateInstances"],
                    "errorCode": None
                },
                "threat_level": ThreatLevel.HIGH,
                "description": "Potentially destructive API calls",
                "recommended_action": SecurityAction.ALERT
            },
            "privilege_escalation": {
                "pattern": {
                    "eventName": ["AttachUserPolicy", "PutUserPolicy", "CreateRole", "AttachRolePolicy"],
                    "userIdentity.type": ["IAMUser", "AssumedRole"]
                },
                "threat_level": ThreatLevel.HIGH,
                "description": "Potential privilege escalation",
                "recommended_action": SecurityAction.INVESTIGATE
            },
            "unusual_location": {
                "pattern": {
                    "sourceIPAddress": "external"  # Will be enhanced with GeoIP
                },
                "threat_level": ThreatLevel.MEDIUM,
                "description": "Access from unusual geographic location",
                "recommended_action": SecurityAction.ALERT
            }
        }
    
    def setup_enterprise_audit_trail(self, 
                                   trail_config: AuditTrail,
                                   enable_insights: bool = True,
                                   enable_data_events: bool = True) -> Dict[str, Any]:
        """Setup enterprise-grade audit trail with comprehensive monitoring"""
        
        try:
            # Create S3 bucket for trail logs if it doesn't exist
            self._ensure_s3_bucket_exists(trail_config.s3_bucket)
            
            # Setup S3 bucket policy for CloudTrail
            self._setup_s3_bucket_policy(trail_config.s3_bucket)
            
            # Create KMS key for log encryption
            if not trail_config.kms_key_id:
                trail_config.kms_key_id = self._create_cloudtrail_kms_key()
            
            # Create CloudWatch log group
            self._setup_cloudwatch_log_group(trail_config.cloudwatch_log_group)
            
            # Configure trail
            trail_params = {
                'Name': trail_config.trail_name,
                'S3BucketName': trail_config.s3_bucket,
                'S3KeyPrefix': trail_config.s3_key_prefix,
                'IncludeGlobalServiceEvents': trail_config.include_global_events,
                'IsMultiRegionTrail': trail_config.multi_region,
                'EnableLogFileValidation': True,
                'KMSKeyId': trail_config.kms_key_id,
                'CloudWatchLogsLogGroupArn': f'arn:aws:logs:{self.region}:123456789012:log-group:{trail_config.cloudwatch_log_group}',
                'CloudWatchLogsRoleArn': f'arn:aws:iam::123456789012:role/CloudTrail_CloudWatchLogs_Role'
            }
            
            # Create or update trail
            try:
                self.cloudtrail_client.create_trail(**trail_params)
                self.logger.info(f"Created new trail: {trail_config.trail_name}")
            except self.cloudtrail_client.exceptions.TrailAlreadyExistsException:
                self.cloudtrail_client.update_trail(**trail_params)
                self.logger.info(f"Updated existing trail: {trail_config.trail_name}")
            
            # Configure event selectors for data events
            if enable_data_events and trail_config.event_selectors:
                self.cloudtrail_client.put_event_selectors(
                    TrailName=trail_config.trail_name,
                    EventSelectors=trail_config.event_selectors
                )
            
            # Configure insight selectors
            if enable_insights and trail_config.insight_selectors:
                self.cloudtrail_client.put_insight_selectors(
                    TrailName=trail_config.trail_name,
                    InsightSelectors=trail_config.insight_selectors
                )
            
            # Start logging
            self.cloudtrail_client.start_logging(Name=trail_config.trail_name)
            
            # Setup real-time security monitoring
            monitoring_config = self._setup_real_time_monitoring(trail_config)
            
            return {
                'status': 'success',
                'trail_name': trail_config.trail_name,
                'trail_arn': f'arn:aws:cloudtrail:{self.region}:123456789012:trail/{trail_config.trail_name}',
                's3_bucket': trail_config.s3_bucket,
                'kms_key_id': trail_config.kms_key_id,
                'cloudwatch_log_group': trail_config.cloudwatch_log_group,
                'monitoring_config': monitoring_config,
                'insights_enabled': enable_insights,
                'data_events_enabled': enable_data_events
            }
            
        except Exception as e:
            self.logger.error(f"Failed to setup audit trail: {str(e)}")
            raise
    
    def _ensure_s3_bucket_exists(self, bucket_name: str) -> None:
        """Ensure S3 bucket exists for CloudTrail logs"""
        
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except self.s3_client.exceptions.NoSuchBucket:
            # Create bucket with proper configuration
            bucket_config = {
                'Bucket': bucket_name,
                'CreateBucketConfiguration': {
                    'LocationConstraint': self.region
                } if self.region != 'us-east-1' else {}
            }
            
            if self.region == 'us-east-1':
                del bucket_config['CreateBucketConfiguration']
            
            self.s3_client.create_bucket(**bucket_config)
            
            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Enable server-side encryption
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )
            
            # Block public access
            self.s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
    
    def _setup_s3_bucket_policy(self, bucket_name: str) -> None:
        """Setup S3 bucket policy for CloudTrail"""
        
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AWSCloudTrailAclCheck",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": "s3:GetBucketAcl",
                    "Resource": f"arn:aws:s3:::{bucket_name}"
                },
                {
                    "Sid": "AWSCloudTrailWrite",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-acl": "bucket-owner-full-control"
                        }
                    }
                }
            ]
        }
        
        self.s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
    
    def _create_cloudtrail_kms_key(self) -> str:
        """Create KMS key for CloudTrail encryption"""
        
        key_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::123456789012:root"},
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow CloudTrail to encrypt logs",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": [
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey",
                        "kms:Encrypt",
                        "kms:ReEncrypt*",
                        "kms:Decrypt"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        response = self.kms_client.create_key(
            Description='CloudTrail log encryption key',
            KeyUsage='ENCRYPT_DECRYPT',
            Policy=json.dumps(key_policy)
        )
        
        key_id = response['KeyMetadata']['KeyId']
        
        # Create alias
        self.kms_client.create_alias(
            AliasName='alias/cloudtrail-logs-key',
            TargetKeyId=key_id
        )
        
        return key_id
    
    def _setup_cloudwatch_log_group(self, log_group_name: str) -> None:
        """Setup CloudWatch log group for CloudTrail"""
        
        try:
            self.logs_client.create_log_group(logGroupName=log_group_name)
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        
        # Set retention policy
        self.logs_client.put_retention_policy(
            logGroupName=log_group_name,
            retentionInDays=365
        )
    
    def _setup_real_time_monitoring(self, trail_config: AuditTrail) -> Dict[str, Any]:
        """Setup real-time security monitoring and alerting"""
        
        # Create CloudWatch metric filters for security events
        metric_filters = []
        
        for pattern_name, pattern_config in self.threat_patterns.items():
            filter_name = f"security-{pattern_name}"
            filter_pattern = self._convert_to_cloudwatch_filter(pattern_config['pattern'])
            
            try:
                self.logs_client.put_metric_filter(
                    logGroupName=trail_config.cloudwatch_log_group,
                    filterName=filter_name,
                    filterPattern=filter_pattern,
                    metricTransformations=[
                        {
                            'metricName': f'CloudTrail-{pattern_name}',
                            'metricNamespace': 'Security/CloudTrail',
                            'metricValue': '1',
                            'defaultValue': 0
                        }
                    ]
                )
                
                metric_filters.append({
                    'name': filter_name,
                    'pattern': filter_pattern,
                    'threat_level': pattern_config['threat_level'].value
                })
                
            except Exception as e:
                self.logger.error(f"Failed to create metric filter {filter_name}: {str(e)}")
        
        return {
            'metric_filters_created': len(metric_filters),
            'metric_filters': metric_filters,
            'real_time_processing': True
        }
    
    def _convert_to_cloudwatch_filter(self, pattern: Dict[str, Any]) -> str:
        """Convert threat pattern to CloudWatch Logs filter pattern"""
        
        filter_parts = []
        
        for key, value in pattern.items():
            if isinstance(value, list):
                value_patterns = ' || '.join([f'$.{key} = "{v}"' for v in value])
                filter_parts.append(f'({value_patterns})')
            elif value is None:
                filter_parts.append(f'!EXISTS($.{key})')
            else:
                filter_parts.append(f'$.{key} = "{value}"')
        
        return '{ ' + ' && '.join(filter_parts) + ' }'

class SecurityAnalyticsEngine:
    """
    Advanced security analytics engine for CloudTrail log analysis,
    threat detection, and automated incident response.
    """
    
    def __init__(self, cloudtrail_manager: EnterpriseCloudTrailManager):
        self.cloudtrail_manager = cloudtrail_manager
        self.threat_intelligence = ThreatIntelligenceEngine()
        
    def analyze_security_events(self, 
                              start_time: datetime,
                              end_time: datetime,
                              event_filters: Optional[Dict[str, Any]] = None) -> List[SecurityEvent]:
        """Analyze CloudTrail events for security threats"""
        
        events = self._fetch_cloudtrail_events(start_time, end_time, event_filters)
        security_events = []
        
        for event in events:
            # Analyze each event for security indicators
            threat_analysis = self._analyze_event_for_threats(event)
            
            if threat_analysis['is_threat']:
                security_event = SecurityEvent(
                    event_id=event.get('EventId', ''),
                    event_time=datetime.fromisoformat(event['EventTime'].replace('Z', '+00:00')),
                    event_name=event.get('EventName', ''),
                    user_identity=event.get('UserIdentity', {}),
                    source_ip=event.get('SourceIPAddress', ''),
                    user_agent=event.get('UserAgent', ''),
                    threat_level=threat_analysis['threat_level'],
                    risk_score=threat_analysis['risk_score'],
                    indicators=threat_analysis['indicators']
                )
                
                security_events.append(security_event)
        
        # Sort by risk score (highest first)
        security_events.sort(key=lambda x: x.risk_score, reverse=True)
        
        return security_events
    
    def _fetch_cloudtrail_events(self, 
                                start_time: datetime,
                                end_time: datetime,
                                filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch CloudTrail events for analysis"""
        
        lookup_attributes = []
        if filters:
            for key, value in filters.items():
                lookup_attributes.append({
                    'AttributeKey': key,
                    'AttributeValue': value
                })
        
        events = []
        next_token = None
        
        while True:
            params = {
                'StartTime': start_time,
                'EndTime': end_time,
                'MaxItems': 50
            }
            
            if lookup_attributes:
                params['LookupAttributes'] = lookup_attributes
            
            if next_token:
                params['NextToken'] = next_token
            
            response = self.cloudtrail_manager.cloudtrail_client.lookup_events(**params)
            
            events.extend(response.get('Events', []))
            
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        return events
    
    def _analyze_event_for_threats(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual event for threat indicators"""
        
        threat_score = 0
        indicators = []
        threat_level = ThreatLevel.LOW
        
        # Check against known threat patterns
        for pattern_name, pattern_config in self.cloudtrail_manager.threat_patterns.items():
            if self._matches_pattern(event, pattern_config['pattern']):
                threat_score += self._get_threat_score(pattern_config['threat_level'])
                indicators.append(pattern_config['description'])
                
                if pattern_config['threat_level'].value > threat_level.value:
                    threat_level = pattern_config['threat_level']
        
        # Additional threat intelligence checks
        threat_intel_score = self.threat_intelligence.check_indicators(event)
        threat_score += threat_intel_score
        
        # Behavioral analysis
        behavioral_score = self._analyze_behavioral_patterns(event)
        threat_score += behavioral_score
        
        # Normalize risk score (0-100)
        risk_score = min(threat_score * 10, 100)
        
        return {
            'is_threat': threat_score > 0,
            'threat_level': threat_level,
            'risk_score': risk_score,
            'indicators': indicators
        }
    
    def _matches_pattern(self, event: Dict[str, Any], pattern: Dict[str, Any]) -> bool:
        """Check if event matches threat pattern"""
        
        for key, expected_value in pattern.items():
            event_value = self._get_nested_value(event, key)
            
            if isinstance(expected_value, list):
                if event_value not in expected_value:
                    return False
            elif expected_value is None:
                if event_value is not None:
                    return False
            else:
                if event_value != expected_value:
                    return False
        
        return True
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def _get_threat_score(self, threat_level: ThreatLevel) -> int:
        """Get numeric threat score from threat level"""
        
        scores = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.HIGH: 7,
            ThreatLevel.CRITICAL: 10
        }
        
        return scores.get(threat_level, 0)
    
    def _analyze_behavioral_patterns(self, event: Dict[str, Any]) -> int:
        """Analyze event for behavioral anomalies"""
        
        behavioral_score = 0
        
        # Check for unusual timing patterns
        event_time = datetime.fromisoformat(event['EventTime'].replace('Z', '+00:00'))
        if event_time.hour < 6 or event_time.hour > 22:  # Outside business hours
            behavioral_score += 1
        
        # Check for unusual source IP patterns
        source_ip = event.get('SourceIPAddress', '')
        if self._is_suspicious_ip(source_ip):
            behavioral_score += 2
        
        # Check for unusual user agent patterns
        user_agent = event.get('UserAgent', '')
        if self._is_suspicious_user_agent(user_agent):
            behavioral_score += 1
        
        return behavioral_score
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        
        # This would typically integrate with threat intelligence feeds
        # For now, simple checks for common patterns
        suspicious_patterns = [
            'tor-exit',
            'proxy',
            'vpn'
        ]
        
        return any(pattern in ip_address.lower() for pattern in suspicious_patterns)
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        
        suspicious_agents = [
            'curl',
            'wget',
            'python-requests',
            'boto3'
        ]
        
        return any(agent in user_agent.lower() for agent in suspicious_agents)

class ThreatIntelligenceEngine:
    """
    Threat intelligence engine for enriching security events
    with external threat intelligence data.
    """
    
    def __init__(self):
        self.threat_feeds = self._initialize_threat_feeds()
    
    def _initialize_threat_feeds(self) -> Dict[str, Any]:
        """Initialize threat intelligence feeds"""
        
        return {
            'malicious_ips': set(),
            'suspicious_domains': set(),
            'known_attack_patterns': [],
            'iocs': []  # Indicators of Compromise
        }
    
    def check_indicators(self, event: Dict[str, Any]) -> int:
        """Check event against threat intelligence indicators"""
        
        score = 0
        
        # Check source IP against threat feeds
        source_ip = event.get('SourceIPAddress', '')
        if source_ip in self.threat_feeds['malicious_ips']:
            score += 5
        
        # Check for known attack patterns
        event_name = event.get('EventName', '')
        for pattern in self.threat_feeds['known_attack_patterns']:
            if pattern in event_name:
                score += 3
        
        return score

# DevOps Integration Pipeline
class CloudTrailDevOpsPipeline:
    """
    DevOps pipeline integration for CloudTrail with automated security
    monitoring, compliance validation, and incident response.
    """
    
    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.cloudtrail_manager = EnterpriseCloudTrailManager()
        self.security_engine = SecurityAnalyticsEngine(self.cloudtrail_manager)
        
    def create_security_automation_pipeline(self, 
                                          trail_config: AuditTrail,
                                          alert_channels: List[str]) -> Dict[str, Any]:
        """Create automated security monitoring pipeline"""
        
        pipeline_config = {
            'pipeline_name': self.pipeline_name,
            'trail_config': trail_config,
            'alert_channels': alert_channels,
            'automation_functions': [],
            'security_rules': []
        }
        
        # Setup CloudTrail
        trail_result = self.cloudtrail_manager.setup_enterprise_audit_trail(trail_config)
        
        # Create Lambda functions for real-time processing
        processing_functions = self._create_processing_functions(trail_config)
        pipeline_config['automation_functions'] = processing_functions
        
        # Setup EventBridge rules for automated response
        event_rules = self._create_event_rules(trail_config, alert_channels)
        pipeline_config['security_rules'] = event_rules
        
        # Create security dashboards
        dashboard_config = self._create_security_dashboards()
        pipeline_config['dashboards'] = dashboard_config
        
        return pipeline_config
    
    def _create_processing_functions(self, trail_config: AuditTrail) -> List[Dict[str, Any]]:
        """Create Lambda functions for log processing"""
        
        functions = []
        
        # Real-time threat detection function
        threat_detection_function = {
            'function_name': f'{self.pipeline_name}-threat-detection',
            'runtime': 'python3.9',
            'handler': 'lambda_function.lambda_handler',
            'code': self._generate_threat_detection_code(),
            'environment': {
                'LOG_GROUP': trail_config.cloudwatch_log_group,
                'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:security-alerts'
            },
            'trigger': {
                'type': 'CloudWatch Logs',
                'log_group': trail_config.cloudwatch_log_group
            }
        }
        
        functions.append(threat_detection_function)
        
        # Compliance validation function
        compliance_function = {
            'function_name': f'{self.pipeline_name}-compliance-check',
            'runtime': 'python3.9',
            'handler': 'lambda_function.lambda_handler',
            'code': self._generate_compliance_code(),
            'environment': {
                'TRAIL_NAME': trail_config.trail_name,
                'COMPLIANCE_BUCKET': 'compliance-reports-bucket'
            },
            'trigger': {
                'type': 'CloudWatch Events',
                'schedule': 'rate(1 hour)'
            }
        }
        
        functions.append(compliance_function)
        
        return functions
    
    def _generate_threat_detection_code(self) -> str:
        """Generate Lambda function code for threat detection"""
        
        return '''
import json
import boto3
import gzip
import base64
from datetime import datetime

def lambda_handler(event, context):
    """Real-time threat detection from CloudTrail logs"""
    
    # Parse CloudWatch Logs event
    cw_data = event['awslogs']['data']
    compressed_payload = base64.b64decode(cw_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    log_data = json.loads(uncompressed_payload)
    
    sns_client = boto3.client('sns')
    
    threats_detected = []
    
    for log_event in log_data['logEvents']:
        try:
            cloudtrail_event = json.loads(log_event['message'])
            
            # Analyze for threats
            threat_result = analyze_event_for_threats(cloudtrail_event)
            
            if threat_result['is_threat']:
                threats_detected.append({
                    'event_id': cloudtrail_event.get('eventID'),
                    'event_name': cloudtrail_event.get('eventName'),
                    'user_identity': cloudtrail_event.get('userIdentity', {}),
                    'source_ip': cloudtrail_event.get('sourceIPAddress'),
                    'threat_level': threat_result['threat_level'],
                    'risk_score': threat_result['risk_score'],
                    'timestamp': cloudtrail_event.get('eventTime')
                })
                
        except Exception as e:
            print(f"Error processing log event: {str(e)}")
            continue
    
    # Send alerts for detected threats
    if threats_detected:
        alert_message = {
            'alert_type': 'CloudTrail Security Alert',
            'timestamp': datetime.utcnow().isoformat(),
            'threats_count': len(threats_detected),
            'threats': threats_detected
        }
        
        sns_client.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=json.dumps(alert_message, indent=2),
            Subject=f'Security Alert: {len(threats_detected)} threats detected'
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'threats_detected': len(threats_detected),
            'processed_events': len(log_data['logEvents'])
        })
    }

def analyze_event_for_threats(event):
    """Analyze CloudTrail event for security threats"""
    
    threat_patterns = {
        'root_usage': event.get('userIdentity', {}).get('type') == 'Root',
        'console_without_mfa': (
            event.get('eventName') == 'ConsoleLogin' and
            event.get('responseElements', {}).get('ConsoleLogin') == 'Success' and
            event.get('additionalEventData', {}).get('MFAUsed') == 'No'
        ),
        'destructive_actions': event.get('eventName') in [
            'DeleteBucket', 'DeleteDBInstance', 'TerminateInstances'
        ]
    }
    
    threat_level = 'LOW'
    risk_score = 0
    
    if threat_patterns['root_usage']:
        threat_level = 'HIGH'
        risk_score += 70
    
    if threat_patterns['console_without_mfa']:
        threat_level = 'MEDIUM'
        risk_score += 50
        
    if threat_patterns['destructive_actions']:
        threat_level = 'HIGH'
        risk_score += 80
    
    return {
        'is_threat': any(threat_patterns.values()),
        'threat_level': threat_level,
        'risk_score': min(risk_score, 100)
    }
        '''
    
    def _generate_compliance_code(self) -> str:
        """Generate Lambda function code for compliance checking"""
        
        return '''
import json
import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    """Automated compliance checking for CloudTrail"""
    
    cloudtrail = boto3.client('cloudtrail')
    s3 = boto3.client('s3')
    
    trail_name = os.environ['TRAIL_NAME']
    compliance_bucket = os.environ['COMPLIANCE_BUCKET']
    
    compliance_checks = []
    
    # Check trail status
    trail_status = cloudtrail.get_trail_status(Name=trail_name)
    compliance_checks.append({
        'check': 'Trail Logging Status',
        'status': 'PASS' if trail_status['IsLogging'] else 'FAIL',
        'details': f"Logging: {trail_status['IsLogging']}"
    })
    
    # Check log file validation
    trail_info = cloudtrail.describe_trails(trailNameList=[trail_name])
    log_validation = trail_info['trailList'][0].get('LogFileValidationEnabled', False)
    compliance_checks.append({
        'check': 'Log File Validation',
        'status': 'PASS' if log_validation else 'FAIL',
        'details': f"Validation Enabled: {log_validation}"
    })
    
    # Check encryption
    kms_key = trail_info['trailList'][0].get('KMSKeyId')
    compliance_checks.append({
        'check': 'Log Encryption',
        'status': 'PASS' if kms_key else 'FAIL',
        'details': f"KMS Key: {kms_key or 'Not configured'}"
    })
    
    # Generate compliance report
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'trail_name': trail_name,
        'compliance_checks': compliance_checks,
        'overall_status': 'PASS' if all(c['status'] == 'PASS' for c in compliance_checks) else 'FAIL'
    }
    
    # Store report in S3
    report_key = f"compliance-reports/{datetime.utcnow().strftime('%Y/%m/%d')}/cloudtrail-compliance-{datetime.utcnow().strftime('%H%M%S')}.json"
    
    s3.put_object(
        Bucket=compliance_bucket,
        Key=report_key,
        Body=json.dumps(report, indent=2),
        ContentType='application/json'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'report_generated': True,
            'report_location': f"s3://{compliance_bucket}/{report_key}",
            'overall_status': report['overall_status'],
            'checks_count': len(compliance_checks)
        })
    }
        '''
    
    def _create_event_rules(self, 
                           trail_config: AuditTrail,
                           alert_channels: List[str]) -> List[Dict[str, Any]]:
        """Create EventBridge rules for automated response"""
        
        rules = []
        
        # High-severity security event rule
        security_rule = {
            'rule_name': f'{self.pipeline_name}-high-severity-events',
            'event_pattern': {
                'source': ['aws.cloudtrail'],
                'detail-type': ['AWS API Call via CloudTrail'],
                'detail': {
                    'eventName': [
                        'DeleteBucket',
                        'DeleteDBInstance',
                        'TerminateInstances',
                        'DeleteUser',
                        'DeleteRole'
                    ]
                }
            },
            'targets': alert_channels
        }
        
        rules.append(security_rule)
        
        # Failed authentication rule
        auth_rule = {
            'rule_name': f'{self.pipeline_name}-failed-auth',
            'event_pattern': {
                'source': ['aws.cloudtrail'],
                'detail-type': ['AWS Console Sign In via CloudTrail'],
                'detail': {
                    'responseElements': {
                        'ConsoleLogin': ['Failure']
                    }
                }
            },
            'targets': alert_channels
        }
        
        rules.append(auth_rule)
        
        return rules
    
    def _create_security_dashboards(self) -> Dict[str, Any]:
        """Create CloudWatch dashboards for security monitoring"""
        
        dashboard_config = {
            'dashboard_name': f'{self.pipeline_name}-security-dashboard',
            'widgets': [
                {
                    'type': 'metric',
                    'properties': {
                        'metrics': [
                            ['Security/CloudTrail', 'CloudTrail-root_account_usage'],
                            ['.', 'CloudTrail-console_login_without_mfa'],
                            ['.', 'CloudTrail-failed_login_attempts'],
                            ['.', 'CloudTrail-unusual_api_calls']
                        ],
                        'period': 300,
                        'stat': 'Sum',
                        'region': 'us-east-1',
                        'title': 'Security Events Overview'
                    }
                },
                {
                    'type': 'log',
                    'properties': {
                        'query': '''
                        SOURCE '/aws/cloudtrail/security-trail'
                        | fields @timestamp, eventName, userIdentity.type, sourceIPAddress
                        | filter eventName like /Delete|Terminate|Remove/
                        | sort @timestamp desc
                        | limit 100
                        ''',
                        'region': 'us-east-1',
                        'title': 'Recent Destructive Actions'
                    }
                }
            ]
        }
        
        return dashboard_config

# CLI Usage Examples
if __name__ == "__main__":
    # Initialize enterprise CloudTrail manager
    trail_mgr = EnterpriseCloudTrailManager(region='us-east-1')
    
    # Create audit trail configuration
    audit_trail = AuditTrail(
        trail_name='enterprise-security-trail',
        s3_bucket='enterprise-cloudtrail-logs',
        s3_key_prefix='security-logs/',
        cloudwatch_log_group='enterprise-cloudtrail',
        kms_key_id='',  # Will be created automatically
        include_global_events=True,
        multi_region=True,
        event_selectors=[
            {
                'ReadWriteType': 'All',
                'IncludeManagementEvents': True,
                'DataResources': [
                    {
                        'Type': 'AWS::S3::Object',
                        'Values': ['arn:aws:s3:::sensitive-data-bucket/*']
                    }
                ]
            }
        ],
        insight_selectors=[
            {
                'InsightType': 'ApiCallRateInsight'
            }
        ]
    )
    
    # Setup enterprise audit trail
    trail_result = trail_mgr.setup_enterprise_audit_trail(
        trail_config=audit_trail,
        enable_insights=True,
        enable_data_events=True
    )
    
    # Initialize security analytics
    security_engine = SecurityAnalyticsEngine(trail_mgr)
    
    # Analyze recent security events
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    security_events = security_engine.analyze_security_events(
        start_time=start_time,
        end_time=end_time
    )
    
    # Setup DevOps pipeline
    pipeline = CloudTrailDevOpsPipeline('production-security')
    pipeline_config = pipeline.create_security_automation_pipeline(
        trail_config=audit_trail,
        alert_channels=['arn:aws:sns:us-east-1:123456789012:security-alerts']
    )
    
    print(f"Enterprise CloudTrail setup completed with {len(security_events)} security events detected")
```

## Advanced Multi-Account CloudTrail Architecture

```python
class MultiAccountCloudTrailManager:
    """
    Enterprise multi-account CloudTrail management with centralized logging,
    cross-account security monitoring, and compliance aggregation.
    """
    
    def __init__(self, management_account_id: str, regions: List[str]):
        self.management_account_id = management_account_id
        self.regions = regions
        self.trail_managers = {}
        
        # Initialize trail managers for each region
        for region in regions:
            self.trail_managers[region] = EnterpriseCloudTrailManager(region)
    
    def setup_organization_wide_logging(self, 
                                       member_accounts: List[str],
                                       central_logging_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup organization-wide CloudTrail logging"""
        
        results = {}
        
        for region in self.regions:
            trail_mgr = self.trail_managers[region]
            
            # Create organization trail
            org_trail_config = AuditTrail(
                trail_name=f'organization-trail-{region}',
                s3_bucket=central_logging_config['s3_bucket'],
                s3_key_prefix=f'organization-logs/{region}/',
                cloudwatch_log_group=f'organization-cloudtrail-{region}',
                kms_key_id=central_logging_config.get('kms_key_id'),
                include_global_events=(region == 'us-east-1'),  # Only one region for global events
                multi_region=True
            )
            
            try:
                trail_result = trail_mgr.setup_enterprise_audit_trail(
                    trail_config=org_trail_config,
                    enable_insights=True,
                    enable_data_events=True
                )
                
                # Enable organization trail
                trail_mgr.cloudtrail_client.put_trail(
                    Name=org_trail_config.trail_name,
                    S3BucketName=org_trail_config.s3_bucket,
                    S3KeyPrefix=org_trail_config.s3_key_prefix,
                    IsOrganizationTrail=True
                )
                
                results[region] = {
                    'status': 'success',
                    'trail_name': org_trail_config.trail_name,
                    'trail_result': trail_result
                }
                
            except Exception as e:
                results[region] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results

# Real-world Enterprise Use Cases

## Use Case 1: Financial Services Security Monitoring
"""
Large investment bank implements comprehensive CloudTrail monitoring
across 200+ AWS accounts with real-time threat detection and compliance.

Key Requirements:
- Real-time security event monitoring
- PCI-DSS and SOX compliance logging
- Multi-region audit trail aggregation
- Automated incident response
- Forensic analysis capabilities
- Regulatory reporting automation
"""

## Use Case 2: Healthcare HIPAA Audit Trails
"""
Healthcare organization maintains detailed HIPAA audit trails with
automated compliance checking and breach detection capabilities.

Key Requirements:
- PHI access tracking and auditing
- HIPAA compliance monitoring
- Automated breach detection
- Forensic investigation support
- Compliance reporting for audits
- Data retention and lifecycle management
"""

## Use Case 3: Government Security Operations
"""
Government agency implements enterprise security monitoring with
advanced threat detection and incident response automation.

Key Requirements:
- FedRAMP compliance monitoring
- Advanced persistent threat (APT) detection
- Insider threat monitoring
- Automated security response
- Cross-agency log sharing
- SIEM integration and analysis
"""

# Advanced CloudTrail Integration Patterns

## Pattern 1: CloudTrail + GuardDuty Integration
cloudtrail_guardduty_integration = """
# Enhanced threat detection combining CloudTrail and GuardDuty
# for comprehensive security monitoring

def integrate_cloudtrail_with_guardduty():
    import boto3
    
    cloudtrail = boto3.client('cloudtrail')
    guardduty = boto3.client('guardduty')
    
    # Get existing GuardDuty detector
    detectors = guardduty.list_detectors()
    detector_id = detectors['DetectorIds'][0]
    
    # Create threat intelligence set from CloudTrail data
    threat_intel_set = guardduty.create_threat_intel_set(
        DetectorId=detector_id,
        Name='CloudTrail-Threat-Intelligence',
        Format='TXT',
        Location='s3://threat-intelligence-bucket/indicators.txt',
        Activate=True
    )
    
    # Create finding filter for CloudTrail events
    finding_filter = guardduty.create_filter(
        DetectorId=detector_id,
        Name='CloudTrail-High-Risk-Events',
        FindingCriteria={
            'Criterion': {
                'service.serviceName': {'Eq': ['cloudtrail']},
                'severity': {'Gte': 7.0}
            }
        },
        Action='ARCHIVE'  # or 'NOOP' to keep findings
    )
"""

## Pattern 2: CloudTrail + SIEM Integration
cloudtrail_siem_integration = """
# Automated CloudTrail log forwarding to SIEM systems
# for advanced security analytics

def setup_siem_integration():
    import boto3
    
    kinesis = boto3.client('kinesis')
    
    # Create Kinesis stream for SIEM integration
    stream_config = {
        'StreamName': 'cloudtrail-siem-stream',
        'ShardCount': 5,
        'StreamModeDetails': {
            'StreamMode': 'PROVISIONED'
        }
    }
    
    kinesis.create_stream(**stream_config)
    
    # Create Kinesis Firehose for SIEM delivery
    firehose_config = {
        'DeliveryStreamName': 'cloudtrail-to-siem',
        'DeliveryStreamType': 'DirectPut',
        'ExtendedS3DestinationConfiguration': {
            'RoleARN': 'arn:aws:iam::123456789012:role/firehose-delivery-role',
            'BucketARN': 'arn:aws:s3:::siem-integration-bucket',
            'Prefix': 'cloudtrail-logs/',
            'BufferingHints': {
                'SizeInMBs': 5,
                'IntervalInSeconds': 300
            },
            'CompressionFormat': 'GZIP',
            'DataFormatConversionConfiguration': {
                'Enabled': True,
                'OutputFormatConfiguration': {
                    'Serializer': {
                        'ParquetSerDe': {}
                    }
                }
            }
        }
    }
    
    boto3.client('firehose').create_delivery_stream(**firehose_config)
"""

## DevOps Best Practices

### 1. Infrastructure as Code
- Deploy CloudTrail via CloudFormation/CDK
- Version control trail configurations
- Automated testing of log processing
- Blue-green deployment of monitoring changes

### 2. Security Automation
- Real-time threat detection and response
- Automated incident escalation
- Security playbook automation
- Threat intelligence integration

### 3. Compliance Management
- Automated compliance checking
- Regulatory reporting automation
- Audit trail preservation
- Data retention policy enforcement

### 4. Cost Optimization
- Log lifecycle management
- Intelligent data tiering
- Cost allocation and chargeback
- Resource optimization recommendations

This enterprise AWS CloudTrail framework provides comprehensive security monitoring, threat detection, compliance automation, and seamless DevOps integration for organizations requiring advanced audit capabilities and security operations at scale.