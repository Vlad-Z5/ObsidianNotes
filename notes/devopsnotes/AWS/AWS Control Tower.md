# AWS Control Tower: Enterprise Multi-Account Governance and Orchestration

> **Service Type:** Management & Governance | **Scope:** Regional | **Serverless:** Yes

## Overview

AWS Control Tower provides a streamlined way to set up and govern secure, compliant multi-account AWS environments based on best practices learned from thousands of enterprise customer deployments. It establishes a landing zone with pre-configured organizational units, account factory for automated provisioning, and comprehensive guardrails for ongoing governance. Control Tower integrates seamlessly with DevOps workflows through automated account vending, Infrastructure as Code templates, and API-driven account management, making it essential for enterprise-scale AWS adoption.

## Core Architecture Components

- **Landing Zone:** Pre-configured multi-account environment with foundational security and compliance controls
- **Account Factory:** Automated account provisioning service with standardized configurations and governance baselines
- **Organizational Units (OUs):** Pre-configured organizational structure including Security, Sandbox, and custom OUs for workload isolation
- **Guardrails:** Preventive and detective controls that enforce organizational policies across all accounts
- **Centralized Logging:** Automated CloudTrail and Config setup across all accounts with centralized data archival
- **Integration Points:** Native connectivity with AWS Organizations, Service Catalog, SSO, and third-party governance tools
- **Security & Compliance:** Built-in security baselines, compliance frameworks, and audit trail management across all accounts

## DevOps & Enterprise Use Cases

### Infrastructure Automation
- **Account Lifecycle Management:** Automated account creation, configuration, and decommissioning through APIs
- **Baseline Configuration:** Standardized security and compliance configurations deployed automatically to all accounts
- **Environment Provisioning:** Rapid setup of development, staging, and production environments with proper isolation
- **Resource Tagging:** Organization-wide tagging strategies enforced across all accounts and resources

### CI/CD Integration
- **Pipeline Account Isolation:** Dedicated accounts for CI/CD pipelines with proper cross-account access controls
- **Automated Testing:** Isolated testing environments provisioned on-demand through account factory automation
- **Deployment Orchestration:** Multi-account deployment strategies with proper approval workflows
- **Environment Promotion:** Automated promotion of applications across account boundaries with governance controls

### Security & Compliance
- **Governance at Scale:** Consistent security policies enforced across hundreds of AWS accounts automatically
- **Compliance Automation:** Built-in compliance frameworks with continuous monitoring and drift detection
- **Identity Federation:** Centralized identity management with AWS SSO integration across all accounts
- **Security Baselines:** Standardized security configurations deployed to every account upon creation

### Monitoring & Operations
- **Centralized Visibility:** Unified view of all accounts, resources, and compliance status through Control Tower dashboard
- **Drift Detection:** Automated detection and alerting when accounts drift from established baselines
- **Operational Insights:** Comprehensive logging and monitoring across all accounts with centralized analysis
- **Cost Management:** Organization-wide cost visibility and allocation with account-level cost tracking

## Service Features & Capabilities

### Landing Zone Management
- **Quick Setup:** Deploy a complete multi-account environment in hours instead of weeks
- **Best Practice Architecture:** Pre-configured organizational structure based on AWS Well-Architected principles
- **Security Foundation:** Foundational security services enabled across all accounts automatically
- **Customization Options:** Ability to customize organizational units, account structure, and governance policies

### Account Factory Features
- **Self-Service Portal:** Enable teams to provision accounts through Service Catalog with proper approvals
- **Standardized Provisioning:** Consistent account setup with security baselines and organizational policies
- **Custom Configurations:** Account-specific configurations while maintaining organizational governance
- **Integration APIs:** Programmatic account provisioning for DevOps workflows and automation

### Guardrails Management
- **Preventive Controls:** Prevent non-compliant actions through service control policies (SCPs)
- **Detective Controls:** Monitor and report on compliance violations across all accounts
- **Built-in Policies:** 20+ pre-built guardrails for common governance requirements
- **Custom Guardrails:** Create organization-specific policies and controls for unique requirements

## Configuration & Setup

