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
