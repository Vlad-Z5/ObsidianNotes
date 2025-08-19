# AWS WAF - Enterprise Web Application Security Platform

Web Application Firewall to protect web applications from common exploits at Layer 7, enhanced with enterprise automation, advanced threat detection, and comprehensive DevOps integration.

## Core Features & Components

- **Multi-platform protection:** ALB, API Gateway, CloudFront, AppSync, Cognito
- **Comprehensive rule engine:** IP, headers, body, URI, query strings, and geo-location filtering
- **AWS Managed Rule Groups:** Pre-configured rules for OWASP Top 10, known bad inputs, and bot control
- **Custom security rules:** Tailored protection for specific application needs
- **Rate-based rules:** Automatic IP blocking for DDoS and brute force protection
- **Bot Control & CAPTCHA:** Advanced bot detection and mitigation capabilities
- **Web ACL management:** Centralized policy configuration and deployment
- **Real-time logging & metrics:** CloudWatch, Kinesis, and S3 integration for monitoring
- **Threat intelligence integration:** IP reputation lists and geographic blocking
- **Rule testing & tuning:** Automated rule optimization and false positive reduction

## Enterprise WAF Security Automation Framework

```python
import json
import boto3
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
import time
import uuid

class RuleAction(Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    COUNT = "COUNT"
    CAPTCHA = "CAPTCHA"
    CHALLENGE = "CHALLENGE"

class ResourceType(Enum):
    CLOUDFRONT = "CLOUDFRONT"
    APPLICATION_LOAD_BALANCER = "APPLICATION_LOAD_BALANCER"
    API_GATEWAY = "API_GATEWAY"
    APPSYNC = "APPSYNC"
    COGNITO_USER_POOL = "COGNITO_USER_POOL"

class ManagedRuleGroupVendor(Enum):
    AWS = "AWS"
    MARKETPLACE = "MARKETPLACE"

class LogDestinationType(Enum):
    S3 = "s3"
    CLOUDWATCH_LOGS = "cloudwatch_logs"
    KINESIS_DATA_FIREHOSE = "kinesis_data_firehose"

@dataclass
class WAFRule:
    name: str
    priority: int
    action: RuleAction
    statement: Dict[str, Any]
    visibility_config: Dict[str, Any]
    rule_labels: List[str] = field(default_factory=list)
    captcha_config: Optional[Dict[str, Any]] = None
    challenge_config: Optional[Dict[str, Any]] = None

@dataclass
class ManagedRuleGroup:
    vendor_name: str
    name: str
    version: Optional[str] = None
    excluded_rules: List[str] = field(default_factory=list)
    scope_down_statement: Optional[Dict[str, Any]] = None
    managed_rule_group_configs: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class WebACL:
    name: str
    scope: str  # CLOUDFRONT or REGIONAL
    description: str
    rules: List[WAFRule] = field(default_factory=list)
    managed_rule_groups: List[ManagedRuleGroup] = field(default_factory=list)
    default_action: RuleAction = RuleAction.ALLOW
    tags: Dict[str, str] = field(default_factory=dict)
    custom_response_bodies: Dict[str, Dict[str, str]] = field(default_factory=dict)
    captcha_config: Optional[Dict[str, Any]] = None
    challenge_config: Optional[Dict[str, Any]] = None

@dataclass
class LoggingConfiguration:
    resource_arn: str
    log_destination_configs: List[str]
    redacted_fields: List[Dict[str, Any]] = field(default_factory=list)
    managed_by_firewall_manager: bool = False
    logging_filter: Optional[Dict[str, Any]] = None

class EnterpriseWAFManager:
    """
    Enterprise AWS WAF manager with automated security rule deployment,
    threat detection, and comprehensive protection management.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.wafv2 = boto3.client('wafv2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.region = region
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('WAFManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def create_enterprise_web_acl(self, web_acl_config: WebACL) -> Dict[str, Any]:
        """Create enterprise Web ACL with comprehensive security rules"""
        try:
            # Build rules list
            rules = []
            
            # Add managed rule groups
            priority = 0
            for managed_group in web_acl_config.managed_rule_groups:
                priority += 1
                managed_rule = {
                    'Name': f"{managed_group.vendor_name}-{managed_group.name}",
                    'Priority': priority,
                    'OverrideAction': {'None': {}},
                    'Statement': {
                        'ManagedRuleGroupStatement': {
                            'VendorName': managed_group.vendor_name,
                            'Name': managed_group.name
                        }
                    },
                    'VisibilityConfig': {
                        'SampledRequestsEnabled': True,
                        'CloudWatchMetricsEnabled': True,
                        'MetricName': f"{managed_group.vendor_name}{managed_group.name}"
                    }
                }
                
                # Add version if specified
                if managed_group.version:
                    managed_rule['Statement']['ManagedRuleGroupStatement']['Version'] = managed_group.version
                
                # Add excluded rules
                if managed_group.excluded_rules:
                    managed_rule['Statement']['ManagedRuleGroupStatement']['ExcludedRules'] = [
                        {'Name': rule} for rule in managed_group.excluded_rules
                    ]
                
                # Add scope down statement
                if managed_group.scope_down_statement:
                    managed_rule['Statement']['ManagedRuleGroupStatement']['ScopeDownStatement'] = managed_group.scope_down_statement
                
                # Add rule group configs
                if managed_group.managed_rule_group_configs:
                    managed_rule['Statement']['ManagedRuleGroupStatement']['ManagedRuleGroupConfigs'] = managed_group.managed_rule_group_configs
                
                rules.append(managed_rule)
            
            # Add custom rules
            for rule in web_acl_config.rules:
                priority += 1
                custom_rule = {
                    'Name': rule.name,
                    'Priority': priority,
                    'Action': {rule.action.value: {}},
                    'Statement': rule.statement,
                    'VisibilityConfig': rule.visibility_config
                }
                
                # Add rule labels
                if rule.rule_labels:
                    custom_rule['RuleLabels'] = [{'Name': label} for label in rule.rule_labels]
                
                # Add CAPTCHA config
                if rule.action == RuleAction.CAPTCHA and rule.captcha_config:
                    custom_rule['CaptchaConfig'] = rule.captcha_config
                
                # Add Challenge config
                if rule.action == RuleAction.CHALLENGE and rule.challenge_config:
                    custom_rule['ChallengeConfig'] = rule.challenge_config
                
                rules.append(custom_rule)
            
            # Create Web ACL
            response = self.wafv2.create_web_acl(
                Name=web_acl_config.name,
                Scope=web_acl_config.scope,
                DefaultAction={web_acl_config.default_action.value: {}},
                Description=web_acl_config.description,
                Rules=rules,
                VisibilityConfig={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': web_acl_config.name
                },
                Tags=[
                    {'Key': k, 'Value': v} 
                    for k, v in web_acl_config.tags.items()
                ],
                CustomResponseBodies=web_acl_config.custom_response_bodies,
                CaptchaConfig=web_acl_config.captcha_config,
                ChallengeConfig=web_acl_config.challenge_config
            )
            
            self.logger.info(f"Created Web ACL: {web_acl_config.name}")
            
            return {
                'web_acl_name': web_acl_config.name,
                'web_acl_id': response['Summary']['Id'],
                'web_acl_arn': response['Summary']['ARN'],
                'lock_token': response['Summary']['LockToken'],
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating Web ACL: {str(e)}")
            raise

    def create_rate_limiting_rules(self, base_rate: int = 2000, 
                                  strict_rate: int = 100) -> List[WAFRule]:
        """Create comprehensive rate limiting rules"""
        rules = []
        
        # General rate limiting
        general_rate_rule = WAFRule(
            name="GeneralRateLimiting",
            priority=1,
            action=RuleAction.BLOCK,
            statement={
                'RateBasedStatement': {
                    'Limit': base_rate,
                    'AggregateKeyType': 'IP',
                    'EvaluationWindowSec': 300
                }
            },
            visibility_config={
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'GeneralRateLimiting'
            },
            rule_labels=['rate-limiting', 'ddos-protection']
        )
        rules.append(general_rate_rule)
        
        # Strict rate limiting for login endpoints
        login_rate_rule = WAFRule(
            name="LoginEndpointRateLimiting",
            priority=2,
            action=RuleAction.CAPTCHA,
            statement={
                'RateBasedStatement': {
                    'Limit': strict_rate,
                    'AggregateKeyType': 'IP',
                    'EvaluationWindowSec': 300,
                    'ScopeDownStatement': {
                        'ByteMatchStatement': {
                            'SearchString': '/login',
                            'FieldToMatch': {'UriPath': {}},
                            'TextTransformations': [
                                {'Priority': 0, 'Type': 'LOWERCASE'}
                            ],
                            'PositionalConstraint': 'CONTAINS'
                        }
                    }
                }
            },
            visibility_config={
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'LoginRateLimiting'
            },
            rule_labels=['rate-limiting', 'authentication', 'brute-force-protection']
        )
        rules.append(login_rate_rule)
        
        # API endpoint rate limiting
        api_rate_rule = WAFRule(
            name="APIEndpointRateLimiting",
            priority=3,
            action=RuleAction.BLOCK,
            statement={
                'RateBasedStatement': {
                    'Limit': base_rate * 2,
                    'AggregateKeyType': 'IP',
                    'EvaluationWindowSec': 300,
                    'ScopeDownStatement': {
                        'ByteMatchStatement': {
                            'SearchString': '/api/',
                            'FieldToMatch': {'UriPath': {}},
                            'TextTransformations': [
                                {'Priority': 0, 'Type': 'LOWERCASE'}
                            ],
                            'PositionalConstraint': 'STARTS_WITH'
                        }
                    }
                }
            },
            visibility_config={
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'APIRateLimiting'
            },
            rule_labels=['rate-limiting', 'api-protection']
        )
        rules.append(api_rate_rule)
        
        return rules

    def create_geo_blocking_rules(self, blocked_countries: List[str]) -> List[WAFRule]:
        """Create geographic blocking rules"""
        rules = []
        
        if blocked_countries:
            geo_block_rule = WAFRule(
                name="GeographicBlocking",
                priority=10,
                action=RuleAction.BLOCK,
                statement={
                    'GeoMatchStatement': {
                        'CountryCodes': blocked_countries
                    }
                },
                visibility_config={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'GeographicBlocking'
                },
                rule_labels=['geo-blocking', 'compliance']
            )
            rules.append(geo_block_rule)
        
        return rules

    def create_ip_reputation_rules(self, ip_reputation_list_arn: str) -> List[WAFRule]:
        """Create IP reputation-based blocking rules"""
        rules = []
        
        ip_reputation_rule = WAFRule(
            name="IPReputationBlocking",
            priority=5,
            action=RuleAction.BLOCK,
            statement={
                'IPSetReferenceStatement': {
                    'ARN': ip_reputation_list_arn
                }
            },
            visibility_config={
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'IPReputationBlocking'
            },
            rule_labels=['ip-reputation', 'threat-intelligence']
        )
        rules.append(ip_reputation_rule)
        
        return rules

    def create_custom_security_rules(self) -> List[WAFRule]:
        """Create custom security rules for application-specific threats"""
        rules = []
        
        # SQL Injection protection
        sql_injection_rule = WAFRule(
            name="CustomSQLInjectionProtection",
            priority=20,
            action=RuleAction.BLOCK,
            statement={
                'OrStatement': {
                    'Statements': [
                        {
                            'SqliMatchStatement': {
                                'FieldToMatch': {'Body': {'OversizeHandling': 'CONTINUE'}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'URL_DECODE'},
                                    {'Priority': 1, 'Type': 'HTML_ENTITY_DECODE'}
                                ]
                            }
                        },
                        {
                            'SqliMatchStatement': {
                                'FieldToMatch': {'UriPath': {}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'URL_DECODE'},
                                    {'Priority': 1, 'Type': 'HTML_ENTITY_DECODE'}
                                ]
                            }
                        },
                        {
                            'SqliMatchStatement': {
                                'FieldToMatch': {'QueryString': {}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'URL_DECODE'},
                                    {'Priority': 1, 'Type': 'HTML_ENTITY_DECODE'}
                                ]
                            }
                        }
                    ]
                }
            },
            visibility_config={
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'CustomSQLInjectionProtection'
            },
            rule_labels=['sql-injection', 'owasp-top10']
        )
        rules.append(sql_injection_rule)
        
        # XSS protection
        xss_protection_rule = WAFRule(
            name="CustomXSSProtection",
            priority=21,
            action=RuleAction.BLOCK,
            statement={
                'OrStatement': {
                    'Statements': [
                        {
                            'XssMatchStatement': {
                                'FieldToMatch': {'Body': {'OversizeHandling': 'CONTINUE'}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'URL_DECODE'},
                                    {'Priority': 1, 'Type': 'HTML_ENTITY_DECODE'}
                                ]
                            }
                        },
                        {
                            'XssMatchStatement': {
                                'FieldToMatch': {'UriPath': {}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'URL_DECODE'},
                                    {'Priority': 1, 'Type': 'HTML_ENTITY_DECODE'}
                                ]
                            }
                        },
                        {
                            'XssMatchStatement': {
                                'FieldToMatch': {'QueryString': {}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'URL_DECODE'},
                                    {'Priority': 1, 'Type': 'HTML_ENTITY_DECODE'}
                                ]
                            }
                        }
                    ]
                }
            },
            visibility_config={
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'CustomXSSProtection'
            },
            rule_labels=['xss', 'owasp-top10']
        )
        rules.append(xss_protection_rule)
        
        # Scanner detection
        scanner_detection_rule = WAFRule(
            name="ScannerDetection",
            priority=22,
            action=RuleAction.BLOCK,
            statement={
                'OrStatement': {
                    'Statements': [
                        {
                            'ByteMatchStatement': {
                                'SearchString': 'Nmap',
                                'FieldToMatch': {'SingleHeader': {'Name': 'user-agent'}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'LOWERCASE'}
                                ],
                                'PositionalConstraint': 'CONTAINS'
                            }
                        },
                        {
                            'ByteMatchStatement': {
                                'SearchString': 'nikto',
                                'FieldToMatch': {'SingleHeader': {'Name': 'user-agent'}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'LOWERCASE'}
                                ],
                                'PositionalConstraint': 'CONTAINS'
                            }
                        },
                        {
                            'ByteMatchStatement': {
                                'SearchString': 'sqlmap',
                                'FieldToMatch': {'SingleHeader': {'Name': 'user-agent'}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'LOWERCASE'}
                                ],
                                'PositionalConstraint': 'CONTAINS'
                            }
                        }
                    ]
                }
            },
            visibility_config={
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'ScannerDetection'
            },
            rule_labels=['scanner-detection', 'malicious-tools']
        )
        rules.append(scanner_detection_rule)
        
        return rules

    def associate_web_acl(self, web_acl_arn: str, resource_arn: str) -> Dict[str, Any]:
        """Associate Web ACL with AWS resource"""
        try:
            self.wafv2.associate_web_acl(
                WebACLArn=web_acl_arn,
                ResourceArn=resource_arn
            )
            
            self.logger.info(f"Associated Web ACL {web_acl_arn} with resource {resource_arn}")
            
            return {
                'web_acl_arn': web_acl_arn,
                'resource_arn': resource_arn,
                'status': 'associated'
            }
            
        except ClientError as e:
            self.logger.error(f"Error associating Web ACL: {str(e)}")
            raise

    def setup_waf_logging(self, logging_config: LoggingConfiguration) -> Dict[str, Any]:
        """Setup comprehensive WAF logging"""
        try:
            # Create logging configuration
            response = self.wafv2.put_logging_configuration(
                LoggingConfiguration={
                    'ResourceArn': logging_config.resource_arn,
                    'LogDestinationConfigs': logging_config.log_destination_configs,
                    'RedactedFields': logging_config.redacted_fields,
                    'ManagedByFirewallManager': logging_config.managed_by_firewall_manager,
                    'LoggingFilter': logging_config.logging_filter
                }
            )
            
            self.logger.info(f"Configured WAF logging for {logging_config.resource_arn}")
            
            return {
                'resource_arn': logging_config.resource_arn,
                'log_destinations': logging_config.log_destination_configs,
                'status': 'configured'
            }
            
        except ClientError as e:
            self.logger.error(f"Error setting up WAF logging: {str(e)}")
            raise

    def create_ip_set(self, name: str, scope: str, ip_addresses: List[str], 
                     description: str = "") -> Dict[str, Any]:
        """Create IP set for blocking or allowing specific IPs"""
        try:
            response = self.wafv2.create_ip_set(
                Name=name,
                Scope=scope,
                IPAddressVersion='IPV4',
                Addresses=ip_addresses,
                Description=description,
                Tags=[
                    {'Key': 'Purpose', 'Value': 'WAF-Security'},
                    {'Key': 'ManagedBy', 'Value': 'EnterpriseWAFManager'}
                ]
            )
            
            self.logger.info(f"Created IP Set: {name}")
            
            return {
                'ip_set_name': name,
                'ip_set_id': response['Summary']['Id'],
                'ip_set_arn': response['Summary']['ARN'],
                'addresses_count': len(ip_addresses),
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating IP set: {str(e)}")
            raise

    def monitor_waf_metrics(self, web_acl_name: str, metric_period_hours: int = 24) -> Dict[str, Any]:
        """Monitor WAF metrics and generate security reports"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=metric_period_hours)
            
            metrics_data = {}
            
            # Get blocked requests metric
            blocked_requests = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/WAFV2',
                MetricName='BlockedRequests',
                Dimensions=[
                    {
                        'Name': 'WebACL',
                        'Value': web_acl_name
                    },
                    {
                        'Name': 'Region',
                        'Value': self.region
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Sum']
            )
            
            # Get allowed requests metric
            allowed_requests = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/WAFV2',
                MetricName='AllowedRequests',
                Dimensions=[
                    {
                        'Name': 'WebACL',
                        'Value': web_acl_name
                    },
                    {
                        'Name': 'Region',
                        'Value': self.region
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Sum']
            )
            
            # Calculate totals
            total_blocked = sum(point['Sum'] for point in blocked_requests['Datapoints'])
            total_allowed = sum(point['Sum'] for point in allowed_requests['Datapoints'])
            total_requests = total_blocked + total_allowed
            
            block_percentage = (total_blocked / total_requests * 100) if total_requests > 0 else 0
            
            metrics_data = {
                'web_acl_name': web_acl_name,
                'monitoring_period_hours': metric_period_hours,
                'total_requests': total_requests,
                'blocked_requests': total_blocked,
                'allowed_requests': total_allowed,
                'block_percentage': round(block_percentage, 2),
                'blocked_requests_by_hour': [
                    {
                        'timestamp': point['Timestamp'].isoformat(),
                        'count': point['Sum']
                    }
                    for point in blocked_requests['Datapoints']
                ],
                'allowed_requests_by_hour': [
                    {
                        'timestamp': point['Timestamp'].isoformat(),
                        'count': point['Sum']
                    }
                    for point in allowed_requests['Datapoints']
                ],
                'report_generated': datetime.utcnow().isoformat()
            }
            
            # Publish custom metrics
            self._publish_security_metrics(metrics_data)
            
            return metrics_data
            
        except Exception as e:
            self.logger.error(f"Error monitoring WAF metrics: {str(e)}")
            raise

    def _publish_security_metrics(self, metrics_data: Dict[str, Any]) -> None:
        """Publish custom security metrics to CloudWatch"""
        try:
            metric_data = [
                {
                    'MetricName': 'TotalSecurityEvents',
                    'Value': metrics_data['blocked_requests'],
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'WebACL',
                            'Value': metrics_data['web_acl_name']
                        }
                    ]
                },
                {
                    'MetricName': 'SecurityBlockPercentage',
                    'Value': metrics_data['block_percentage'],
                    'Unit': 'Percent',
                    'Dimensions': [
                        {
                            'Name': 'WebACL',
                            'Value': metrics_data['web_acl_name']
                        }
                    ]
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='Enterprise/WAF/Security',
                MetricData=metric_data
            )
            
        except Exception as e:
            self.logger.warning(f"Error publishing security metrics: {str(e)}")

    def test_rules_effectiveness(self, web_acl_id: str, test_payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test WAF rules effectiveness with various payloads"""
        try:
            test_results = []
            
            for payload in test_payloads:
                # Get sampled requests for analysis
                response = self.wafv2.get_sampled_requests(
                    WebAclArn=f"arn:aws:wafv2:{self.region}:123456789012:regional/webacl/{web_acl_id}",
                    RuleMetricName=payload.get('rule_name', 'TestRule'),
                    Scope='REGIONAL',
                    TimeWindow={
                        'StartTime': datetime.utcnow() - timedelta(hours=1),
                        'EndTime': datetime.utcnow()
                    },
                    MaxItems=100
                )
                
                test_results.append({
                    'payload_type': payload.get('type'),
                    'rule_name': payload.get('rule_name'),
                    'samples_found': len(response.get('SampledRequests', [])),
                    'test_timestamp': datetime.utcnow().isoformat()
                })
            
            return {
                'web_acl_id': web_acl_id,
                'test_results': test_results,
                'total_tests': len(test_payloads),
                'test_completed': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error testing rule effectiveness: {str(e)}")
            raise

# Practical Real-World Examples

def create_comprehensive_web_security():
    """Create comprehensive web application security with WAF"""
    
    manager = EnterpriseWAFManager()
    
    # Create IP sets for known threats
    malicious_ips = [
        '192.0.2.44/32',
        '198.51.100.0/24',
        '203.0.113.0/24'
    ]
    
    ip_set_result = manager.create_ip_set(
        name="KnownMaliciousIPs",
        scope="REGIONAL",
        ip_addresses=malicious_ips,
        description="Known malicious IP addresses from threat intelligence"
    )
    print(f"Created IP set: {ip_set_result}")
    
    # Create comprehensive Web ACL
    web_acl = WebACL(
        name="EnterpriseWebApplicationFirewall",
        scope="REGIONAL",
        description="Comprehensive enterprise web application security",
        managed_rule_groups=[
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesCommonRuleSet",
                excluded_rules=["SizeRestrictions_BODY", "GenericRFI_BODY"]
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesOWASPTop10RuleSet"
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesKnownBadInputsRuleSet"
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesBotControlRuleSet",
                managed_rule_group_configs=[
                    {
                        'LoginPath': '/login',
                        'RegistrationPagePath': '/register',
                        'ForgotPasswordPath': '/forgot-password',
                        'CreationPath': '/api/users',
                        'ChangePasswordPath': '/change-password',
                        'UsernameField': {
                            'Identifier': 'username'
                        },
                        'PasswordField': {
                            'Identifier': 'password'
                        }
                    }
                ]
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesAmazonIpReputationList"
            )
        ],
        default_action=RuleAction.ALLOW,
        tags={
            'Environment': 'Production',
            'Application': 'WebApp',
            'SecurityLevel': 'High',
            'ManagedBy': 'EnterpriseWAF'
        },
        custom_response_bodies={
            'CustomResponseBodyKey': {
                'ContentType': 'TEXT_PLAIN',
                'Content': 'Access denied due to security policy'
            }
        }
    )
    
    # Add rate limiting rules
    rate_rules = manager.create_rate_limiting_rules(base_rate=2000, strict_rate=100)
    web_acl.rules.extend(rate_rules)
    
    # Add geographic blocking
    blocked_countries = ['CN', 'RU', 'KP']  # Example: Block China, Russia, North Korea
    geo_rules = manager.create_geo_blocking_rules(blocked_countries)
    web_acl.rules.extend(geo_rules)
    
    # Add IP reputation rules
    ip_reputation_rules = manager.create_ip_reputation_rules(ip_set_result['ip_set_arn'])
    web_acl.rules.extend(ip_reputation_rules)
    
    # Add custom security rules
    custom_rules = manager.create_custom_security_rules()
    web_acl.rules.extend(custom_rules)
    
    # Create Web ACL
    web_acl_result = manager.create_enterprise_web_acl(web_acl)
    print(f"Created Web ACL: {web_acl_result}")
    
    return {
        'ip_set': ip_set_result,
        'web_acl': web_acl_result
    }

def create_api_gateway_protection():
    """Create API Gateway protection with advanced threat detection"""
    
    manager = EnterpriseWAFManager()
    
    # Create API-specific Web ACL
    api_web_acl = WebACL(
        name="APIGatewayProtection",
        scope="REGIONAL",
        description="Advanced protection for API Gateway endpoints",
        managed_rule_groups=[
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesCommonRuleSet"
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesOWASPTop10RuleSet"
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesLinuxRuleSet"
            )
        ],
        rules=[
            WAFRule(
                name="APIKeyValidation",
                priority=100,
                action=RuleAction.BLOCK,
                statement={
                    'NotStatement': {
                        'Statement': {
                            'ByteMatchStatement': {
                                'SearchString': 'x-api-key',
                                'FieldToMatch': {'SingleHeader': {'Name': 'x-api-key'}},
                                'TextTransformations': [
                                    {'Priority': 0, 'Type': 'LOWERCASE'}
                                ],
                                'PositionalConstraint': 'EXACTLY'
                            }
                        }
                    }
                },
                visibility_config={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'APIKeyValidation'
                },
                rule_labels=['api-security', 'authentication']
            ),
            WAFRule(
                name="APIRateLimitingPerKey",
                priority=101,
                action=RuleAction.BLOCK,
                statement={
                    'RateBasedStatement': {
                        'Limit': 1000,
                        'AggregateKeyType': 'CUSTOM_KEYS',
                        'CustomKeys': [
                            {
                                'Header': {
                                    'Name': 'x-api-key',
                                    'TextTransformations': [
                                        {'Priority': 0, 'Type': 'NONE'}
                                    ]
                                }
                            }
                        ],
                        'EvaluationWindowSec': 300
                    }
                },
                visibility_config={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'APIRateLimitingPerKey'
                },
                rule_labels=['api-rate-limiting', 'per-key-limiting']
            )
        ],
        tags={
            'Environment': 'Production',
            'ResourceType': 'API-Gateway',
            'SecurityLevel': 'High'
        }
    )
    
    # Create the API protection Web ACL
    api_result = manager.create_enterprise_web_acl(api_web_acl)
    
    # Setup logging for API Gateway WAF
    logging_config = LoggingConfiguration(
        resource_arn=api_result['web_acl_arn'],
        log_destination_configs=[
            'arn:aws:logs:us-east-1:123456789012:log-group:aws-waf-logs-api-gateway'
        ],
        redacted_fields=[
            {'SingleHeader': {'Name': 'authorization'}},
            {'SingleHeader': {'Name': 'x-api-key'}}
        ],
        logging_filter={
            'DefaultBehavior': 'KEEP',
            'Filters': [
                {
                    'Behavior': 'DROP',
                    'Conditions': [
                        {
                            'ActionCondition': {
                                'Action': 'ALLOW'
                            }
                        }
                    ],
                    'Requirement': 'MEETS_ALL'
                }
            ]
        }
    )
    
    logging_result = manager.setup_waf_logging(logging_config)
    
    return {
        'api_web_acl': api_result,
        'logging_config': logging_result
    }

def create_cloudfront_protection():
    """Create CloudFront distribution protection with global rules"""
    
    manager = EnterpriseWAFManager()
    
    # Create CloudFront-specific Web ACL (Global scope)
    cloudfront_web_acl = WebACL(
        name="CloudFrontGlobalProtection",
        scope="CLOUDFRONT",
        description="Global protection for CloudFront distributions",
        managed_rule_groups=[
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesCommonRuleSet"
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesOWASPTop10RuleSet"
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesBotControlRuleSet"
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesAmazonIpReputationList"
            )
        ],
        rules=[
            WAFRule(
                name="CloudFrontRateLimiting",
                priority=200,
                action=RuleAction.BLOCK,
                statement={
                    'RateBasedStatement': {
                        'Limit': 5000,
                        'AggregateKeyType': 'IP',
                        'EvaluationWindowSec': 300
                    }
                },
                visibility_config={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'CloudFrontRateLimiting'
                },
                rule_labels=['cloudfront-protection', 'ddos-mitigation']
            ),
            WAFRule(
                name="StaticAssetsBypass",
                priority=201,
                action=RuleAction.ALLOW,
                statement={
                    'OrStatement': {
                        'Statements': [
                            {
                                'ByteMatchStatement': {
                                    'SearchString': '.css',
                                    'FieldToMatch': {'UriPath': {}},
                                    'TextTransformations': [
                                        {'Priority': 0, 'Type': 'LOWERCASE'}
                                    ],
                                    'PositionalConstraint': 'ENDS_WITH'
                                }
                            },
                            {
                                'ByteMatchStatement': {
                                    'SearchString': '.js',
                                    'FieldToMatch': {'UriPath': {}},
                                    'TextTransformations': [
                                        {'Priority': 0, 'Type': 'LOWERCASE'}
                                    ],
                                    'PositionalConstraint': 'ENDS_WITH'
                                }
                            },
                            {
                                'ByteMatchStatement': {
                                    'SearchString': '.png',
                                    'FieldToMatch': {'UriPath': {}},
                                    'TextTransformations': [
                                        {'Priority': 0, 'Type': 'LOWERCASE'}
                                    ],
                                    'PositionalConstraint': 'ENDS_WITH'
                                }
                            },
                            {
                                'ByteMatchStatement': {
                                    'SearchString': '.jpg',
                                    'FieldToMatch': {'UriPath': {}},
                                    'TextTransformations': [
                                        {'Priority': 0, 'Type': 'LOWERCASE'}
                                    ],
                                    'PositionalConstraint': 'ENDS_WITH'
                                }
                            }
                        ]
                    }
                },
                visibility_config={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'StaticAssetsBypass'
                },
                rule_labels=['static-assets', 'performance-optimization']
            )
        ],
        tags={
            'Environment': 'Production',
            'ResourceType': 'CloudFront',
            'Scope': 'Global'
        }
    )
    
    # Create the CloudFront Web ACL
    cloudfront_result = manager.create_enterprise_web_acl(cloudfront_web_acl)
    
    return cloudfront_result

def create_application_load_balancer_protection():
    """Create Application Load Balancer protection with custom rules"""
    
    manager = EnterpriseWAFManager()
    
    # Create ALB-specific Web ACL
    alb_web_acl = WebACL(
        name="ALBApplicationProtection",
        scope="REGIONAL",
        description="Advanced protection for Application Load Balancer",
        managed_rule_groups=[
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesCommonRuleSet",
                excluded_rules=["SizeRestrictions_BODY"]  # Allow larger file uploads
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesOWASPTop10RuleSet"
            ),
            ManagedRuleGroup(
                vendor_name="AWS",
                name="AWSManagedRulesLinuxRuleSet"
            )
        ],
        rules=[
            WAFRule(
                name="AdminPanelProtection",
                priority=300,
                action=RuleAction.BLOCK,
                statement={
                    'AndStatement': {
                        'Statements': [
                            {
                                'ByteMatchStatement': {
                                    'SearchString': '/admin',
                                    'FieldToMatch': {'UriPath': {}},
                                    'TextTransformations': [
                                        {'Priority': 0, 'Type': 'LOWERCASE'}
                                    ],
                                    'PositionalConstraint': 'STARTS_WITH'
                                }
                            },
                            {
                                'NotStatement': {
                                    'Statement': {
                                        'IPSetReferenceStatement': {
                                            'ARN': 'arn:aws:wafv2:us-east-1:123456789012:regional/ipset/AdminAllowedIPs/12345'
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                visibility_config={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'AdminPanelProtection'
                },
                rule_labels=['admin-protection', 'access-control']
            ),
            WAFRule(
                name="FileUploadSizeLimit",
                priority=301,
                action=RuleAction.BLOCK,
                statement={
                    'SizeConstraintStatement': {
                        'FieldToMatch': {'Body': {'OversizeHandling': 'CONTINUE'}},
                        'ComparisonOperator': 'GT',
                        'Size': 10485760,  # 10MB
                        'TextTransformations': [
                            {'Priority': 0, 'Type': 'NONE'}
                        ]
                    }
                },
                visibility_config={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'FileUploadSizeLimit'
                },
                rule_labels=['file-upload', 'size-restriction']
            )
        ],
        tags={
            'Environment': 'Production',
            'ResourceType': 'ALB',
            'Application': 'WebApplication'
        }
    )
    
    # Create the ALB Web ACL
    alb_result = manager.create_enterprise_web_acl(alb_web_acl)
    
    # Setup comprehensive logging
    logging_config = LoggingConfiguration(
        resource_arn=alb_result['web_acl_arn'],
        log_destination_configs=[
            'arn:aws:s3:::waf-logs-bucket/AWSLogs/',
            'arn:aws:firehose:us-east-1:123456789012:deliverystream/aws-waf-logs-stream'
        ],
        redacted_fields=[
            {'SingleHeader': {'Name': 'authorization'}},
            {'SingleHeader': {'Name': 'cookie'}}
        ]
    )
    
    logging_result = manager.setup_waf_logging(logging_config)
    
    # Monitor metrics
    metrics_result = manager.monitor_waf_metrics(alb_web_acl.name, metric_period_hours=24)
    
    return {
        'alb_web_acl': alb_result,
        'logging_config': logging_result,
        'metrics': metrics_result
    }
```