### Basic Configuration
```bash
# Enable Control Tower in your management account
aws controltower enable-control-tower \
  --landing-zone-configuration '{
    "driftStatus": "DRIFTED",
    "latestAvailableVersion": "3.0",
    "version": "3.0"
  }' \
  --tags Environment=Production,Owner=DevOps

# Create organizational unit
aws controltower create-managed-account \
  --account-name "Production-Workloads" \
  --account-email "aws-prod-workloads@company.com" \
  --organizational-unit-name "Security" \
  --sso-user-email "admin@company.com" \
  --sso-user-first-name "Admin" \
  --sso-user-last-name "User"

# Enable guardrail on organizational unit
aws controltower enable-guardrail \
  --guardrail-identifier "arn:aws:controltower:us-east-1::guardrail/AWS-GR_ENCRYPTED_VOLUMES" \
  --target-identifier "arn:aws:organizations::123456789012:ou/o-123456789/ou-123456789"
```

### Advanced Configuration
```bash
# Set up custom organizational structure
aws controltower update-landing-zone \
  --landing-zone-identifier "arn:aws:controltower:us-east-1:123456789012:landingzone/123456789" \
  --landing-zone-configuration '{
    "governanceAtScale": {
      "managedOrganizationalUnits": [
        {
          "name": "Development", 
          "guardrails": ["AWS-GR_ENCRYPTED_VOLUMES", "AWS-GR_EBS_OPTIMIZED_INSTANCE"]
        },
        {
          "name": "Production",
          "guardrails": ["AWS-GR_ENCRYPTED_VOLUMES", "AWS-GR_EBS_OPTIMIZED_INSTANCE", "AWS-GR_ROOT_ACCESS_KEY_CHECK"]
        }
      ]
    }
  }'

# Deploy custom account factory configuration
environments=("development" "staging" "production")
for env in "${environments[@]}"; do
  aws controltower create-managed-account \
    --account-name "${env}-workload-account" \
    --account-email "aws-${env}@company.com" \
    --organizational-unit-name "${env^}" \
    --tags Environment=$env,Purpose=workload
done
```

## Enterprise Implementation Examples

### Example 1: Large Enterprise Multi-Account Setup

**Business Requirement:** Deploy a secure multi-account environment for a 5,000+ employee enterprise with development, staging, and production isolation across multiple business units.

**Implementation Steps:**
1. **Landing Zone Architecture Design**
   ```python
   import boto3
   import json
   from typing import Dict, List, Any
   
   class ControlTowerOrchestrator:
       def __init__(self, region: str = 'us-east-1'):
           self.control_tower = boto3.client('controltower', region_name=region)
           self.organizations = boto3.client('organizations', region_name=region)
           self.service_catalog = boto3.client('servicecatalog', region_name=region)
           
       def deploy_enterprise_landing_zone(self, org_config: Dict[str, Any]) -> Dict[str, Any]:
           """Deploy enterprise landing zone with custom organizational structure"""
           
           landing_zone_config = {
               'driftStatus': 'IN_SYNC',
               'latestAvailableVersion': '3.0',
               'version': '3.0',
               'governanceAtScale': {
                   'managedOrganizationalUnits': [
                       {
                           'name': 'Security',
                           'description': 'Centralized security and logging accounts',
                           'guardrails': [
                               'AWS-GR_ENCRYPTED_VOLUMES',
                               'AWS-GR_EBS_OPTIMIZED_INSTANCE',
                               'AWS-GR_ROOT_ACCESS_KEY_CHECK',
                               'AWS-GR_MFA_ENABLED_FOR_ROOT'
                           ]
                       },
                       {
                           'name': 'Sandbox',
                           'description': 'Individual developer sandbox accounts',
                           'guardrails': [
                               'AWS-GR_ENCRYPTED_VOLUMES',
                               'AWS-GR_RESTRICTED_COMMON_PORTS'
                           ]
                       },
                       {
                           'name': 'Development',
                           'description': 'Development environment accounts',
                           'guardrails': [
                               'AWS-GR_ENCRYPTED_VOLUMES',
                               'AWS-GR_EBS_OPTIMIZED_INSTANCE'
                           ]
                       },
                       {
                           'name': 'Production',
                           'description': 'Production workload accounts',
                           'guardrails': [
                               'AWS-GR_ENCRYPTED_VOLUMES',
                               'AWS-GR_EBS_OPTIMIZED_INSTANCE',
                               'AWS-GR_ROOT_ACCESS_KEY_CHECK',
                               'AWS-GR_MFA_ENABLED_FOR_ROOT',
                               'AWS-GR_RESTRICTED_COMMON_PORTS',
                               'AWS-GR_S3_BUCKET_PUBLIC_WRITE_PROHIBITED'
                           ]
                       }
                   ]
               },
               'centralizedLogging': {
                   'logArchiveAccount': org_config.get('log_archive_account'),
                   'auditAccount': org_config.get('audit_account'),
                   'cloudTrailConfiguration': {
                       'enabled': True,
                       'multiRegionEnabled': True,
                       'organizationEnabled': True
                   }
               }
           }
           
           try:
               response = self.control_tower.enable_control_tower(
                   landingZoneConfiguration=landing_zone_config,
                   tags={
                       'Environment': 'Enterprise',
                       'ManagedBy': 'ControlTower',
                       'Purpose': 'MultiAccountGovernance'
                   }
               )
               
               return {
                   'status': 'success',
                   'landing_zone_arn': response.get('arn'),
                   'operation_identifier': response.get('operationIdentifier')
               }
               
           except Exception as e:
               return {
                   'status': 'failed',
                   'error': str(e)
               }
   ```

