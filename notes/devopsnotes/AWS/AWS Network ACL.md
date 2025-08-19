# AWS Network ACL - Enterprise Security Automation & Compliance Platform

AWS Network ACLs provide stateless subnet-level security with automated rule management, intelligent threat detection, compliance enforcement, and enterprise-scale security orchestration frameworks.

## Enterprise Network ACL Security Framework

```python
import json
import boto3
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import re
from botocore.exceptions import ClientError

class RuleAction(Enum):
    ALLOW = "allow"
    DENY = "deny"

class Protocol(Enum):
    TCP = "6"
    UDP = "17"
    ICMP = "1"
    ICMPV6 = "58"
    ALL = "-1"

class ComplianceFramework(Enum):
    PCI_DSS = "pci-dss"
    HIPAA = "hipaa"
    SOX = "sox"
    GDPR = "gdpr"
    SOC2 = "soc2"
    NIST = "nist"
    CIS = "cis"

class SecurityTier(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ThreatLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class PortRange:
    from_port: int
    to_port: int

@dataclass
class ICMPTypeCode:
    type: int
    code: Optional[int] = None

@dataclass
class NetworkACLRule:
    rule_number: int
    protocol: Protocol
    action: RuleAction
    cidr_block: str
    port_range: Optional[PortRange] = None
    icmp_type_code: Optional[ICMPTypeCode] = None
    description: str = ""
    compliance_tags: List[ComplianceFramework] = field(default_factory=list)
    security_level: SecurityTier = SecurityTier.MEDIUM

@dataclass
class NetworkACLConfig:
    name: str
    vpc_id: str
    inbound_rules: List[NetworkACLRule] = field(default_factory=list)
    outbound_rules: List[NetworkACLRule] = field(default_factory=list)
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    security_tier: SecurityTier = SecurityTier.MEDIUM
    auto_remediation: bool = False
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class ManagedNetworkACL:
    id: str
    name: str
    vpc_id: str
    is_default: bool
    inbound_rules: List[NetworkACLRule] = field(default_factory=list)
    outbound_rules: List[NetworkACLRule] = field(default_factory=list)
    associated_subnets: List[str] = field(default_factory=list)
    compliance_status: Dict[str, bool] = field(default_factory=dict)
    security_score: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class SecurityViolation:
    violation_id: str
    nacl_id: str
    rule_number: int
    violation_type: str
    severity: ThreatLevel
    description: str
    recommendation: str
    compliance_impact: List[ComplianceFramework] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ComplianceReport:
    framework: ComplianceFramework
    nacl_id: str
    compliance_score: float
    violations: List[SecurityViolation] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    last_assessed: datetime = field(default_factory=datetime.utcnow)

class EnterpriseNetworkACLManager:
    """
    Enterprise AWS Network ACL manager with automated security,
    compliance enforcement, and intelligent threat detection.
    """
    
    def __init__(self, 
                 region: str = 'us-east-1',
                 compliance_frameworks: List[ComplianceFramework] = None):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.guardduty = boto3.client('guardduty', region_name=region)
        self.securityhub = boto3.client('securityhub', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.region = region
        self.compliance_frameworks = compliance_frameworks or []
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('NetworkACL')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def deploy_enterprise_security_framework(self, 
                                           vpc_id: str,
                                           security_tier: SecurityTier = SecurityTier.HIGH,
                                           compliance_frameworks: List[ComplianceFramework] = None) -> Dict[str, Any]:
        """Deploy comprehensive enterprise security framework with Network ACLs"""
        try:
            deployment_start = datetime.utcnow()
            
            # Get VPC details and subnets
            vpc_details = self._get_vpc_details(vpc_id)
            subnets = self._get_vpc_subnets(vpc_id)
            
            # Generate security architecture
            security_architecture = self._generate_security_architecture(
                vpc_details, subnets, security_tier, compliance_frameworks
            )
            
            # Deploy Network ACLs
            deployed_nacls = self._deploy_network_acls(security_architecture)
            
            # Associate NACLs with appropriate subnets
            subnet_associations = self._configure_subnet_associations(
                deployed_nacls, subnets, security_architecture
            )
            
            # Setup compliance monitoring
            compliance_monitoring = self._setup_compliance_monitoring(
                deployed_nacls, compliance_frameworks
            )
            
            # Setup threat detection and automated response
            threat_detection = self._setup_threat_detection(deployed_nacls)
            
            # Generate security baseline
            security_baseline = self._generate_security_baseline(deployed_nacls)
            
            deployment_time = (datetime.utcnow() - deployment_start).total_seconds()
            
            result = {
                'deployment_id': f"nacl-security-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'vpc_id': vpc_id,
                'security_tier': security_tier.value,
                'network_acls': [self._serialize_nacl(nacl) for nacl in deployed_nacls],
                'subnet_associations': subnet_associations,
                'compliance_monitoring': compliance_monitoring,
                'threat_detection': threat_detection,
                'security_baseline': security_baseline,
                'deployment_time_seconds': deployment_time,
                'deployed_at': deployment_start.isoformat()
            }
            
            self.logger.info(f"Deployed enterprise security framework: {result['deployment_id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error deploying enterprise security framework: {str(e)}")
            raise

    def _generate_security_architecture(self, 
                                      vpc_details: Dict[str, Any],
                                      subnets: List[Dict[str, Any]],
                                      security_tier: SecurityTier,
                                      compliance_frameworks: List[ComplianceFramework] = None) -> Dict[str, Any]:
        """Generate comprehensive security architecture for VPC"""
        
        architecture = {
            'security_zones': {},
            'nacl_configs': [],
            'threat_models': [],
            'compliance_requirements': []
        }
        
        # Categorize subnets into security zones
        security_zones = self._categorize_security_zones(subnets)
        architecture['security_zones'] = security_zones
        
        # Generate NACL configurations for each security zone
        for zone_name, zone_subnets in security_zones.items():
            nacl_config = self._generate_zone_nacl_config(
                zone_name, zone_subnets, security_tier, compliance_frameworks
            )
            architecture['nacl_configs'].append(nacl_config)
        
        # Generate threat models
        architecture['threat_models'] = self._generate_threat_models(
            security_zones, security_tier
        )
        
        # Generate compliance requirements
        if compliance_frameworks:
            architecture['compliance_requirements'] = self._generate_compliance_requirements(
                compliance_frameworks, security_zones
            )
        
        return architecture

    def _categorize_security_zones(self, subnets: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize subnets into security zones based on tags and naming"""
        
        zones = {
            'public': [],
            'private_app': [],
            'private_data': [],
            'management': [],
            'dmz': []
        }
        
        for subnet in subnets:
            subnet_name = self._get_tag_value(subnet.get('Tags', []), 'Name', '').lower()
            
            # Categorize based on naming patterns and route table analysis
            if any(keyword in subnet_name for keyword in ['public', 'web', 'elb', 'alb']):
                zones['public'].append(subnet)
            elif any(keyword in subnet_name for keyword in ['database', 'db', 'data', 'rds']):
                zones['private_data'].append(subnet)
            elif any(keyword in subnet_name for keyword in ['mgmt', 'management', 'admin', 'bastion']):
                zones['management'].append(subnet)
            elif any(keyword in subnet_name for keyword in ['dmz', 'edge', 'firewall']):
                zones['dmz'].append(subnet)
            else:
                # Default to private application tier
                zones['private_app'].append(subnet)
        
        # Remove empty zones
        return {k: v for k, v in zones.items() if v}

    def _generate_zone_nacl_config(self, 
                                 zone_name: str,
                                 zone_subnets: List[Dict[str, Any]],
                                 security_tier: SecurityTier,
                                 compliance_frameworks: List[ComplianceFramework] = None) -> NetworkACLConfig:
        """Generate Network ACL configuration for a security zone"""
        
        vpc_id = zone_subnets[0]['VpcId']
        
        # Base configuration
        config = NetworkACLConfig(
            name=f"NACL-{zone_name.upper()}-{security_tier.value}",
            vpc_id=vpc_id,
            compliance_frameworks=compliance_frameworks or [],
            security_tier=security_tier,
            auto_remediation=(security_tier in [SecurityTier.CRITICAL, SecurityTier.HIGH]),
            tags={
                'SecurityZone': zone_name,
                'SecurityTier': security_tier.value,
                'ManagedBy': 'EnterpriseNetworkACLManager',
                'ComplianceFrameworks': ','.join([f.value for f in (compliance_frameworks or [])])
            }
        )
        
        # Generate rules based on zone type and security tier
        if zone_name == 'public':
            config.inbound_rules.extend(self._generate_public_zone_rules(security_tier))
            config.outbound_rules.extend(self._generate_public_zone_outbound_rules(security_tier))
        elif zone_name == 'private_app':
            config.inbound_rules.extend(self._generate_app_zone_rules(security_tier))
            config.outbound_rules.extend(self._generate_app_zone_outbound_rules(security_tier))
        elif zone_name == 'private_data':
            config.inbound_rules.extend(self._generate_data_zone_rules(security_tier))
            config.outbound_rules.extend(self._generate_data_zone_outbound_rules(security_tier))
        elif zone_name == 'management':
            config.inbound_rules.extend(self._generate_mgmt_zone_rules(security_tier))
            config.outbound_rules.extend(self._generate_mgmt_zone_outbound_rules(security_tier))
        elif zone_name == 'dmz':
            config.inbound_rules.extend(self._generate_dmz_zone_rules(security_tier))
            config.outbound_rules.extend(self._generate_dmz_zone_outbound_rules(security_tier))
        
        # Add compliance-specific rules
        if compliance_frameworks:
            config.inbound_rules.extend(self._generate_compliance_rules(compliance_frameworks, zone_name))
        
        return config

    def _generate_public_zone_rules(self, security_tier: SecurityTier) -> List[NetworkACLRule]:
        """Generate inbound rules for public zone"""
        rules = [
            # HTTP traffic
            NetworkACLRule(
                rule_number=100,
                protocol=Protocol.TCP,
                action=RuleAction.ALLOW,
                cidr_block="0.0.0.0/0",
                port_range=PortRange(80, 80),
                description="Allow HTTP traffic from internet",
                security_level=SecurityTier.LOW
            ),
            # HTTPS traffic
            NetworkACLRule(
                rule_number=110,
                protocol=Protocol.TCP,
                action=RuleAction.ALLOW,
                cidr_block="0.0.0.0/0",
                port_range=PortRange(443, 443),
                description="Allow HTTPS traffic from internet",
                security_level=SecurityTier.LOW
            ),
            # Ephemeral ports for return traffic
            NetworkACLRule(
                rule_number=120,
                protocol=Protocol.TCP,
                action=RuleAction.ALLOW,
                cidr_block="0.0.0.0/0",
                port_range=PortRange(1024, 65535),
                description="Allow ephemeral ports for return traffic",
                security_level=SecurityTier.MEDIUM
            )
        ]
        
        # Add security tier specific rules
        if security_tier == SecurityTier.CRITICAL:
            # Block known malicious IPs (example ranges)
            rules.extend([
                NetworkACLRule(
                    rule_number=50,
                    protocol=Protocol.ALL,
                    action=RuleAction.DENY,
                    cidr_block="192.0.2.0/24",  # Test network
                    description="Block test network range",
                    security_level=SecurityTier.CRITICAL
                ),
                NetworkACLRule(
                    rule_number=60,
                    protocol=Protocol.ALL,
                    action=RuleAction.DENY,
                    cidr_block="198.51.100.0/24",  # Test network
                    description="Block test network range",
                    security_level=SecurityTier.CRITICAL
                )
            ])
        
        return rules

    def _generate_data_zone_rules(self, security_tier: SecurityTier) -> List[NetworkACLRule]:
        """Generate inbound rules for data zone (most restrictive)"""
        rules = [
            # MySQL/Aurora from application subnets only
            NetworkACLRule(
                rule_number=100,
                protocol=Protocol.TCP,
                action=RuleAction.ALLOW,
                cidr_block="10.0.0.0/8",  # Internal network only
                port_range=PortRange(3306, 3306),
                description="Allow MySQL from internal networks only",
                security_level=SecurityTier.HIGH,
                compliance_tags=[ComplianceFramework.PCI_DSS, ComplianceFramework.HIPAA]
            ),
            # PostgreSQL from application subnets only
            NetworkACLRule(
                rule_number=110,
                protocol=Protocol.TCP,
                action=RuleAction.ALLOW,
                cidr_block="10.0.0.0/8",
                port_range=PortRange(5432, 5432),
                description="Allow PostgreSQL from internal networks only",
                security_level=SecurityTier.HIGH,
                compliance_tags=[ComplianceFramework.PCI_DSS, ComplianceFramework.HIPAA]
            ),
            # Ephemeral ports for return traffic (restricted)
            NetworkACLRule(
                rule_number=200,
                protocol=Protocol.TCP,
                action=RuleAction.ALLOW,
                cidr_block="10.0.0.0/8",
                port_range=PortRange(32768, 65535),
                description="Allow ephemeral ports from internal networks",
                security_level=SecurityTier.MEDIUM
            )
        ]
        
        # Critical security: Explicit deny for internet traffic
        if security_tier in [SecurityTier.CRITICAL, SecurityTier.HIGH]:
            rules.insert(0, NetworkACLRule(
                rule_number=50,
                protocol=Protocol.ALL,
                action=RuleAction.DENY,
                cidr_block="0.0.0.0/0",
                description="Explicit deny all internet traffic to data layer",
                security_level=SecurityTier.CRITICAL
            ))
        
        return rules

    def setup_automated_compliance_monitoring(self, 
                                            nacl_ids: List[str],
                                            compliance_frameworks: List[ComplianceFramework]) -> Dict[str, Any]:
        """Setup automated compliance monitoring for Network ACLs"""
        try:
            monitoring_setup = {}
            
            # Create compliance assessment Lambda function
            compliance_function = self._create_compliance_assessment_lambda()
            monitoring_setup['compliance_function'] = compliance_function
            
            # Setup CloudWatch rules for compliance monitoring
            compliance_rules = self._create_compliance_monitoring_rules(nacl_ids, compliance_frameworks)
            monitoring_setup['cloudwatch_rules'] = compliance_rules
            
            # Create compliance dashboard
            compliance_dashboard = self._create_compliance_dashboard(nacl_ids, compliance_frameworks)
            monitoring_setup['dashboard'] = compliance_dashboard
            
            # Setup automated remediation workflows
            remediation_workflows = self._setup_remediation_workflows(nacl_ids)
            monitoring_setup['remediation_workflows'] = remediation_workflows
            
            # Create security findings integration
            security_hub_integration = self._setup_security_hub_integration(nacl_ids)
            monitoring_setup['security_hub_integration'] = security_hub_integration
            
            return {
                'monitoring_id': f"compliance-monitor-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'frameworks': [f.value for f in compliance_frameworks],
                'nacls_monitored': len(nacl_ids),
                'monitoring_setup': monitoring_setup,
                'setup_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error setting up compliance monitoring: {str(e)}")
            raise

    def perform_comprehensive_security_assessment(self, 
                                                 nacl_ids: List[str] = None,
                                                 compliance_frameworks: List[ComplianceFramework] = None) -> Dict[str, Any]:
        """Perform comprehensive security assessment of Network ACLs"""
        try:
            if not nacl_ids:
                nacl_ids = self._get_all_nacl_ids()
            
            assessment_results = {}
            total_violations = 0
            
            for nacl_id in nacl_ids:
                # Get NACL details
                nacl_details = self._get_nacl_details(nacl_id)
                
                # Perform security analysis
                security_analysis = self._analyze_nacl_security(nacl_details)
                
                # Check compliance if frameworks specified
                compliance_reports = []
                if compliance_frameworks:
                    for framework in compliance_frameworks:
                        compliance_report = self._assess_compliance(nacl_details, framework)
                        compliance_reports.append(compliance_report)
                
                # Identify security violations
                violations = self._identify_security_violations(nacl_details, security_analysis)
                total_violations += len(violations)
                
                # Generate recommendations
                recommendations = self._generate_security_recommendations(
                    nacl_details, security_analysis, violations
                )
                
                assessment_results[nacl_id] = {
                    'nacl_details': self._serialize_nacl(nacl_details),
                    'security_analysis': security_analysis,
                    'compliance_reports': [self._serialize_compliance_report(cr) for cr in compliance_reports],
                    'violations': [self._serialize_violation(v) for v in violations],
                    'recommendations': recommendations,
                    'security_score': self._calculate_security_score(security_analysis, violations)
                }
            
            # Generate summary insights
            summary = {
                'total_nacls_assessed': len(nacl_ids),
                'total_violations': total_violations,
                'average_security_score': sum(
                    result['security_score'] for result in assessment_results.values()
                ) / len(nacl_ids) if nacl_ids else 0,
                'critical_violations': len([
                    v for result in assessment_results.values() 
                    for v in result['violations'] 
                    if v['severity'] == 'critical'
                ]),
                'compliance_summary': self._generate_compliance_summary(assessment_results, compliance_frameworks)
            }
            
            return {
                'assessment_id': f"nacl-assessment-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'generated_at': datetime.utcnow().isoformat(),
                'summary': summary,
                'assessment_results': assessment_results,
                'security_insights': self._generate_security_insights(assessment_results),
                'remediation_plan': self._generate_remediation_plan(assessment_results)
            }
            
        except Exception as e:
            self.logger.error(f"Error performing security assessment: {str(e)}")
            raise

    def automated_threat_response(self, 
                                threat_indicators: List[str],
                                response_level: ThreatLevel = ThreatLevel.HIGH) -> Dict[str, Any]:
        """Implement automated threat response by updating Network ACL rules"""
        try:
            response_actions = []
            
            for threat_ip in threat_indicators:
                # Validate IP address
                try:
                    ipaddress.ip_address(threat_ip)
                except ValueError:
                    self.logger.warning(f"Invalid IP address: {threat_ip}")
                    continue
                
                # Get all NACLs that need updating
                nacls_to_update = self._get_nacls_for_threat_response(response_level)
                
                for nacl_id in nacls_to_update:
                    # Add deny rule for threat IP
                    action_result = self._add_threat_deny_rule(nacl_id, threat_ip, response_level)
                    response_actions.append(action_result)
                    
                    # Log security event
                    self._log_security_event(nacl_id, threat_ip, response_level, action_result)
            
            # Create incident response report
            incident_report = self._create_incident_response_report(
                threat_indicators, response_actions, response_level
            )
            
            return {
                'response_id': f"threat-response-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'threat_indicators': threat_indicators,
                'response_level': response_level.value,
                'actions_taken': len(response_actions),
                'response_actions': response_actions,
                'incident_report': incident_report,
                'responded_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in automated threat response: {str(e)}")
            raise

    def _analyze_nacl_security(self, nacl: ManagedNetworkACL) -> Dict[str, Any]:
        """Analyze Network ACL security posture"""
        
        analysis = {
            'rule_analysis': {},
            'security_gaps': [],
            'best_practice_violations': [],
            'risk_score': 0.0
        }
        
        # Analyze inbound rules
        inbound_analysis = self._analyze_rule_set(nacl.inbound_rules, 'inbound')
        analysis['rule_analysis']['inbound'] = inbound_analysis
        
        # Analyze outbound rules
        outbound_analysis = self._analyze_rule_set(nacl.outbound_rules, 'outbound')
        analysis['rule_analysis']['outbound'] = outbound_analysis
        
        # Check for security gaps
        analysis['security_gaps'] = self._identify_security_gaps(nacl)
        
        # Check best practice violations
        analysis['best_practice_violations'] = self._check_best_practices(nacl)
        
        # Calculate risk score
        analysis['risk_score'] = self._calculate_risk_score(
            inbound_analysis, outbound_analysis, 
            analysis['security_gaps'], analysis['best_practice_violations']
        )
        
        return analysis

    def _identify_security_violations(self, 
                                   nacl: ManagedNetworkACL,
                                   analysis: Dict[str, Any]) -> List[SecurityViolation]:
        """Identify security violations in Network ACL configuration"""
        
        violations = []
        
        # Check for overly permissive rules
        for rule in nacl.inbound_rules + nacl.outbound_rules:
            if rule.cidr_block == "0.0.0.0/0" and rule.action == RuleAction.ALLOW:
                if rule.port_range and (rule.port_range.to_port - rule.port_range.from_port) > 100:
                    violations.append(SecurityViolation(
                        violation_id=f"OVERLY_PERMISSIVE_{rule.rule_number}",
                        nacl_id=nacl.id,
                        rule_number=rule.rule_number,
                        violation_type="Overly Permissive Rule",
                        severity=ThreatLevel.HIGH,
                        description=f"Rule {rule.rule_number} allows wide port range from anywhere",
                        recommendation="Restrict source CIDR and/or port range",
                        compliance_impact=[ComplianceFramework.PCI_DSS, ComplianceFramework.HIPAA]
                    ))
        
        # Check for missing explicit deny rules
        if not any(rule.action == RuleAction.DENY for rule in nacl.inbound_rules):
            violations.append(SecurityViolation(
                violation_id="MISSING_EXPLICIT_DENY",
                nacl_id=nacl.id,
                rule_number=0,
                violation_type="Missing Explicit Deny",
                severity=ThreatLevel.MEDIUM,
                description="No explicit deny rules found",
                recommendation="Add explicit deny rules for known bad actors",
                compliance_impact=[ComplianceFramework.CIS, ComplianceFramework.NIST]
            ))
        
        return violations

    def _serialize_nacl(self, nacl: ManagedNetworkACL) -> Dict[str, Any]:
        """Serialize Network ACL for JSON output"""
        return {
            'id': nacl.id,
            'name': nacl.name,
            'vpc_id': nacl.vpc_id,
            'is_default': nacl.is_default,
            'inbound_rules': [self._serialize_rule(rule) for rule in nacl.inbound_rules],
            'outbound_rules': [self._serialize_rule(rule) for rule in nacl.outbound_rules],
            'associated_subnets': nacl.associated_subnets,
            'compliance_status': nacl.compliance_status,
            'security_score': nacl.security_score,
            'tags': nacl.tags
        }

    def _serialize_rule(self, rule: NetworkACLRule) -> Dict[str, Any]:
        """Serialize Network ACL rule for JSON output"""
        return {
            'rule_number': rule.rule_number,
            'protocol': rule.protocol.value,
            'action': rule.action.value,
            'cidr_block': rule.cidr_block,
            'port_range': {
                'from_port': rule.port_range.from_port,
                'to_port': rule.port_range.to_port
            } if rule.port_range else None,
            'icmp_type_code': {
                'type': rule.icmp_type_code.type,
                'code': rule.icmp_type_code.code
            } if rule.icmp_type_code else None,
            'description': rule.description,
            'compliance_tags': [tag.value for tag in rule.compliance_tags],
            'security_level': rule.security_level.value
        }

    def _get_vpc_details(self, vpc_id: str) -> Dict[str, Any]:
        """Get VPC details"""
        try:
            response = self.ec2.describe_vpcs(VpcIds=[vpc_id])
            return response['Vpcs'][0]
        except Exception as e:
            self.logger.error(f"Error getting VPC details for {vpc_id}: {str(e)}")
            raise

    def _get_vpc_subnets(self, vpc_id: str) -> List[Dict[str, Any]]:
        """Get all subnets in VPC"""
        try:
            response = self.ec2.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            return response['Subnets']
        except Exception as e:
            self.logger.error(f"Error getting subnets for VPC {vpc_id}: {str(e)}")
            raise

    def _get_tag_value(self, tags: List[Dict[str, str]], key: str, default: str = '') -> str:
        """Get tag value by key"""
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
        return default

# Network ACL Security Orchestrator
class NetworkACLSecurityOrchestrator:
    """
    Orchestrates Network ACL security across multiple VPCs,
    accounts, and regions with centralized compliance management.
    """
    
    def __init__(self, regions: List[str], compliance_frameworks: List[ComplianceFramework]):
        self.regions = regions
        self.compliance_frameworks = compliance_frameworks
        self.managers = {}
        self.logger = logging.getLogger('NACLSecurityOrchestrator')
        
        # Initialize managers for each region
        for region in regions:
            self.managers[region] = EnterpriseNetworkACLManager(
                region=region, 
                compliance_frameworks=compliance_frameworks
            )

    def deploy_organization_wide_security(self, 
                                        security_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy Network ACL security framework across organization"""
        
        deployment_results = {}
        total_nacls = 0
        
        try:
            # Deploy security framework in parallel across regions
            with ThreadPoolExecutor(max_workers=len(self.regions)) as executor:
                futures = {}
                
                for region in self.regions:
                    if region in security_config:
                        region_config = security_config[region]
                        manager = self.managers[region]
                        
                        future = executor.submit(
                            manager.deploy_enterprise_security_framework,
                            region_config['vpc_id'],
                            SecurityTier(region_config.get('security_tier', 'high')),
                            self.compliance_frameworks
                        )
                        futures[future] = region
                
                for future in as_completed(futures):
                    region = futures[future]
                    try:
                        result = future.result()
                        deployment_results[region] = result
                        total_nacls += len(result['network_acls'])
                        
                        self.logger.info(f"Successfully deployed security framework in {region}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to deploy security framework in {region}: {str(e)}")
                        deployment_results[region] = {'error': str(e)}
            
            return {
                'deployment_id': f"org-security-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'regions_deployed': len([r for r in deployment_results.values() if 'error' not in r]),
                'total_regions': len(self.regions),
                'total_nacls_deployed': total_nacls,
                'compliance_frameworks': [f.value for f in self.compliance_frameworks],
                'regional_deployments': deployment_results,
                'deployed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in organization-wide security deployment: {str(e)}")
            raise

# Example usage and enterprise patterns
def create_enterprise_security_deployment():
    """Create comprehensive enterprise Network ACL security deployment"""
    
    # Define compliance frameworks
    compliance_frameworks = [
        ComplianceFramework.PCI_DSS,
        ComplianceFramework.HIPAA,
        ComplianceFramework.SOC2,
        ComplianceFramework.NIST
    ]
    
    # Create Network ACL manager
    nacl_manager = EnterpriseNetworkACLManager(
        region='us-east-1',
        compliance_frameworks=compliance_frameworks
    )
    
    # Deploy enterprise security framework
    vpc_id = 'vpc-12345678'  # Replace with actual VPC ID
    security_deployment = nacl_manager.deploy_enterprise_security_framework(
        vpc_id=vpc_id,
        security_tier=SecurityTier.CRITICAL,
        compliance_frameworks=compliance_frameworks
    )
    
    print(f"Deployed security framework: {security_deployment['deployment_id']}")
    print(f"Network ACLs deployed: {len(security_deployment['network_acls'])}")
    print(f"Security tier: {security_deployment['security_tier']}")
    
    # Setup automated compliance monitoring
    nacl_ids = [nacl['id'] for nacl in security_deployment['network_acls']]
    compliance_monitoring = nacl_manager.setup_automated_compliance_monitoring(
        nacl_ids, compliance_frameworks
    )
    
    print(f"Compliance monitoring setup: {compliance_monitoring['monitoring_id']}")
    print(f"Frameworks monitored: {len(compliance_monitoring['frameworks'])}")
    
    return security_deployment, compliance_monitoring

def perform_security_assessment():
    """Perform comprehensive security assessment"""
    
    nacl_manager = EnterpriseNetworkACLManager()
    
    # Define compliance frameworks for assessment
    compliance_frameworks = [
        ComplianceFramework.PCI_DSS,
        ComplianceFramework.CIS,
        ComplianceFramework.NIST
    ]
    
    # Perform comprehensive assessment
    assessment_result = nacl_manager.perform_comprehensive_security_assessment(
        compliance_frameworks=compliance_frameworks
    )
    
    print(f"Security assessment: {assessment_result['assessment_id']}")
    print(f"NACLs assessed: {assessment_result['summary']['total_nacls_assessed']}")
    print(f"Total violations: {assessment_result['summary']['total_violations']}")
    print(f"Average security score: {assessment_result['summary']['average_security_score']:.2f}")
    
    return assessment_result

if __name__ == "__main__":
    # Create enterprise security deployment
    security_deployment, compliance_monitoring = create_enterprise_security_deployment()
    
    # Perform security assessment
    assessment_result = perform_security_assessment()
```

