# AWS IAM (Identity and Access Management)

> **Service Type:** Security & Identity | **Tier:** Essential DevOps | **Global/Regional:** Global

## Overview

AWS IAM is a foundational security service that enables you to securely control access to AWS services and resources. It provides centralized authentication and authorization for users, applications, and services across your AWS infrastructure.

## DevOps Use Cases

### CI/CD Pipeline Security
- **Service roles** for CodePipeline, CodeBuild, and CodeDeploy
- **Cross-account deployments** using assumable roles
- **Automated deployments** with least-privilege permissions
- **Secret access** for build processes and deployments

### Infrastructure Automation
- **CloudFormation service roles** for stack deployments
- **Lambda execution roles** for serverless automation
- **EC2 instance profiles** for applications and services
- **Cross-service permissions** for integrated workflows

### Multi-Account Management
- **Cross-account role assumption** for centralized management
- **Federated access** for external identity providers
- **Service-linked roles** for AWS services
- **Organization-wide policies** using Service Control Policies (SCPs)

### Access Management
- **Developer access** with appropriate boundaries
- **Production access** through break-glass procedures
- **Service accounts** for applications and tools
- **Temporary access** for contractors and auditors

## Core Components

### Identity Types

#### Users
- **Purpose:** A single entity (person, app, or service)
- **Credentials:** Permanent access keys and passwords
- **Best Practice:** Use for human users only, prefer roles for services
- **Limits:** 5,000 users per account, 2 access keys per user

#### Groups
- **Purpose:** Collection of users for permission management
- **Limitations:** Cannot contain other groups, users can be in multiple groups
- **Use Cases:** Department-based permissions, role-based access
- **Best Practice:** Attach policies to groups, not individual users

#### Roles
- **Purpose:** User without permanent credentials, for temporary access
- **Assumption:** When you assume a role, you give up your previous permissions
- **Use Cases:** Cross-account access, service permissions, federated access
- **Benefits:** Automatic credential rotation, enhanced security

### Policy Types

#### Identity-Based Policies
- **Managed Policies:** Standalone, reusable across multiple entities
- **Inline Policies:** Directly attached to a single user, group, or role
- **AWS Managed:** Predefined by AWS, automatically updated
- **Customer Managed:** Created and maintained by you

#### Resource-Based Policies
- **Attachment:** Directly to resources (S3 buckets, SQS queues)
- **Purpose:** Control who can access the resource
- **Cross-Account:** Enable access from other AWS accounts

#### Permission Boundaries
- **Purpose:** Maximum permissions for users or roles (not available for groups)
- **Function:** Filter to limit effective permissions
- **Use Cases:** Delegated administration, developer sandboxes

#### Service Control Policies (SCPs)
- **Scope:** Organization-level policies across AWS accounts
- **Function:** Deny-only policies (allowlist approach)
- **Important:** Allow in SCP doesn't grant permissions, only prevents denial

#### Session Policies
- **Purpose:** Passed when assuming a role via STS
- **Function:** Further restrict permissions during session
- **Use Cases:** Temporary additional restrictions

## Permission Evaluation

**Permission Logic:** Always the minimal intersection of all available rules/restrictions

```
Effective Permissions = 
  Identity-Based Policies ∩ 
  Permission Boundaries ∩ 
  Resource-Based Policies ∩ 
  SCPs ∩ 
  Session Policies
```

### Evaluation Flow
1. **Explicit Deny:** Any explicit deny overrides everything
2. **SCPs:** Organization boundaries applied
3. **Resource-Based:** Resource policies evaluated
4. **Identity-Based:** User/role policies applied
5. **Permission Boundaries:** Maximum permissions filtered
6. **Session Policies:** Additional restrictions applied

## Security Features

### Multi-Factor Authentication (MFA)
- **Virtual MFA:** Authenticator apps (Google Authenticator, Authy)
- **Hardware MFA:** Physical devices (YubiKey, Gemalto)
- **U2F Security Keys:** FIDO-compliant hardware tokens
- **SMS/Voice:** Deprecated, use virtual or hardware MFA

### Access Keys Management
- **Rotation:** Regular rotation for enhanced security
- **Temporary Credentials:** Preferred over long-term access keys
- **Least Privilege:** Minimal required permissions
- **Monitoring:** CloudTrail for access key usage

### Password Policies
- **Complexity Requirements:** Length, character types, case sensitivity
- **Rotation:** Mandatory password changes
- **Reuse Prevention:** Previous password restrictions
- **Account Lockout:** Failed attempt protections

## Monitoring and Auditing

### IAM Credentials Report
- **Scope:** Account-level report
- **Content:** All users and their credential statuses
- **Information:** Password age, MFA status, access key rotation
- **Frequency:** Generated on-demand, useful for compliance audits

### IAM Access Advisor
- **Scope:** User-level report
- **Content:** User permissions and service access timestamps
- **Purpose:** Identify unused permissions for rightsizing
- **Use Cases:** Permission cleanup, compliance reviews

### IAM Access Analyzer
- **Purpose:** Identify resources shared publicly or with external accounts
- **Analysis:** Resource-based policies and their access grants
- **Alerts:** Unintended external access notifications
- **Integration:** Security Hub and CloudWatch for monitoring

### CloudTrail Integration
- **API Logging:** All IAM API calls tracked
- **Authentication Events:** Sign-in attempts and role assumptions
- **Permission Changes:** Policy modifications and attachments
- **Compliance:** Audit trail for security reviews

## Best Practices

### Security
- **Principle of Least Privilege:** Grant minimal required permissions
- **Role-Based Access:** Use roles instead of users for services
- **Regular Audits:** Review permissions and remove unused access
- **Strong Authentication:** Enable MFA for all human users

### Operational
- **Policy Versioning:** Use managed policies with version control
- **Descriptive Naming:** Clear policy and role names
- **Tagging Strategy:** Consistent tags for cost and governance
- **Permission Boundaries:** Prevent privilege escalation

### Automation
- **Infrastructure as Code:** IAM resources in CloudFormation/Terraform
- **Automated Rotation:** Regular access key and password rotation
- **Compliance Monitoring:** Automated policy compliance checks
- **Break-Glass Access:** Emergency access procedures

## Common Patterns

### Service Roles
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Cross-Account Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```

### Conditional Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "203.0.113.0/24"
        }
      }
    }
  ]
}
```

## Enterprise Security Management Framework

### Advanced Identity Governance Engine