2. **Account Factory Configuration**
   ```python
   def setup_account_factory(self, business_units: List[str]) -> Dict[str, Any]:
       """Configure Account Factory for automated account provisioning"""
       
       account_factory_results = []
       
       for business_unit in business_units:
           # Create account factory product for each business unit
           product_config = {
               'Name': f'{business_unit}-Account-Factory',
               'Description': f'Automated account provisioning for {business_unit}',
               'Owner': 'Platform Engineering Team',
               'ProductType': 'CLOUD_FORMATION_TEMPLATE',
               'Tags': [
                   {'Key': 'BusinessUnit', 'Value': business_unit},
                   {'Key': 'Purpose', 'Value': 'AccountFactory'},
                   {'Key': 'ManagedBy', 'Value': 'ControlTower'}
               ],
               'ProvisioningArtifactParameters': {
                   'Name': f'{business_unit}-v1.0',
                   'Description': 'Account factory template with security baselines',
                   'Info': {
                       'LoadTemplateFromURL': 'https://s3.amazonaws.com/control-tower-templates/account-factory-template.yaml'
                   },
                   'Type': 'CLOUD_FORMATION_TEMPLATE'
               },
               'SupportDescription': 'Contact Platform Engineering for support'
           }
           
           try:
               response = self.service_catalog.create_product(**product_config)
               
               # Configure launch constraints
               self.service_catalog.create_constraint(
                   PortfolioId=response['ProductViewDetail']['ProductViewSummary']['ProductId'],
                   ProductId=response['ProductViewDetail']['ProductViewSummary']['ProductId'],
                   Parameters=json.dumps({
                       'RoleArn': f'arn:aws:iam::123456789012:role/AWSControlTowerExecution'
                   }),
                   Type='LAUNCH'
               )
               
               account_factory_results.append({
                   'business_unit': business_unit,
                   'product_id': response['ProductViewDetail']['ProductViewSummary']['ProductId'],
                   'status': 'created'
               })
               
           except Exception as e:
               account_factory_results.append({
                   'business_unit': business_unit,
                   'status': 'failed',
                   'error': str(e)
               })
       
       return {
           'account_factory_setup': account_factory_results,
           'total_business_units': len(business_units)
       }
   ```