## DevOps Integration Patterns

### CI/CD Pipeline Integration

```yaml
# .github/workflows/network-acl-security.yml
name: Network ACL Security Management

on:
  schedule:
    - cron: '0 4 * * *'  # Daily at 4 AM
  workflow_dispatch:
    inputs:
      action:
        description: 'Security action'
        required: false
        default: 'assess'
        type: choice
        options:
        - assess
        - deploy
        - remediate
        - audit

jobs:
  network-acl-security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_NETWORK_SECURITY_ROLE }}
        aws-region: us-east-1
    
    - name: Run Security Assessment
      run: |
        python scripts/network_acl_security.py \
          --action ${{ github.event.inputs.action || 'assess' }} \
          --compliance-frameworks pci-dss,hipaa,nist \
          --security-tier critical \
          --output-format json
    
    - name: Generate Security Report
      run: |
        python scripts/generate_security_report.py \
          --include-compliance-status \
          --include-threat-analysis \
          --include-remediation-plan \
          --output-format html
    
    - name: Upload Security Reports
      uses: actions/upload-artifact@v3
      with:
        name: network-acl-security-reports
        path: |
          security-assessment-*.json
          security-report-*.html
          compliance-report-*.pdf
```

### Terraform Integration

```hcl
# network_acl_security.tf
resource "aws_network_acl" "enterprise_security" {
  for_each = var.security_zones

  vpc_id = var.vpc_id
  
  tags = {
    Name = "NACL-${upper(each.key)}-${var.security_tier}"
    SecurityZone = each.key
    SecurityTier = var.security_tier
    ComplianceFrameworks = join(",", var.compliance_frameworks)
    ManagedBy = "terraform"
  }
}

resource "aws_network_acl_rule" "inbound_security_rules" {
  for_each = {
    for rule in flatten([
      for zone, config in var.security_zones : [
        for rule in config.inbound_rules : {
          key = "${zone}-inbound-${rule.rule_number}"
          zone = zone
          rule = rule
        }
      ]
    ]) : rule.key => rule
  }

  network_acl_id = aws_network_acl.enterprise_security[each.value.zone].id
  rule_number    = each.value.rule.rule_number
  protocol       = each.value.rule.protocol
  rule_action    = each.value.rule.action
  cidr_block     = each.value.rule.cidr_block
  from_port      = each.value.rule.from_port
  to_port        = each.value.rule.to_port
}

resource "aws_network_acl_association" "security_associations" {
  for_each = {
    for assoc in flatten([
      for zone, config in var.security_zones : [
        for subnet_id in config.subnet_ids : {
          key = "${zone}-${subnet_id}"
          zone = zone
          subnet_id = subnet_id
        }
      ]
    ]) : assoc.key => assoc
  }

  subnet_id      = each.value.subnet_id
  network_acl_id = aws_network_acl.enterprise_security[each.value.zone].id
}

resource "aws_lambda_function" "security_monitor" {
  filename         = "security_monitor.zip"
  function_name    = "network-acl-security-monitor"
  role            = aws_iam_role.security_monitor_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900

  environment {
    variables = {
      NACL_IDS = jsonencode([for nacl in aws_network_acl.enterprise_security : nacl.id])
      COMPLIANCE_FRAMEWORKS = join(",", var.compliance_frameworks)
      SECURITY_TIER = var.security_tier
      SNS_TOPIC_ARN = aws_sns_topic.security_alerts.arn
    }
  }
}

resource "aws_cloudwatch_event_rule" "security_assessment_schedule" {
  name                = "network-acl-security-assessment"
  description         = "Trigger Network ACL security assessment"
  schedule_expression = "cron(0 4 * * ? *)"  # Daily at 4 AM
}

resource "aws_cloudwatch_event_target" "security_monitor_target" {
  rule      = aws_cloudwatch_event_rule.security_assessment_schedule.name
  target_id = "NetworkACLSecurityMonitorTarget"
  arn       = aws_lambda_function.security_monitor.arn
}
```