```python
# enterprise-iam-manager.py - Advanced IAM security and governance framework
import boto3
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import re
import concurrent.futures
import hashlib

class AccessLevel(Enum):
    READ_ONLY = "read-only"
    POWER_USER = "power-user"
    ADMIN = "admin"
    BREAK_GLASS = "break-glass"

class CredentialType(Enum):
    TEMPORARY = "temporary"
    SERVICE_LINKED = "service-linked"
    PERMANENT = "permanent"
    FEDERATED = "federated"

@dataclass
class SecurityPolicyRule:
    name: str
    description: str
    severity: str
    condition: callable
    remediation: str
    auto_fix: bool = False

class EnterpriseIAMManager:
    """
    Enterprise-grade IAM management with advanced security governance,
    automated compliance, policy optimization, and threat detection.
    """
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.iam = boto3.client('iam', region_name=region_name)
        self.sts = boto3.client('sts', region_name=region_name)
        self.organizations = boto3.client('organizations', region_name=region_name)
        self.cloudtrail = boto3.client('cloudtrail', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Security governance rules
        self.security_policies = self._initialize_security_policies()
        
        # Permission templates
        self.permission_templates = self._load_permission_templates()
        
        # Monitoring metrics
        self.metrics_namespace = 'Enterprise/IAM/Security'
    
    def _initialize_security_policies(self) -> List[SecurityPolicyRule]:
        """Initialize comprehensive security governance policies"""
        
        return [
            SecurityPolicyRule(
                name="unused_credentials",
                description="Identify and manage unused IAM credentials",
                severity="medium",
                condition=lambda user: self._check_unused_credentials(user),
                remediation="Disable or remove unused access keys and users",
                auto_fix=True
            ),
            SecurityPolicyRule(
                name="overprivileged_users",
                description="Detect users with excessive permissions",
                severity="high",
                condition=lambda user: self._check_overprivileged_access(user),
                remediation="Apply permission boundaries and least privilege principles",
                auto_fix=False
            ),
            SecurityPolicyRule(
                name="mfa_compliance",
                description="Ensure MFA is enabled for all human users",
                severity="high",
                condition=lambda user: self._check_mfa_compliance(user),
                remediation="Enable MFA devices for non-compliant users",
                auto_fix=False
            ),
            SecurityPolicyRule(
                name="cross_account_risk",
                description="Monitor risky cross-account access patterns",
                severity="critical",
                condition=lambda role: self._check_cross_account_risks(role),
                remediation="Review and restrict cross-account trust relationships",
                auto_fix=False
            ),
            SecurityPolicyRule(
                name="root_account_usage",
                description="Detect root account usage patterns",
                severity="critical",
                condition=lambda event: self._check_root_account_usage(event),
                remediation="Eliminate root account usage for operational tasks",
                auto_fix=False
            ),
            SecurityPolicyRule(
                name="policy_complexity",
                description="Identify overly complex or broad policies",
                severity="medium",
                condition=lambda policy: self._check_policy_complexity(policy),
                remediation="Simplify policies and apply principle of least privilege",
                auto_fix=False
            )
        ]
    
    def _load_permission_templates(self) -> Dict[str, Dict]:
        """Load standardized permission templates for different access levels"""
        
        return {
            "developer_readonly": {
                "description": "Read-only access for developers",
                "policies": [
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "ec2:Describe*",
                                    "s3:GetObject",
                                    "s3:ListBucket",
                                    "logs:Describe*",
                                    "logs:Get*",
                                    "cloudwatch:Describe*",
                                    "cloudwatch:Get*",
                                    "cloudwatch:List*"
                                ],
                                "Resource": "*"
                            }
                        ]
                    }
                ]
            },
            "developer_sandbox": {
                "description": "Sandbox environment access for developers",
                "policies": [
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "ec2:*",
                                    "s3:*",
                                    "lambda:*",
                                    "cloudformation:*"
                                ],
                                "Resource": "*",
                                "Condition": {
                                    "StringEquals": {
                                        "aws:RequestedRegion": ["us-west-2"],
                                        "ec2:ResourceTag/Environment": "sandbox"
                                    }
                                }
                            }
                        ]
                    }
                ]
            },
            "cicd_deployment": {
                "description": "CI/CD pipeline deployment permissions",
                "policies": [
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "cloudformation:CreateStack",
                                    "cloudformation:UpdateStack",
                                    "cloudformation:DeleteStack",
                                    "cloudformation:DescribeStacks",
                                    "s3:GetObject",
                                    "s3:PutObject",
                                    "lambda:UpdateFunctionCode",
                                    "lambda:UpdateFunctionConfiguration",
                                    "ecs:UpdateService",
                                    "ecs:DescribeServices"
                                ],
                                "Resource": "*",
                                "Condition": {
                                    "StringEquals": {
                                        "aws:RequestedRegion": ["us-west-2", "us-east-1"]
                                    }
                                }
                            }
                        ]
                    }
                ]
            },
            "monitoring_service": {
                "description": "Monitoring and observability service permissions",
                "policies": [
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "cloudwatch:*",
                                    "logs:*",
                                    "xray:*",
                                    "health:*",
                                    "support:*"
                                ],
                                "Resource": "*"
                            }
                        ]
                    }
                ]
            }
        }
    
    def perform_security_audit(self, scope: str = "all") -> Dict[str, Any]:
        """Perform comprehensive security audit of IAM configuration"""
        
        audit_results = {
            'audit_id': f"iam-audit-{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'scope': scope,
            'findings': {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            },
            'compliance_score': 0,
            'recommendations': [],
            'metrics': {}
        }
        
        try:
            # Audit users
            if scope in ["all", "users"]:
                self.logger.info("Auditing IAM users...")
                user_findings = self._audit_users()
                self._categorize_findings(user_findings, audit_results['findings'])
            
            # Audit roles
            if scope in ["all", "roles"]:
                self.logger.info("Auditing IAM roles...")
                role_findings = self._audit_roles()
                self._categorize_findings(role_findings, audit_results['findings'])
            
            # Audit policies
            if scope in ["all", "policies"]:
                self.logger.info("Auditing IAM policies...")
                policy_findings = self._audit_policies()
                self._categorize_findings(policy_findings, audit_results['findings'])
            
            # Audit access patterns
            if scope in ["all", "access"]:
                self.logger.info("Auditing access patterns...")
                access_findings = self._audit_access_patterns()
                self._categorize_findings(access_findings, audit_results['findings'])
            
            # Calculate compliance score
            audit_results['compliance_score'] = self._calculate_compliance_score(audit_results['findings'])
            
            # Generate recommendations
            audit_results['recommendations'] = self._generate_security_recommendations(audit_results['findings'])
            
            # Collect metrics
            audit_results['metrics'] = self._collect_security_metrics()
            
            # Send metrics to CloudWatch
            self._send_audit_metrics(audit_results)
            
            return audit_results
            
        except Exception as e:
            self.logger.error(f"Security audit failed: {e}")
            audit_results['error'] = str(e)
            return audit_results
    
    def _audit_users(self) -> List[Dict[str, Any]]:
        """Audit all IAM users for security compliance"""
        
        findings = []
        
        try:
            paginator = self.iam.get_paginator('list_users')
            
            for page in paginator.paginate():
                for user in page['Users']:
                    user_name = user['UserName']
                    
                    # Check each security policy
                    for policy in self.security_policies:
                        if policy.condition(user):
                            findings.append({
                                'type': 'user',
                                'resource': user_name,
                                'policy': policy.name,
                                'severity': policy.severity,
                                'description': policy.description,
                                'remediation': policy.remediation,
                                'auto_fix': policy.auto_fix,
                                'details': self._get_user_details(user_name)
                            })
            
        except Exception as e:
            self.logger.error(f"User audit failed: {e}")
            findings.append({
                'type': 'audit_error',
                'resource': 'users',
                'severity': 'high',
                'description': f"Failed to audit users: {e}"
            })
        
        return findings
    
    def _audit_roles(self) -> List[Dict[str, Any]]:
        """Audit all IAM roles for security compliance"""
        
        findings = []
        
        try:
            paginator = self.iam.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page['Roles']:
                    role_name = role['RoleName']
                    
                    # Skip service-linked roles
                    if role.get('Path', '').startswith('/aws-service-role/'):
                        continue
                    
                    # Check cross-account access risks
                    trust_policy = role.get('AssumeRolePolicyDocument', {})
                    if self._has_risky_cross_account_access(trust_policy):
                        findings.append({
                            'type': 'role',
                            'resource': role_name,
                            'policy': 'cross_account_risk',
                            'severity': 'high',
                            'description': 'Role has risky cross-account access configuration',
                            'remediation': 'Review and restrict cross-account trust relationships',
                            'details': {
                                'trust_policy': trust_policy,
                                'last_used': self._get_role_last_used(role_name)
                            }
                        })
                    
                    # Check for overly broad permissions
                    if self._has_admin_permissions(role_name):
                        findings.append({
                            'type': 'role',
                            'resource': role_name,
                            'policy': 'overprivileged_access',
                            'severity': 'medium',
                            'description': 'Role has administrative permissions',
                            'remediation': 'Apply principle of least privilege',
                            'details': self._get_role_permissions_summary(role_name)
                        })
            
        except Exception as e:
            self.logger.error(f"Role audit failed: {e}")
            findings.append({
                'type': 'audit_error',
                'resource': 'roles',
                'severity': 'high',
                'description': f"Failed to audit roles: {e}"
            })
        
        return findings
    
    def _audit_policies(self) -> List[Dict[str, Any]]:
        """Audit managed policies for security best practices"""
        
        findings = []
        
        try:
            # Audit customer managed policies
            paginator = self.iam.get_paginator('list_policies')
            
            for page in paginator.paginate(Scope='Local'):  # Customer managed only
                for policy in page['Policies']:
                    policy_arn = policy['Arn']
                    policy_name = policy['PolicyName']
                    
                    # Get policy document
                    policy_doc = self._get_policy_document(policy_arn, policy['DefaultVersionId'])
                    
                    if not policy_doc:
                        continue
                    
                    # Check for overly broad permissions
                    if self._policy_has_wildcard_actions(policy_doc):
                        findings.append({
                            'type': 'policy',
                            'resource': policy_name,
                            'policy': 'broad_permissions',
                            'severity': 'medium',
                            'description': 'Policy contains wildcard actions',
                            'remediation': 'Specify explicit actions instead of wildcards',
                            'details': {
                                'policy_arn': policy_arn,
                                'wildcard_statements': self._get_wildcard_statements(policy_doc)
                            }
                        })
                    
                    # Check for overly complex policies
                    complexity_score = self._calculate_policy_complexity(policy_doc)
                    if complexity_score > 50:  # Threshold for complexity
                        findings.append({
                            'type': 'policy',
                            'resource': policy_name,
                            'policy': 'policy_complexity',
                            'severity': 'low',
                            'description': f'Policy complexity score: {complexity_score}',
                            'remediation': 'Simplify policy structure and conditions',
                            'details': {
                                'complexity_score': complexity_score,
                                'statement_count': len(policy_doc.get('Statement', [])),
                                'condition_count': self._count_conditions(policy_doc)
                            }
                        })
            
        except Exception as e:
            self.logger.error(f"Policy audit failed: {e}")
            findings.append({
                'type': 'audit_error',
                'resource': 'policies',
                'severity': 'high',
                'description': f"Failed to audit policies: {e}"
            })
        
        return findings
    
    def _audit_access_patterns(self) -> List[Dict[str, Any]]:
        """Audit access patterns using CloudTrail data"""
        
        findings = []
        
        try:
            # Analyze last 30 days of access patterns
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            
            # Look for unusual access patterns
            events = self._get_cloudtrail_events(start_time, end_time, ['AssumeRole', 'GetSessionToken'])
            
            # Analyze root account usage
            root_events = [e for e in events if e.get('userIdentity', {}).get('type') == 'Root']
            if root_events:
                findings.append({
                    'type': 'access_pattern',
                    'resource': 'root_account',
                    'policy': 'root_account_usage',
                    'severity': 'critical',
                    'description': f'Root account used {len(root_events)} times in last 30 days',
                    'remediation': 'Eliminate root account usage for operational tasks',
                    'details': {
                        'event_count': len(root_events),
                        'recent_events': root_events[:5]  # Last 5 events
                    }
                })
            
            # Analyze unusual cross-account access
            cross_account_events = self._identify_cross_account_access(events)
            if cross_account_events:
                findings.append({
                    'type': 'access_pattern',
                    'resource': 'cross_account_access',
                    'policy': 'unusual_access',
                    'severity': 'medium',
                    'description': f'Detected {len(cross_account_events)} cross-account access attempts',
                    'remediation': 'Review cross-account access patterns for legitimacy',
                    'details': {
                        'event_count': len(cross_account_events),
                        'accounts': list(set([e.get('recipientAccountId') for e in cross_account_events]))
                    }
                })
            
        except Exception as e:
            self.logger.error(f"Access pattern audit failed: {e}")
            findings.append({
                'type': 'audit_error',
                'resource': 'access_patterns',
                'severity': 'medium',
                'description': f"Failed to audit access patterns: {e}"
            })
        
        return findings
    
    def create_role_with_governance(self, role_config: Dict[str, Any]) -> str:
        """Create IAM role with enterprise governance controls"""
        
        role_name = role_config['name']
        
        try:
            # Validate role configuration
            self._validate_role_config(role_config)
            
            # Generate trust policy with security controls
            trust_policy = self._generate_secure_trust_policy(role_config)
            
            # Create role
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=role_config.get('description', ''),
                MaxSessionDuration=role_config.get('max_session_duration', 3600),
                PermissionsBoundary=role_config.get('permission_boundary'),
                Tags=self._generate_governance_tags(role_config)
            )
            
            # Attach policies with validation
            for policy_arn in role_config.get('managed_policies', []):
                self._attach_policy_with_validation(role_name, policy_arn)
            
            # Create inline policies if specified
            for policy_name, policy_doc in role_config.get('inline_policies', {}).items():
                self._create_inline_policy_with_validation(role_name, policy_name, policy_doc)
            
            self.logger.info(f"Created role with governance: {role_name}")
            
            # Send metrics
            self._send_role_creation_metrics(role_name, role_config)
            
            return response['Role']['Arn']
            
        except Exception as e:
            self.logger.error(f"Failed to create role {role_name}: {e}")
            raise
    
    def implement_least_privilege_analysis(self, target: str, target_type: str = "user") -> Dict[str, Any]:
        """Analyze and recommend least privilege permissions"""
        
        analysis_results = {
            'target': target,
            'target_type': target_type,
            'analysis_id': f"privilege-analysis-{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'current_permissions': {},
            'used_permissions': {},
            'unused_permissions': {},
            'recommendations': [],
            'optimized_policy': None
        }
        
        try:
            # Get current permissions
            current_permissions = self._get_current_permissions(target, target_type)
            analysis_results['current_permissions'] = current_permissions
            
            # Analyze permission usage from CloudTrail
            used_permissions = self._analyze_permission_usage(target, target_type)
            analysis_results['used_permissions'] = used_permissions
            
            # Identify unused permissions
            unused_permissions = self._identify_unused_permissions(current_permissions, used_permissions)
            analysis_results['unused_permissions'] = unused_permissions
            
            # Generate recommendations
            recommendations = self._generate_privilege_recommendations(
                current_permissions, used_permissions, unused_permissions
            )
            analysis_results['recommendations'] = recommendations
            
            # Create optimized policy
            optimized_policy = self._create_optimized_policy(used_permissions, target_type)
            analysis_results['optimized_policy'] = optimized_policy
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Least privilege analysis failed for {target}: {e}")
            analysis_results['error'] = str(e)
            return analysis_results
    
    def setup_automated_governance(self, governance_config: Dict[str, Any]) -> None:
        """Setup automated IAM governance and compliance monitoring"""
        
        try:
            # Create CloudWatch rules for monitoring
            self._create_governance_monitoring_rules(governance_config)
            
            # Setup automatic remediation
            self._setup_automatic_remediation(governance_config)
            
            # Configure compliance reporting
            self._setup_compliance_reporting(governance_config)
            
            # Create governance dashboard
            self._create_governance_dashboard(governance_config)
            
            self.logger.info("Automated IAM governance setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup automated governance: {e}")
            raise
    
    def _check_unused_credentials(self, user: Dict) -> bool:
        """Check if user has unused credentials"""
        
        try:
            user_name = user['UserName']
            
            # Get credential report for user
            report = self.iam.get_credential_report()
            # Parse report to check last used dates
            
            # Check access keys
            access_keys = self.iam.list_access_keys(UserName=user_name)
            for key in access_keys['AccessKeyMetadata']:
                last_used = self.iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                if 'LastUsedDate' not in last_used['AccessKeyLastUsed']:
                    return True  # Never used
                
                days_since_use = (datetime.now(last_used['AccessKeyLastUsed']['LastUsedDate'].tzinfo) - 
                                last_used['AccessKeyLastUsed']['LastUsedDate']).days
                if days_since_use > 90:  # Unused for 90+ days
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check unused credentials for {user.get('UserName', 'unknown')}: {e}")
            return False
    
    def _check_overprivileged_access(self, user: Dict) -> bool:
        """Check if user has excessive permissions"""
        
        try:
            user_name = user['UserName']
            
            # Check for admin policies
            attached_policies = self.iam.list_attached_user_policies(UserName=user_name)
            for policy in attached_policies['AttachedPolicies']:
                if 'admin' in policy['PolicyName'].lower() or policy['PolicyArn'].endswith('AdministratorAccess'):
                    return True
            
            # Check group memberships
            groups = self.iam.get_groups_for_user(UserName=user_name)
            for group in groups['Groups']:
                group_policies = self.iam.list_attached_group_policies(GroupName=group['GroupName'])
                for policy in group_policies['AttachedPolicies']:
                    if 'admin' in policy['PolicyName'].lower():
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check overprivileged access for {user.get('UserName', 'unknown')}: {e}")
            return False
    
    def _check_mfa_compliance(self, user: Dict) -> bool:
        """Check if user is compliant with MFA requirements"""
        
        try:
            user_name = user['UserName']
            
            # Check if user has console access
            try:
                login_profile = self.iam.get_login_profile(UserName=user_name)
                # User has console access, check MFA
                mfa_devices = self.iam.list_mfa_devices(UserName=user_name)
                return len(mfa_devices['MFADevices']) == 0  # Return True if non-compliant (no MFA)
            except self.iam.exceptions.NoSuchEntityException:
                # No console access, MFA not required
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to check MFA compliance for {user.get('UserName', 'unknown')}: {e}")
            return False
    
    def _generate_secure_trust_policy(self, role_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trust policy with security controls"""
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": []
        }
        
        for principal_config in role_config.get('trusted_principals', []):
            statement = {
                "Effect": "Allow",
                "Principal": principal_config['principal'],
                "Action": "sts:AssumeRole"
            }
            
            # Add conditions for enhanced security
            conditions = {}
            
            # External ID for cross-account access
            if 'external_id' in principal_config:
                conditions["StringEquals"] = {"sts:ExternalId": principal_config['external_id']}
            
            # MFA requirement
            if principal_config.get('require_mfa', False):
                conditions["Bool"] = {"aws:MultiFactorAuthPresent": "true"}
            
            # Session duration limits
            if 'max_session_duration' in principal_config:
                conditions["NumericLessThan"] = {
                    "aws:TokenIssueTime": str(int(time.time()) + principal_config['max_session_duration'])
                }
            
            # Source IP restrictions
            if 'allowed_ips' in principal_config:
                conditions["IpAddress"] = {"aws:SourceIp": principal_config['allowed_ips']}
            
            if conditions:
                statement["Condition"] = conditions
            
            trust_policy["Statement"].append(statement)
        
        return trust_policy
    
    def _categorize_findings(self, findings: List[Dict], categorized: Dict[str, List]) -> None:
        """Categorize findings by severity"""
        
        for finding in findings:
            severity = finding.get('severity', 'low')
            if severity in categorized:
                categorized[severity].append(finding)
    
    def _calculate_compliance_score(self, findings: Dict[str, List]) -> float:
        """Calculate overall compliance score based on findings"""
        
        total_score = 100
        
        # Deduct points based on severity
        severity_weights = {
            'critical': 25,
            'high': 15,
            'medium': 5,
            'low': 1
        }
        
        for severity, weight in severity_weights.items():
            deduction = len(findings.get(severity, [])) * weight
            total_score -= deduction
        
        return max(0, total_score)
    
    def _generate_security_recommendations(self, findings: Dict[str, List]) -> List[str]:
        """Generate security recommendations based on findings"""
        
        recommendations = []
        
        # Critical findings
        if findings.get('critical'):
            recommendations.append("URGENT: Address critical security findings immediately")
            for finding in findings['critical']:
                recommendations.append(f"• {finding.get('remediation', 'Review critical finding')}")
        
        # High severity findings
        if findings.get('high'):
            recommendations.append("HIGH PRIORITY: Address high-severity security issues")
            for finding in findings['high'][:3]:  # Top 3
                recommendations.append(f"• {finding.get('remediation', 'Review high-severity finding')}")
        
        # General recommendations
        recommendations.extend([
            "Implement automated IAM access review processes",
            "Setup continuous compliance monitoring with automated remediation",
            "Establish regular security training for development teams",
            "Create incident response procedures for IAM security events",
            "Implement IAM governance policies using AWS Organizations SCPs"
        ])
        
        return recommendations
    
    def _collect_security_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive IAM security metrics"""
        
        metrics = {}
        
        try:
            # Count entities
            users_response = self.iam.list_users()
            roles_response = self.iam.list_roles()
            policies_response = self.iam.list_policies(Scope='Local')
            
            metrics['entity_counts'] = {
                'users': len(users_response['Users']),
                'roles': len(roles_response['Roles']),
                'customer_managed_policies': len(policies_response['Policies'])
            }
            
            # MFA compliance
            mfa_enabled_users = 0
            for user in users_response['Users']:
                try:
                    mfa_devices = self.iam.list_mfa_devices(UserName=user['UserName'])
                    if mfa_devices['MFADevices']:
                        mfa_enabled_users += 1
                except:
                    continue
            
            metrics['mfa_compliance'] = {
                'enabled_users': mfa_enabled_users,
                'total_users': len(users_response['Users']),
                'compliance_rate': mfa_enabled_users / max(1, len(users_response['Users'])) * 100
            }
            
            # Access key metrics
            total_keys = 0
            unused_keys = 0
            for user in users_response['Users']:
                try:
                    keys = self.iam.list_access_keys(UserName=user['UserName'])
                    total_keys += len(keys['AccessKeyMetadata'])
                    
                    for key in keys['AccessKeyMetadata']:
                        last_used = self.iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                        if 'LastUsedDate' not in last_used['AccessKeyLastUsed']:
                            unused_keys += 1
                except:
                    continue
            
            metrics['access_keys'] = {
                'total_keys': total_keys,
                'unused_keys': unused_keys,
                'utilization_rate': (total_keys - unused_keys) / max(1, total_keys) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect security metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _send_audit_metrics(self, audit_results: Dict[str, Any]) -> None:
        """Send audit metrics to CloudWatch"""
        
        try:
            metric_data = []
            
            # Compliance score
            metric_data.append({
                'MetricName': 'ComplianceScore',
                'Value': audit_results['compliance_score'],
                'Unit': 'Percent'
            })
            
            # Finding counts by severity
            for severity, findings in audit_results['findings'].items():
                metric_data.append({
                    'MetricName': 'FindingCount',
                    'Value': len(findings),
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'Severity', 'Value': severity}]
                })
            
            # Send metrics
            self.cloudwatch.put_metric_data(
                Namespace=self.metrics_namespace,
                MetricData=metric_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send audit metrics: {e}")

# Example usage
if __name__ == "__main__":
    iam_manager = EnterpriseIAMManager()
    
    # Perform comprehensive security audit
    audit_results = iam_manager.perform_security_audit()
    
    print(f"Security audit completed with compliance score: {audit_results['compliance_score']}%")
    print(f"Critical findings: {len(audit_results['findings']['critical'])}")
    print(f"High-severity findings: {len(audit_results['findings']['high'])}")
    
    # Create a role with enterprise governance
    role_config = {
        'name': 'enterprise-deployment-role',
        'description': 'Deployment role with enterprise governance controls',
        'trusted_principals': [
            {
                'principal': {'Service': 'codebuild.amazonaws.com'},
                'require_mfa': False
            },
            {
                'principal': {'AWS': 'arn:aws:iam::123456789012:root'},
                'external_id': 'deployment-external-id',
                'require_mfa': True,
                'allowed_ips': ['203.0.113.0/24']
            }
        ],
        'managed_policies': [
            'arn:aws:iam::aws:policy/PowerUserAccess'
        ],
        'permission_boundary': 'arn:aws:iam::123456789012:policy/DeveloperBoundary',
        'max_session_duration': 3600
    }
    
    role_arn = iam_manager.create_role_with_governance(role_config)
    print(f"Created enterprise role: {role_arn}")
```