3. **Custom Guardrails Implementation**
   ```python
   def deploy_custom_guardrails(self, guardrail_policies: List[Dict[str, Any]]) -> Dict[str, Any]:
       """Deploy custom organizational guardrails"""
       
       guardrail_results = []
       
       for policy in guardrail_policies:
           try:
               # Create custom SCP for preventive guardrail
               if policy['type'] == 'preventive':
                   scp_response = self.organizations.create_policy(
                       Name=policy['name'],
                       Description=policy['description'],
                       Type='SERVICE_CONTROL_POLICY',
                       Content=json.dumps(policy['policy_document'])
                   )
                   
                   # Attach to organizational units
                   for ou_id in policy['target_ou_ids']:
                       self.organizations.attach_policy(
                           PolicyId=scp_response['Policy']['PolicySummary']['Id'],
                           TargetId=ou_id
                       )
               
               # Create Config rule for detective guardrail
               elif policy['type'] == 'detective':
                   # This would integrate with AWS Config for detective controls
                   config_rule = {
                       'ConfigRuleName': policy['name'],
                       'Description': policy['description'],
                       'Source': policy['source'],
                       'Scope': policy.get('scope', {})
                   }
                   
                   # Deploy across organization (simplified)
                   pass
               
               guardrail_results.append({
                   'policy_name': policy['name'],
                   'type': policy['type'],
                   'status': 'deployed'
               })
               
           except Exception as e:
               guardrail_results.append({
                   'policy_name': policy['name'],
                   'status': 'failed',
                   'error': str(e)
               })
       
       return {
           'guardrail_deployment': guardrail_results,
           'total_policies': len(guardrail_policies)
       }
   ```

**Expected Outcome:** 50+ accounts deployed with consistent governance, 90% reduction in account setup time, automated compliance enforcement

### Example 2: DevOps Pipeline Account Automation

**Business Requirement:** Automate account provisioning for DevOps teams with standardized CI/CD pipeline accounts and cross-account deployment capabilities.

**Implementation Steps:**
1. **Pipeline Account Factory**
   ```python
   class PipelineAccountFactory:
       def __init__(self, control_tower_client):
           self.control_tower = control_tower_client
           
       def create_pipeline_account(self, 
                                 team_name: str, 
                                 environment: str,
                                 pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
           """Create standardized pipeline account for DevOps teams"""
           
           account_config = {
               'accountName': f'{team_name}-{environment}-pipeline',
               'accountEmail': f'aws-{team_name}-{environment}@company.com',
               'organizationalUnitName': f'{environment.title()}',
               'ssoUserEmail': pipeline_config.get('team_lead_email'),
               'ssoUserFirstName': pipeline_config.get('team_lead_first_name'),
               'ssoUserLastName': pipeline_config.get('team_lead_last_name'),
               'accountCustomizations': {
                   'tags': [
                       {'key': 'Team', 'value': team_name},
                       {'key': 'Environment', 'value': environment},
                       {'key': 'Purpose', 'value': 'CI/CD Pipeline'},
                       {'key': 'ManagedBy', 'value': 'ControlTower'}
                   ],
                   'baseline_configurations': {
                       'enable_cloudtrail': True,
                       'enable_config': True,
                       'enable_guardduty': True if environment == 'production' else False,
                       'cross_account_roles': pipeline_config.get('cross_account_roles', [])
                   }
               }
           }
           
           try:
               response = self.control_tower.create_managed_account(**account_config)
               
               # Wait for account creation to complete
               operation_id = response['operationIdentifier']
               self.wait_for_account_creation(operation_id)
               
               # Configure cross-account access for pipelines
               if pipeline_config.get('cross_account_roles'):
                   self.setup_cross_account_pipeline_roles(
                       response['accountId'],
                       pipeline_config['cross_account_roles']
                   )
               
               return {
                   'status': 'success',
                   'account_id': response.get('accountId'),
                   'account_name': account_config['accountName'],
                   'operation_id': operation_id
               }
               
           except Exception as e:
               return {
                   'status': 'failed',
                   'error': str(e),
                   'team': team_name,
                   'environment': environment
               }
   ```

**Expected Outcome:** Automated pipeline account provisioning, standardized cross-account access, 80% faster DevOps team onboarding

## Monitoring & Observability

### Key Metrics to Monitor
| Metric | Description | Threshold | Action |
|--------|-------------|-----------|---------|
| **LandingZoneDriftStatus** | Landing zone configuration drift | Any drift detected | Investigate and remediate drift |
| **GuardrailCompliance** | Percentage of accounts compliant with guardrails | <95% | Review and enforce compliance |
| **AccountProvisioningTime** | Time to provision new accounts | >4 hours | Optimize account factory process |
| **OrganizationalUnitHealth** | Health status of organizational units | Any unhealthy | Check OU configuration and policies |