## Enterprise Use Cases

### Financial Services
- **PCI DSS Compliance**: Automated compliance monitoring and enforcement for payment card industry standards
- **Regulatory Reporting**: Comprehensive audit trails and compliance reporting for financial regulators
- **Fraud Prevention**: Automated threat response and IP blocking for known malicious actors

### Healthcare Organizations
- **HIPAA Compliance**: Automated enforcement of healthcare data protection requirements
- **Patient Data Security**: Multi-tier security zones with strict access controls for patient data
- **Audit Requirements**: Comprehensive logging and monitoring for healthcare compliance audits

### Enterprise SaaS
- **Multi-Tenant Security**: Isolated security zones for different customer environments
- **SOC 2 Compliance**: Automated compliance assessment and reporting for service organization controls
- **Threat Intelligence**: Integration with threat feeds for proactive security response

## Key Features

- **Automated Security Deployment**: Enterprise-grade Network ACL deployment with security zone categorization
- **Compliance Automation**: Built-in compliance frameworks for PCI DSS, HIPAA, SOX, GDPR, SOC 2, NIST, and CIS
- **Intelligent Threat Response**: Automated threat detection and response with IP blocking capabilities
- **Security Assessment**: Comprehensive security posture analysis with violation detection
- **DevOps Integration**: Native integration with CI/CD pipelines and Infrastructure as Code
- **Multi-Framework Support**: Support for multiple compliance frameworks simultaneously
- **Risk-Based Security**: Dynamic security rules based on security tiers and threat levels
- **Automated Remediation**: Self-healing security configurations with automated rule updates

- **Purpose:** Optional stateless firewall for controlling traffic in and out of subnets  
- Deny everything by default
- **Stateless:** Responses must be explicitly allowed by rules  
- **Applies To:** Subnets (not individual instances)  
- **Rule Evaluation:** Numbered rules evaluated in order; lowest number first (1-32766)
- **Default NACL:** Allows all inbound and outbound traffic 
- **Custom NACL:** Deny all by default unless specified  
- **Supports:** Allow and deny rules (unlike Security Groups which only allow)  
- **Use Case:** Fine-grained subnet-level control, blacklist IPs, etc.