### Zero Trust Identity Architecture

```python
# zero-trust-identity.py - Zero Trust identity and access management framework
import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import ipaddress
import re
import hashlib

class ZeroTrustIdentityManager:
    """
    Zero Trust identity management with continuous verification,
    contextual access controls, and adaptive security policies.
    """
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.iam = boto3.client('iam', region_name=region_name)
        self.cognito_idp = boto3.client('cognito-idp', region_name=region_name)
        self.cloudtrail = boto3.client('cloudtrail', region_name=region_name)
        self.waf = boto3.client('wafv2', region_name=region_name)
        self.guardduty = boto3.client('guardduty', region_name=region_name)
        
        # Zero Trust policies
        self.trust_policies = {
            'device_trust': {
                'required_attributes': ['device_id', 'device_fingerprint', 'os_version'],
                'trusted_devices': [],
                'certificate_required': True
            },
            'location_trust': {
                'allowed_countries': ['US', 'CA', 'GB'],
                'allowed_ip_ranges': [],
                'geofencing_enabled': True
            },
            'behavioral_trust': {
                'anomaly_detection': True,
                'session_patterns': True,
                'access_velocity_limits': True
            }
        }
        
        # Risk scoring thresholds
        self.risk_thresholds = {
            'low': 25,
            'medium': 50,
            'high': 75,
            'critical': 90
        }
    
    def evaluate_access_request(self, access_context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate access request using Zero Trust principles"""
        
        evaluation_result = {
            'request_id': f"zt-eval-{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'decision': 'DENY',  # Default deny
            'risk_score': 0,
            'verification_results': {},
            'required_actions': [],
            'session_constraints': {}
        }
        
        try:
            # Extract context
            user_identity = access_context.get('user_identity', {})
            device_info = access_context.get('device_info', {})
            location_info = access_context.get('location_info', {})
            request_info = access_context.get('request_info', {})
            
            # Perform continuous verification
            verification_results = {
                'identity_verification': self._verify_identity(user_identity),
                'device_verification': self._verify_device(device_info),
                'location_verification': self._verify_location(location_info),
                'behavioral_verification': self._verify_behavior(user_identity, request_info),
                'resource_verification': self._verify_resource_access(request_info)
            }
            
            evaluation_result['verification_results'] = verification_results
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(verification_results, access_context)
            evaluation_result['risk_score'] = risk_score
            
            # Make access decision
            decision, constraints = self._make_access_decision(risk_score, verification_results)
            evaluation_result['decision'] = decision
            evaluation_result['session_constraints'] = constraints
            
            # Determine required actions
            required_actions = self._determine_required_actions(risk_score, verification_results)
            evaluation_result['required_actions'] = required_actions
            
            # Log evaluation for audit
            self._log_access_evaluation(evaluation_result, access_context)
            
            return evaluation_result
            
        except Exception as e:
            evaluation_result['error'] = str(e)
            evaluation_result['decision'] = 'DENY'
            return evaluation_result
    
    def _verify_identity(self, user_identity: Dict[str, Any]) -> Dict[str, Any]:
        """Verify user identity with multi-factor authentication"""
        
        verification = {
            'verified': False,
            'confidence_score': 0,
            'factors_verified': [],
            'issues': []
        }
        
        try:
            user_id = user_identity.get('user_id')
            if not user_id:
                verification['issues'].append('Missing user identifier')
                return verification
            
            # Check primary authentication factor
            primary_auth = user_identity.get('primary_auth', {})
            if primary_auth.get('method') in ['password', 'certificate']:
                verification['factors_verified'].append('primary_auth')
                verification['confidence_score'] += 30
            
            # Check MFA factors
            mfa_factors = user_identity.get('mfa_factors', [])
            for factor in mfa_factors:
                if factor.get('type') in ['totp', 'hardware_token', 'biometric']:
                    verification['factors_verified'].append(factor['type'])
                    verification['confidence_score'] += 35
            
            # Check continuous authentication
            continuous_auth = user_identity.get('continuous_auth', {})
            if continuous_auth.get('active'):
                verification['factors_verified'].append('continuous_auth')
                verification['confidence_score'] += 20
            
            # Identity verification threshold
            verification['verified'] = verification['confidence_score'] >= 60
            
        except Exception as e:
            verification['issues'].append(f"Identity verification error: {e}")
        
        return verification
    
    def _verify_device(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Verify device trust and security posture"""
        
        verification = {
            'trusted': False,
            'compliance_score': 0,
            'trust_factors': [],
            'risks': []
        }
        
        try:
            device_id = device_info.get('device_id')
            if not device_id:
                verification['risks'].append('Device not identified')
                return verification
            
            # Check device registration
            if self._is_device_registered(device_id):
                verification['trust_factors'].append('registered_device')
                verification['compliance_score'] += 25
            else:
                verification['risks'].append('Unregistered device')
            
            # Check device certificate
            certificate = device_info.get('certificate')
            if certificate and self._validate_device_certificate(certificate):
                verification['trust_factors'].append('valid_certificate')
                verification['compliance_score'] += 30
            else:
                verification['risks'].append('Invalid or missing device certificate')
            
            # Check device security posture
            security_posture = device_info.get('security_posture', {})
            
            # OS version check
            os_version = security_posture.get('os_version')
            if os_version and self._is_os_version_supported(os_version):
                verification['trust_factors'].append('supported_os')
                verification['compliance_score'] += 15
            else:
                verification['risks'].append('Unsupported or outdated OS version')
            
            # Antivirus status
            if security_posture.get('antivirus_status') == 'active':
                verification['trust_factors'].append('antivirus_active')
                verification['compliance_score'] += 10
            else:
                verification['risks'].append('Antivirus not active')
            
            # Encryption status
            if security_posture.get('disk_encryption') == 'enabled':
                verification['trust_factors'].append('disk_encrypted')
                verification['compliance_score'] += 10
            else:
                verification['risks'].append('Disk encryption not enabled')
            
            # Jailbreak/root detection
            if security_posture.get('jailbroken') or security_posture.get('rooted'):
                verification['risks'].append('Device compromised (jailbroken/rooted)')
                verification['compliance_score'] -= 50
            
            verification['trusted'] = verification['compliance_score'] >= 70
            
        except Exception as e:
            verification['risks'].append(f"Device verification error: {e}")
        
        return verification
    
    def _verify_location(self, location_info: Dict[str, Any]) -> Dict[str, Any]:
        """Verify location and geolocation context"""
        
        verification = {
            'trusted_location': False,
            'location_score': 0,
            'location_factors': [],
            'location_risks': []
        }
        
        try:
            # IP address verification
            ip_address = location_info.get('ip_address')
            if ip_address:
                if self._is_ip_in_trusted_ranges(ip_address):
                    verification['location_factors'].append('trusted_ip_range')
                    verification['location_score'] += 40
                elif self._is_ip_from_tor_or_vpn(ip_address):
                    verification['location_risks'].append('TOR/VPN IP detected')
                    verification['location_score'] -= 30
            
            # Geographic location
            geo_location = location_info.get('geo_location', {})
            country = geo_location.get('country')
            if country:
                if country in self.trust_policies['location_trust']['allowed_countries']:
                    verification['location_factors'].append('trusted_country')
                    verification['location_score'] += 30
                else:
                    verification['location_risks'].append(f'Access from untrusted country: {country}')
                    verification['location_score'] -= 20
            
            # Impossible travel detection
            previous_location = location_info.get('previous_location')
            if previous_location and self._detect_impossible_travel(geo_location, previous_location):
                verification['location_risks'].append('Impossible travel detected')
                verification['location_score'] -= 50
            
            # Network reputation
            network_reputation = location_info.get('network_reputation', {})
            if network_reputation.get('malicious_activity'):
                verification['location_risks'].append('Network with malicious activity history')
                verification['location_score'] -= 40
            
            verification['trusted_location'] = verification['location_score'] >= 50
            
        except Exception as e:
            verification['location_risks'].append(f"Location verification error: {e}")
        
        return verification
    
    def _verify_behavior(self, user_identity: Dict[str, Any], request_info: Dict[str, Any]) -> Dict[str, Any]:
        """Verify behavioral patterns and detect anomalies"""
        
        verification = {
            'normal_behavior': True,
            'behavior_score': 100,
            'behavioral_factors': [],
            'anomalies': []
        }
        
        try:
            user_id = user_identity.get('user_id')
            if not user_id:
                return verification
            
            # Access time patterns
            access_time = datetime.now()
            if self._is_unusual_access_time(user_id, access_time):
                verification['anomalies'].append('Unusual access time')
                verification['behavior_score'] -= 20
            else:
                verification['behavioral_factors'].append('normal_access_time')
            
            # Resource access patterns
            requested_resource = request_info.get('resource')
            if requested_resource and self._is_unusual_resource_access(user_id, requested_resource):
                verification['anomalies'].append('Unusual resource access')
                verification['behavior_score'] -= 25
            else:
                verification['behavioral_factors'].append('normal_resource_access')
            
            # Access velocity
            if self._detect_high_access_velocity(user_id):
                verification['anomalies'].append('High access velocity detected')
                verification['behavior_score'] -= 30
            
            # Failed authentication attempts
            recent_failures = self._get_recent_auth_failures(user_id)
            if recent_failures > 3:
                verification['anomalies'].append(f'{recent_failures} recent authentication failures')
                verification['behavior_score'] -= 15
            
            verification['normal_behavior'] = verification['behavior_score'] >= 70
            
        except Exception as e:
            verification['anomalies'].append(f"Behavior verification error: {e}")
        
        return verification
    
    def _calculate_risk_score(self, verification_results: Dict[str, Dict], 
                            access_context: Dict[str, Any]) -> int:
        """Calculate overall risk score for access request"""
        
        risk_score = 0
        
        # Identity risk
        identity_verification = verification_results.get('identity_verification', {})
        if not identity_verification.get('verified'):
            risk_score += 40
        else:
            confidence = identity_verification.get('confidence_score', 0)
            risk_score += max(0, 40 - (confidence * 0.4))
        
        # Device risk
        device_verification = verification_results.get('device_verification', {})
        if not device_verification.get('trusted'):
            risk_score += 30
        else:
            compliance = device_verification.get('compliance_score', 0)
            risk_score += max(0, 30 - (compliance * 0.3))
        
        # Location risk
        location_verification = verification_results.get('location_verification', {})
        if not location_verification.get('trusted_location'):
            risk_score += 20
        location_score = location_verification.get('location_score', 0)
        if location_score < 0:
            risk_score += abs(location_score) * 0.2
        
        # Behavioral risk
        behavior_verification = verification_results.get('behavioral_verification', {})
        if not behavior_verification.get('normal_behavior'):
            behavior_score = behavior_verification.get('behavior_score', 100)
            risk_score += (100 - behavior_score) * 0.3
        
        # Resource sensitivity
        resource_info = access_context.get('request_info', {})
        resource_sensitivity = resource_info.get('sensitivity_level', 'low')
        sensitivity_multiplier = {
            'low': 1.0,
            'medium': 1.2,
            'high': 1.5,
            'critical': 2.0
        }
        risk_score *= sensitivity_multiplier.get(resource_sensitivity, 1.0)
        
        return min(100, int(risk_score))
    
    def _make_access_decision(self, risk_score: int, 
                            verification_results: Dict[str, Dict]) -> tuple:
        """Make access decision based on risk score and verification results"""
        
        constraints = {}
        
        if risk_score >= self.risk_thresholds['critical']:
            return 'DENY', {}
        elif risk_score >= self.risk_thresholds['high']:
            # High risk - require additional verification
            return 'CONDITIONAL', {
                'additional_mfa_required': True,
                'session_duration': 900,  # 15 minutes
                'continuous_monitoring': True
            }
        elif risk_score >= self.risk_thresholds['medium']:
            # Medium risk - limited access
            return 'ALLOW', {
                'session_duration': 3600,  # 1 hour
                'restricted_actions': ['delete', 'modify'],
                'monitoring_level': 'enhanced'
            }
        else:
            # Low risk - normal access
            return 'ALLOW', {
                'session_duration': 28800,  # 8 hours
                'monitoring_level': 'standard'
            }
    
    def implement_adaptive_policies(self, policy_config: Dict[str, Any]) -> str:
        """Implement adaptive IAM policies based on context and risk"""
        
        policy_name = policy_config['name']
        
        # Generate adaptive policy document
        policy_document = {
            "Version": "2012-10-17",
            "Statement": []
        }
        
        # Base permissions
        base_statement = {
            "Effect": "Allow",
            "Action": policy_config.get('base_actions', []),
            "Resource": policy_config.get('resources', ["*"])
        }
        
        # Add contextual conditions
        conditions = {}
        
        # Time-based access
        if 'time_restrictions' in policy_config:
            time_config = policy_config['time_restrictions']
            conditions["DateGreaterThan"] = {"aws:CurrentTime": time_config['start_time']}
            conditions["DateLessThan"] = {"aws:CurrentTime": time_config['end_time']}
        
        # IP-based access
        if 'ip_restrictions' in policy_config:
            conditions["IpAddress"] = {"aws:SourceIp": policy_config['ip_restrictions']}
        
        # MFA requirement based on resource sensitivity
        if policy_config.get('require_mfa_for_sensitive', True):
            conditions["Bool"] = {"aws:MultiFactorAuthPresent": "true"}
        
        # Device-based access
        if 'device_restrictions' in policy_config:
            # Custom condition for device verification
            conditions["StringEquals"] = {
                "aws:RequestTag/DeviceVerified": "true"
            }
        
        if conditions:
            base_statement["Condition"] = conditions
        
        policy_document["Statement"].append(base_statement)
        
        # Create the policy
        try:
            response = self.iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description=f"Adaptive policy: {policy_config.get('description', '')}",
                Tags=[
                    {'Key': 'PolicyType', 'Value': 'Adaptive'},
                    {'Key': 'ZeroTrust', 'Value': 'true'},
                    {'Key': 'CreatedBy', 'Value': 'ZeroTrustManager'}
                ]
            )
            
            return response['Policy']['Arn']
            
        except Exception as e:
            raise Exception(f"Failed to create adaptive policy {policy_name}: {e}")
    
    def create_zero_trust_dashboard(self) -> Dict[str, Any]:
        """Create comprehensive Zero Trust monitoring dashboard"""
        
        dashboard_config = {
            'name': 'ZeroTrustSecurityDashboard',
            'widgets': [
                {
                    'type': 'metric',
                    'title': 'Access Request Risk Scores',
                    'metrics': [
                        ['ZeroTrust/Access', 'RiskScore', {'stat': 'Average'}],
                        ['ZeroTrust/Access', 'HighRiskRequests', {'stat': 'Sum'}],
                        ['ZeroTrust/Access', 'DeniedRequests', {'stat': 'Sum'}]
                    ]
                },
                {
                    'type': 'metric',
                    'title': 'Device Trust Metrics',
                    'metrics': [
                        ['ZeroTrust/Device', 'TrustedDevices', {'stat': 'Average'}],
                        ['ZeroTrust/Device', 'ComplianceScore', {'stat': 'Average'}],
                        ['ZeroTrust/Device', 'UntrustedAccess', {'stat': 'Sum'}]
                    ]
                },
                {
                    'type': 'metric',
                    'title': 'Identity Verification',
                    'metrics': [
                        ['ZeroTrust/Identity', 'MFACompliance', {'stat': 'Average'}],
                        ['ZeroTrust/Identity', 'VerificationFailures', {'stat': 'Sum'}],
                        ['ZeroTrust/Identity', 'ContinuousAuthActive', {'stat': 'Average'}]
                    ]
                },
                {
                    'type': 'log',
                    'title': 'Security Events',
                    'query': 'fields @timestamp, user_id, risk_score, decision, verification_results | filter decision = "DENY" or risk_score > 75 | sort @timestamp desc | limit 100'
                }
            ]
        }
        
        return dashboard_config

# Example usage for Zero Trust implementation
if __name__ == "__main__":
    zt_manager = ZeroTrustIdentityManager()
    
    # Example access request evaluation
    access_context = {
        'user_identity': {
            'user_id': 'john.doe@company.com',
            'primary_auth': {'method': 'certificate'},
            'mfa_factors': [{'type': 'totp', 'verified': True}],
            'continuous_auth': {'active': True}
        },
        'device_info': {
            'device_id': 'device-123456',
            'certificate': 'device-cert-data',
            'security_posture': {
                'os_version': 'Windows 10 21H1',
                'antivirus_status': 'active',
                'disk_encryption': 'enabled',
                'jailbroken': False
            }
        },
        'location_info': {
            'ip_address': '203.0.113.100',
            'geo_location': {'country': 'US', 'city': 'Seattle'},
            'network_reputation': {'malicious_activity': False}
        },
        'request_info': {
            'resource': 'arn:aws:s3:::production-data/*',
            'action': 'GetObject',
            'sensitivity_level': 'high'
        }
    }
    
    # Evaluate access request
    evaluation = zt_manager.evaluate_access_request(access_context)
    
    print(f"Access Decision: {evaluation['decision']}")
    print(f"Risk Score: {evaluation['risk_score']}")
    print(f"Required Actions: {evaluation['required_actions']}")
    
    # Create adaptive policy
    adaptive_policy_config = {
        'name': 'AdaptiveProductionAccess',
        'description': 'Adaptive access policy for production resources',
        'base_actions': [
            's3:GetObject',
            's3:ListBucket',
            'ec2:DescribeInstances'
        ],
        'resources': [
            'arn:aws:s3:::production-*/*',
            'arn:aws:ec2:*:*:instance/*'
        ],
        'require_mfa_for_sensitive': True,
        'ip_restrictions': ['203.0.113.0/24', '198.51.100.0/24'],
        'time_restrictions': {
            'start_time': '2024-01-01T08:00:00Z',
            'end_time': '2024-12-31T18:00:00Z'
        }
    }
    
    policy_arn = zt_manager.implement_adaptive_policies(adaptive_policy_config)
    print(f"Created adaptive policy: {policy_arn}")
```

## Troubleshooting

### Common Issues
- **Access Denied:** Check all policy layers (identity, boundary, SCP)
- **Role Assumption Failed:** Verify trust policy and external ID
- **MFA Required:** Ensure MFA device is associated and working
- **Policy Too Large:** AWS policies have size limits (2KB for users, 10KB for roles)

### Debugging Tools
- **Policy Simulator:** Test permissions before deployment
- **Access Advisor:** Identify unused permissions
- **CloudTrail:** Trace API calls and access patterns
- **Access Analyzer:** Find unintended external access

### Enterprise Security Best Practices
- **Implement Zero Trust Architecture:** Never trust, always verify with continuous authentication
- **Use Enterprise IAM Governance:** Automated compliance monitoring and policy optimization
- **Deploy Adaptive Security Policies:** Context-aware access controls based on risk assessment
- **Establish Continuous Monitoring:** Real-time threat detection and automated response
- **Create Security Automation:** Reduce manual overhead with intelligent security workflows