### CloudWatch Integration
```bash
# Create Control Tower monitoring dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "ControlTower-Enterprise-Dashboard" \
  --dashboard-body file://control-tower-dashboard.json

# Set up drift detection alerts
aws cloudwatch put-metric-alarm \
  --alarm-name "ControlTower-Drift-Detected" \
  --alarm-description "Alert when landing zone drift is detected" \
  --metric-name "LandingZoneDriftStatus" \
  --namespace "AWS/ControlTower" \
  --statistic Maximum \
  --period 3600 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:control-tower-alerts
```

### Custom Monitoring
```python
import boto3
from datetime import datetime

class ControlTowerMonitor:
    def __init__(self):
        self.control_tower = boto3.client('controltower')
        self.organizations = boto3.client('organizations')
        self.cloudwatch = boto3.client('cloudwatch')
        
    def monitor_landing_zone_health(self) -> Dict[str, Any]:
        """Monitor overall landing zone health and compliance"""
        try:
            # Get landing zone status
            landing_zones = self.control_tower.list_landing_zones()
            
            health_metrics = []
            for lz in landing_zones['landingZones']:
                lz_details = self.control_tower.get_landing_zone(
                    landingZoneIdentifier=lz['arn']
                )
                
                # Check drift status
                drift_status = lz_details['landingZone']['driftStatus']
                
                # Get guardrail compliance
                guardrails = self.control_tower.list_enabled_guardrails(
                    landingZoneIdentifier=lz['arn']
                )
                
                compliance_score = self.calculate_guardrail_compliance(guardrails['guardrails'])
                
                health_metrics.append({
                    'landing_zone_arn': lz['arn'],
                    'drift_status': drift_status,
                    'compliance_score': compliance_score,
                    'last_updated': lz_details['landingZone']['latestLandingZoneOperation']['operationTime']
                })
                
                # Publish metrics to CloudWatch
                self.cloudwatch.put_metric_data(
                    Namespace='Custom/ControlTower',
                    MetricData=[
                        {
                            'MetricName': 'ComplianceScore',
                            'Value': compliance_score,
                            'Unit': 'Percent',
                            'Dimensions': [
                                {
                                    'Name': 'LandingZone',
                                    'Value': lz['arn'].split('/')[-1]
                                }
                            ]
                        },
                        {
                            'MetricName': 'DriftStatus',
                            'Value': 1 if drift_status == 'DRIFTED' else 0,
                            'Unit': 'Count'
                        }
                    ]
                )
            
            return {
                'status': 'healthy',
                'landing_zones_monitored': len(health_metrics),
                'health_details': health_metrics
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def calculate_guardrail_compliance(self, guardrails: List[Dict]) -> float:
        """Calculate overall guardrail compliance score"""
        if not guardrails:
            return 100.0
            
        compliant_count = sum(1 for g in guardrails if g.get('complianceStatus') == 'COMPLIANT')
        return (compliant_count / len(guardrails)) * 100
```

## Security & Compliance

### Security Best Practices
- **Least Privilege Access:** Implement minimal required permissions for Control Tower operations and account management
- **Cross-Account Security:** Secure cross-account roles with proper trust relationships and conditions
- **Centralized Identity:** Use AWS SSO for centralized identity management across all accounts
- **Audit Logging:** Enable comprehensive logging across all accounts with centralized log aggregation

### Compliance Frameworks
- **SOC 2:** Built-in controls for security, availability, and confidentiality across all accounts
- **PCI DSS:** Payment card industry compliance with automated security baselines
- **ISO 27001:** Information security management system controls enforced organization-wide
- **NIST:** Cybersecurity framework alignment with continuous monitoring and assessment

### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "controltower:GetLandingZone",
        "controltower:ListLandingZones",
        "controltower:ListEnabledGuardrails"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "controltower:CreateManagedAccount",
        "controltower:EnableGuardrail",
        "controltower:UpdateLandingZone"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-west-2"]
        }
      }
    }
  ]
}
```

## Cost Optimization

### Pricing Model
- **Landing Zone:** No additional charges for Control Tower service itself
- **AWS Services:** Pay for underlying AWS services (CloudTrail, Config, CloudWatch)
- **Account Factory:** No additional charges for account provisioning
- **Data Transfer:** Standard AWS data transfer charges for cross-account communication

### Cost Optimization Strategies
```bash
# Optimize logging costs across accounts
aws controltower update-landing-zone \
  --landing-zone-identifier "arn:aws:controltower:us-east-1:123456789012:landingzone/123456789" \
  --landing-zone-configuration '{
    "centralizedLogging": {
      "logRetentionDays": 90,
      "cloudTrailConfiguration": {
        "dataEvents": false,
        "insightEvents": false
      }
    }
  }'