## DevOps Integration Patterns

### Infrastructure as Code (Terraform)

```hcl
# waf_infrastructure.tf
resource "aws_wafv2_web_acl" "enterprise_waf" {
  name  = "enterprise-web-application-firewall"
  scope = "REGIONAL"
  description = "Enterprise WAF for comprehensive web application protection"

  default_action {
    allow {}
  }

  # AWS Managed Rule - Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        rule_action_override {
          action_to_use {
            count {}
          }
          name = "SizeRestrictions_BODY"
        }

        rule_action_override {
          action_to_use {
            count {}
          }
          name = "GenericRFI_BODY"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rule - OWASP Top 10
  rule {
    name     = "AWSManagedRulesOWASPTop10RuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesOWASPTop10RuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesOWASPTop10RuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Rate Limiting Rule
  rule {
    name     = "RateLimitRule"
    priority = 3

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
        
        scope_down_statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string         = "/health"
                positional_constraint = "STARTS_WITH"
                
                field_to_match {
                  uri_path {}
                }
                
                text_transformation {
                  priority = 0
                  type     = "LOWERCASE"
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # Geographic Blocking
  rule {
    name     = "GeoBlockRule"
    priority = 4

    action {
      block {}
    }

    statement {
      geo_match_statement {
        country_codes = var.blocked_countries
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "GeoBlockRule"
      sampled_requests_enabled   = true
    }
  }

  # IP Reputation List
  rule {
    name     = "IPReputationRule"
    priority = 5

    action {
      block {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "IPReputationRule"
      sampled_requests_enabled   = true
    }
  }

  # Bot Control
  rule {
    name     = "BotControlRule"
    priority = 6

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesBotControlRuleSet"
        vendor_name = "AWS"

        managed_rule_group_configs {
          login_path                = "/login"
          registration_page_path    = "/register"
          forgot_password_path      = "/forgot-password"
          creation_path            = "/api/users"
          change_password_path     = "/change-password"
          
          username_field {
            identifier = "username"
          }
          
          password_field {
            identifier = "password"
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BotControlRule"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "enterprise-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Environment = var.environment
    Purpose     = "WebApplicationSecurity"
    ManagedBy   = "Terraform"
  }
}

# IP Set for Known Bad IPs
resource "aws_wafv2_ip_set" "known_bad_ips" {
  name               = "known-bad-ips"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  
  addresses = var.known_malicious_ips

  tags = {
    Environment = var.environment
    Purpose     = "ThreatIntelligence"
  }
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "enterprise_waf_logging" {
  resource_arn            = aws_wafv2_web_acl.enterprise_waf.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]

  redacted_field {
    single_header {
      name = "authorization"
    }
  }

  redacted_field {
    single_header {
      name = "cookie"
    }
  }

  logging_filter {
    default_behavior = "KEEP"

    filter {
      behavior    = "DROP"
      condition {
        action_condition {
          action = "ALLOW"
        }
      }
      requirement = "MEETS_ALL"
    }
  }
}

# CloudWatch Log Group for WAF
resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "/aws/wafv2/enterprise"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Purpose     = "WAFLogging"
  }
}

# Associate WAF with Application Load Balancer
resource "aws_wafv2_web_acl_association" "alb_association" {
  resource_arn = aws_lb.application.arn
  web_acl_arn  = aws_wafv2_web_acl.enterprise_waf.arn
}

# CloudWatch Alarms for WAF
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  alarm_name          = "waf-high-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "This metric monitors blocked requests by WAF"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.enterprise_waf.name
    Region = var.aws_region
  }

  tags = {
    Environment = var.environment
    Purpose     = "SecurityMonitoring"
  }
}
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/waf-deployment.yml
name: WAF Security Deployment

on:
  push:
    branches: [main]
    paths: ['security/waf/**']
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - development
          - staging
          - production

jobs:
  validate-rules:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Validate WAF Rules
      run: |
        python scripts/validate_waf_rules.py \
          --rules-dir security/waf/rules/ \
          --environment ${{ github.event.inputs.environment || 'development' }}
    
    - name: Test Rule Effectiveness
      run: |
        python scripts/test_waf_rules.py \
          --test-payloads security/waf/test-payloads.json \
          --environment ${{ github.event.inputs.environment || 'development' }}

  deploy-waf:
    needs: validate-rules
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_WAF_ROLE }}
        aws-region: us-east-1
    
    - name: Deploy WAF Rules
      run: |
        python scripts/deploy_waf_rules.py \
          --config-file security/waf/config/web-acl.json \
          --environment ${{ github.event.inputs.environment || 'development' }}
    
    - name: Associate with Resources
      run: |
        python scripts/associate_waf_resources.py \
          --web-acl-name enterprise-waf-${{ github.event.inputs.environment || 'development' }} \
          --resources-config security/waf/config/resources.json
    
    - name: Setup Monitoring
      run: |
        python scripts/setup_waf_monitoring.py \
          --web-acl-name enterprise-waf-${{ github.event.inputs.environment || 'development' }} \
          --alert-topic ${{ secrets.SECURITY_ALERTS_TOPIC_ARN }}

  security-testing:
    needs: deploy-waf
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_WAF_ROLE }}
        aws-region: us-east-1
    
    - name: Run Security Tests
      run: |
        python scripts/run_security_tests.py \
          --target-url ${{ secrets.TEST_APPLICATION_URL }} \
          --web-acl-name enterprise-waf-${{ github.event.inputs.environment || 'development' }} \
          --test-suite security/waf/tests/
    
    - name: Generate Security Report
      run: |
        python scripts/generate_security_report.py \
          --web-acl-name enterprise-waf-${{ github.event.inputs.environment || 'development' }} \
          --output-format html \
          --output-file security-report.html
    
    - name: Upload Security Report
      uses: actions/upload-artifact@v3
      with:
        name: security-report
        path: security-report.html
```