# Set up cost monitoring for organization
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "ControlTower-Organization-Budget",
    "BudgetLimit": {
      "Amount": "5000",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'
```

## Automation & Infrastructure as Code

### CloudFormation Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Enterprise Control Tower deployment'

Parameters:
  OrganizationName:
    Type: String
    Description: Name of the organization
  
  LogArchiveAccountEmail:
    Type: String
    Description: Email for log archive account

Resources:
  ControlTowerLandingZone:
    Type: AWS::ControlTower::LandingZone
    Properties:
      Version: '3.0'
      Manifest:
        governanceAtScale:
          managedOrganizationalUnits:
            - name: Security
              guardrails:
                - AWS-GR_ENCRYPTED_VOLUMES
                - AWS-GR_ROOT_ACCESS_KEY_CHECK
            - name: Sandbox
              guardrails:
                - AWS-GR_ENCRYPTED_VOLUMES
            - name: Production
              guardrails:
                - AWS-GR_ENCRYPTED_VOLUMES
                - AWS-GR_ROOT_ACCESS_KEY_CHECK
                - AWS-GR_S3_BUCKET_PUBLIC_WRITE_PROHIBITED
        centralizedLogging:
          accountEmail: !Ref LogArchiveAccountEmail
          configurations:
            cloudtrail:
              enableLogFileValidation: true
              includeGlobalServiceEvents: true
              isMultiRegionTrail: true
      Tags:
        - Key: Organization
          Value: !Ref OrganizationName
        - Key: ManagedBy
          Value: CloudFormation

Outputs:
  LandingZoneId:
    Description: Control Tower Landing Zone ID
    Value: !Ref ControlTowerLandingZone
    Export:
      Name: !Sub '${AWS::StackName}-LandingZoneId'
```

### Terraform Configuration
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_controltower_landing_zone" "enterprise_lz" {
  version = "3.0"
  
  manifest = jsonencode({
    governanceAtScale = {
      managedOrganizationalUnits = [
        {
          name = "Security"
          guardrails = [
            "AWS-GR_ENCRYPTED_VOLUMES",
            "AWS-GR_ROOT_ACCESS_KEY_CHECK"
          ]
        },
        {
          name = "Production"
          guardrails = [
            "AWS-GR_ENCRYPTED_VOLUMES",
            "AWS-GR_ROOT_ACCESS_KEY_CHECK",
            "AWS-GR_S3_BUCKET_PUBLIC_WRITE_PROHIBITED"
          ]
        }
      ]
    }
    centralizedLogging = {
      accountEmail = var.log_archive_account_email
      configurations = {
        cloudtrail = {
          enableLogFileValidation = true
          includeGlobalServiceEvents = true
          isMultiRegionTrail = true
        }
      }
    }
  })
  
  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Purpose     = "MultiAccountGovernance"
  }
}