## Practical Use Cases

### 1. E-commerce Platform Protection
- **OWASP Top 10 protection** against common web vulnerabilities
- **Bot protection** for inventory scraping and account creation
- **Rate limiting** for checkout and payment processes
- **Geographic blocking** for compliance with regional regulations

### 2. API Gateway Security
- **API key validation** and rate limiting per key
- **SQL injection and XSS protection** for API endpoints
- **DDoS mitigation** with advanced rate-based rules
- **Request size limiting** to prevent resource exhaustion

### 3. Corporate Web Applications
- **Admin panel protection** with IP whitelisting
- **Employee authentication** endpoint security
- **File upload security** with size and type restrictions
- **Internal network access** controls and monitoring

### 4. Content Delivery Networks
- **Global threat protection** for CloudFront distributions
- **Static asset optimization** with bypass rules
- **Cache poisoning prevention** with header validation
- **Origin protection** with custom security headers

### 5. Financial Services Security
- **PCI DSS compliance** with comprehensive logging
- **Fraud prevention** with advanced bot detection
- **Transaction endpoint** protection with strict rate limiting
- **Regulatory compliance** with geographic and IP-based controls

## Advanced Security Features

- **Machine learning-based bot detection** with AWS Bot Control
- **Real-time threat intelligence** integration with IP reputation lists
- **Custom response pages** for blocked requests
- **CAPTCHA and JavaScript challenges** for suspicious traffic
- **Comprehensive logging** with PII redaction
- **Automated rule tuning** based on traffic patterns

## Cost Optimization

- **Request-based pricing** with efficient rule ordering
- **Managed rule groups** to reduce custom rule overhead
- **Logging optimization** with selective filtering
- **Regional vs. global** scope selection based on requirements
- **Rule consolidation** to minimize processing overhead
- **Performance monitoring** to optimize rule effectiveness