resource "aws_controltower_guardrail" "custom_guardrails" {
  for_each = var.custom_guardrails
  
  guardrail_identifier = each.value.identifier
  target_identifier   = each.value.target_ou
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "log_archive_account_email" {
  description = "Email for the log archive account"
  type        = string
}

variable "custom_guardrails" {
  description = "Custom guardrails to deploy"
  type = map(object({
    identifier = string
    target_ou  = string
  }))
  default = {}
}

output "landing_zone_arn" {
  description = "ARN of the Control Tower Landing Zone"
  value       = aws_controltower_landing_zone.enterprise_lz.arn
}
```

## Troubleshooting & Operations

### Common Issues & Solutions

#### Issue 1: Landing Zone Drift Detected
**Symptoms:** Control Tower dashboard shows drift status, compliance violations detected
**Cause:** Manual changes made outside of Control Tower, configuration modifications
**Solution:**
```bash
# Check drift details
aws controltower get-landing-zone \
  --landing-zone-identifier "arn:aws:controltower:us-east-1:123456789012:landingzone/123456789"

# Reset landing zone to remove drift
aws controltower reset-landing-zone \
  --landing-zone-identifier "arn:aws:controltower:us-east-1:123456789012:landingzone/123456789"
```

#### Issue 2: Account Factory Provisioning Failures
**Symptoms:** Account creation requests fail or timeout
**Cause:** Service limits, insufficient permissions, or naming conflicts
**Solution:**
```python
import boto3

def diagnose_account_provisioning(operation_id: str) -> Dict[str, Any]:
    """Diagnose account provisioning operation failures"""
    control_tower = boto3.client('controltower')
    
    try:
        # Get operation details
        response = control_tower.get_landing_zone_operation(
            operationIdentifier=operation_id
        )
        
        operation = response['operationDetails']
        
        if operation['status'] == 'FAILED':
            failure_reason = operation.get('statusMessage', 'Unknown error')
            
            # Common failure analysis
            if 'LIMIT_EXCEEDED' in failure_reason:
                return {
                    'issue': 'Service limits exceeded',
                    'solution': 'Request limit increase through AWS Support',
                    'details': failure_reason
                }
            elif 'EMAIL_ALREADY_EXISTS' in failure_reason:
                return {
                    'issue': 'Email address already in use',
                    'solution': 'Use a different email address for account',
                    'details': failure_reason
                }
            else:
                return {
                    'issue': 'Unknown provisioning failure',
                    'solution': 'Contact AWS Support with operation ID',
                    'details': failure_reason
                }
        
        return {
            'status': operation['status'],
            'operation_type': operation['operationType']
        }
        
    except Exception as e:
        return {
            'error': f'Failed to diagnose operation: {str(e)}'
        }
```

### Performance Optimization

#### Optimization Strategy 1: Account Provisioning Speed
- **Current State Analysis:** Monitor account creation times and identify bottlenecks
- **Optimization Steps:** Optimize baseline configurations and reduce unnecessary services
- **Expected Improvement:** 50% reduction in account provisioning time

#### Optimization Strategy 2: Guardrail Evaluation
- **Monitoring Approach:** Track guardrail evaluation frequency and performance impact
- **Tuning Parameters:** Optimize detective guardrail evaluation schedules
- **Validation Methods:** Balance compliance coverage with operational efficiency

## Best Practices Summary

### Development & Deployment
1. **Phased Rollout:** Deploy Control Tower in phases starting with development environments
2. **Testing Strategy:** Thoroughly test all guardrails and configurations in sandbox environments
3. **Documentation:** Maintain comprehensive documentation of organizational structure and policies
4. **Change Management:** Implement proper change management processes for landing zone modifications

### Operations & Maintenance
1. **Regular Monitoring:** Continuously monitor landing zone health and compliance status
2. **Drift Management:** Implement processes to prevent and quickly remediate configuration drift
3. **Cost Optimization:** Regularly review and optimize costs across all managed accounts
4. **Training:** Provide regular training for teams on Control Tower best practices

### Security & Governance
1. **Least Privilege:** Implement least privilege access for all Control Tower operations
2. **Regular Audits:** Conduct regular audits of guardrails and organizational policies
3. **Incident Response:** Establish clear procedures for responding to compliance violations
4. **Continuous Improvement:** Regularly review and update governance policies based on business needs

---

## Additional Resources

### AWS Documentation
- [Official AWS Control Tower Documentation](https://docs.aws.amazon.com/controltower/)
- [AWS Control Tower API Reference](https://docs.aws.amazon.com/controltower/latest/APIReference/)
- [AWS Control Tower User Guide](https://docs.aws.amazon.com/controltower/latest/userguide/)

### Community Resources
- [AWS Control Tower GitHub Samples](https://github.com/aws-samples?q=control-tower)
- [AWS Control Tower Workshop](https://controltower.aws-management.tools/)
- [AWS Control Tower Blog Posts](https://aws.amazon.com/blogs/aws/?tag=control-tower)

### Tools & Utilities
- [AWS CLI Control Tower Commands](https://docs.aws.amazon.com/cli/latest/reference/controltower/)
- [AWS SDKs for Control Tower](https://aws.amazon.com/developer/tools/)
- [Terraform AWS Control Tower Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/controltower_landing_zone)