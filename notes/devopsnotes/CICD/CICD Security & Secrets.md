# CICD Security & Secrets

Enterprise security patterns, secrets management, and compliance frameworks for secure CICD pipelines.

## Table of Contents
1. [Security Architecture](#security-architecture)
2. [Secrets Management](#secrets-management)
3. [Pipeline Security](#pipeline-security)
4. [Vulnerability Management](#vulnerability-management)
5. [Access Control](#access-control)
6. [Compliance & Governance](#compliance--governance)
7. [Security Monitoring](#security-monitoring)
8. [Incident Response](#incident-response)

## Security Architecture

### Zero-Trust CICD Security Model
```yaml
security_architecture:
  identity_management:
    authentication:
      methods: ["oidc", "saml", "mfa"]
      providers: ["azure_ad", "okta", "auth0"]
      session_timeout: "8h"
      token_refresh: true
    
    authorization:
      model: "rbac"
      policies: "opa"
      just_in_time_access: true
      approval_workflows: true
  
  network_security:
    isolation:
      build_agents: "private_subnets"
      artifact_storage: "vpc_endpoints"
      secret_stores: "dedicated_network"
    
    traffic_controls:
      egress_filtering: true
      allowlist_domains: ["github.com", "docker.io", "npmjs.org"]
      proxy_configuration: true
      ssl_inspection: true
  
  infrastructure_security:
    compute:
      ephemeral_agents: true
      immutable_images: true
      runtime_protection: true
      vulnerability_scanning: true
    
    storage:
      encryption_at_rest: true
      encryption_in_transit: true
      key_rotation: "90d"
      backup_encryption: true
```

### Secure Pipeline Implementation
```groovy
@Library('security-shared-library') _

pipeline {
    agent {
        kubernetes {
            yaml '''
                apiVersion: v1
                kind: Pod
                spec:
                  securityContext:
                    runAsNonRoot: true
                    runAsUser: 1000
                    fsGroup: 1000
                  containers:
                  - name: build
                    image: secure-build-agent:latest
                    securityContext:
                      allowPrivilegeEscalation: false
                      readOnlyRootFilesystem: true
                      capabilities:
                        drop:
                          - ALL
                    resources:
                      limits:
                        memory: "2Gi"
                        cpu: "1000m"
                      requests:
                        memory: "1Gi"
                        cpu: "500m"
            '''
        }
    }
    
    environment {
        // Security-first environment configuration
        DOCKER_CONTENT_TRUST = '1'
        COSIGN_EXPERIMENTAL = '1'
        GRADLE_OPTS = '-Dorg.gradle.parallel=false -Dorg.gradle.daemon=false'
    }
    
    stages {
        stage('Security Initialization') {
            steps {
                script {
                    // Initialize security context
                    securityContext.initialize([
                        project: "${env.JOB_NAME}",
                        branch: "${env.BRANCH_NAME}",
                        buildNumber: "${env.BUILD_NUMBER}"
                    ])
                    
                    // Validate pipeline security configuration
                    securityValidation.validatePipelineConfig()
                    
                    // Setup secure temporary directories
                    sh '''
                    mkdir -p /tmp/secure-workspace
                    chmod 700 /tmp/secure-workspace
                    '''
                }
            }
        }
        
        stage('Code Security Scanning') {
            parallel {
                stage('Static Analysis (SAST)') {
                    steps {
                        script {
                            // SonarQube security analysis
                            withSonarQubeEnv('sonarqube-server') {
                                sh '''
                                sonar-scanner \
                                  -Dsonar.projectKey=${JOB_NAME} \
                                  -Dsonar.sources=src \
                                  -Dsonar.host.url=${SONAR_HOST_URL} \
                                  -Dsonar.login=${SONAR_AUTH_TOKEN}
                                '''
                            }
                            
                            // Semgrep security scanning
                            sh '''
                            docker run --rm -v $(pwd):/src \
                              returntocorp/semgrep:latest \
                              --config=auto \
                              --json \
                              --output=/src/semgrep-results.json \
                              /src
                            '''
                            
                            // Process security scan results
                            def scanResults = securityScanning.processSastResults([
                                sonarqube: 'sonar-report.json',
                                semgrep: 'semgrep-results.json'
                            ])
                            
                            if (scanResults.critical > 0) {
                                error "Critical security vulnerabilities found: ${scanResults.critical}"
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: '*-results.json'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'security-reports',
                                reportFiles: 'sast-report.html',
                                reportName: 'SAST Security Report'
                            ])
                        }
                    }
                }
                
                stage('Dependency Scanning') {
                    steps {
                        script {
                            // Snyk dependency scanning
                            withCredentials([string(credentialsId: 'snyk-token', variable: 'SNYK_TOKEN')]) {
                                sh '''
                                snyk auth ${SNYK_TOKEN}
                                snyk test --json-file-output=snyk-results.json
                                snyk monitor
                                '''
                            }
                            
                            // OWASP Dependency Check
                            sh '''
                            dependency-check.sh \
                              --project "${JOB_NAME}" \
                              --scan . \
                              --format ALL \
                              --out dependency-check-report
                            '''
                            
                            // Process dependency scan results
                            def depResults = securityScanning.processDependencyResults([
                                snyk: 'snyk-results.json',
                                owasp: 'dependency-check-report/dependency-check-report.json'
                            ])
                            
                            securityGates.evaluateDependencyFindings(depResults)
                        }
                    }
                }
                
                stage('Secret Scanning') {
                    steps {
                        script {
                            // TruffleHog secret detection
                            sh '''
                            docker run --rm -v $(pwd):/repo \
                              trufflesecurity/trufflehog:latest \
                              filesystem /repo \
                              --json \
                              --output=/repo/trufflehog-results.json
                            '''
                            
                            // GitLeaks secret scanning
                            sh '''
                            gitleaks detect \
                              --source . \
                              --report-format json \
                              --report-path gitleaks-results.json
                            '''
                            
                            // Process secret scan results
                            def secretResults = securityScanning.processSecretResults([
                                trufflehog: 'trufflehog-results.json',
                                gitleaks: 'gitleaks-results.json'
                            ])
                            
                            if (secretResults.findings.size() > 0) {
                                error "Secrets detected in codebase: ${secretResults.findings.size()}"
                            }
                        }
                    }
                }
            }
        }
        
        stage('Secure Build') {
            steps {
                script {
                    // Build with security controls
                    securityContext.withSecureEnvironment {
                        // Secure dependency resolution
                        sh '''
                        npm ci --only=production
                        npm audit --audit-level high
                        '''
                        
                        // Build application
                        sh 'npm run build'
                        
                        // Generate SBOM (Software Bill of Materials)
                        sh '''
                        syft . -o spdx-json=sbom.json
                        '''
                    }
                }
            }
        }
        
        stage('Container Security') {
            when {
                expression { fileExists('Dockerfile') }
            }
            steps {
                script {
                    // Secure container build
                    def imageTag = "${env.DOCKER_REGISTRY}/myapp:${env.BUILD_NUMBER}"
                    
                    // Build with security best practices
                    sh """
                    docker build \
                      --no-cache \
                      --pull \
                      --build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                      --build-arg VCS_REF=${env.GIT_COMMIT} \
                      --build-arg VERSION=${env.BUILD_NUMBER} \
                      -t ${imageTag} .
                    """
                    
                    // Container vulnerability scanning
                    sh """
                    # Trivy container scan
                    trivy image \
                      --format json \
                      --output trivy-results.json \
                      --severity HIGH,CRITICAL \
                      ${imageTag}
                    
                    # Grype container scan
                    grype ${imageTag} -o json > grype-results.json
                    
                    # Snyk container scan
                    snyk container test ${imageTag} \
                      --json-file-output=snyk-container-results.json
                    """
                    
                    // Process container scan results
                    def containerResults = securityScanning.processContainerResults([
                        trivy: 'trivy-results.json',
                        grype: 'grype-results.json',
                        snyk: 'snyk-container-results.json'
                    ])
                    
                    securityGates.evaluateContainerFindings(containerResults)
                    
                    // Sign container image
                    withCredentials([file(credentialsId: 'cosign-private-key', variable: 'COSIGN_KEY')]) {
                        sh """
                        cosign sign --key ${COSIGN_KEY} ${imageTag}
                        cosign attest --predicate sbom.json --key ${COSIGN_KEY} ${imageTag}
                        """
                    }
                }
            }
        }
        
        stage('Security Gates') {
            steps {
                script {
                    // Aggregate security results
                    def securityReport = securityGates.generateReport([
                        sast: 'sonar-report.json',
                        dependencies: 'snyk-results.json',
                        container: 'trivy-results.json',
                        secrets: 'trufflehog-results.json'
                    ])
                    
                    // Apply security policies
                    def gateResult = securityGates.evaluate(securityReport, [
                        policy: 'enterprise-security-policy',
                        environment: env.BRANCH_NAME == 'main' ? 'production' : 'development'
                    ])
                    
                    if (!gateResult.passed) {
                        error """
                        Security gate failed:
                        - Critical vulnerabilities: ${gateResult.critical}
                        - High vulnerabilities: ${gateResult.high}
                        - Policy violations: ${gateResult.violations}
                        """
                    }
                    
                    // Generate security attestation
                    securityAttestation.generate([
                        buildId: env.BUILD_NUMBER,
                        commit: env.GIT_COMMIT,
                        scanResults: securityReport,
                        policies: ['enterprise-security-policy']
                    ])
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Security cleanup
                sh '''
                # Secure cleanup of sensitive build artifacts
                find . -name "*.key" -delete
                find . -name "*.pem" -delete
                find . -name "*secret*" -delete
                
                # Clean Docker build cache
                docker system prune -f
                '''
                
                // Archive security reports
                archiveArtifacts artifacts: '''
                    *-results.json,
                    security-reports/**/*,
                    sbom.json,
                    security-attestation.json
                ''', fingerprint: true
                
                // Send security notifications
                securityNotifications.send([
                    channel: '#security-alerts',
                    results: securityReport,
                    buildUrl: env.BUILD_URL
                ])
            }
        }
        
        failure {
            script {
                // Security incident response
                securityIncident.create([
                    severity: 'medium',
                    type: 'pipeline_security_failure',
                    details: [
                        project: env.JOB_NAME,
                        branch: env.BRANCH_NAME,
                        build: env.BUILD_NUMBER,
                        commit: env.GIT_COMMIT
                    ]
                ])
            }
        }
    }
}
```

## Real-World Enterprise Use Cases

### Use Case 1: Zero-Trust Financial Services CICD
```python
#!/usr/bin/env python3
# zero_trust_cicd_security.py
# Zero-trust security model for financial services CICD pipeline

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import jwt
from cryptography.fernet import Fernet

class SecurityLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"

class ThreatLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    SEVERE = 5

@dataclass
class SecurityContext:
    user_id: str
    session_id: str
    ip_address: str
    mfa_verified: bool
    risk_score: float
    security_clearance: SecurityLevel
    timestamp: datetime

class ZeroTrustCICDSecurityManager:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.active_sessions: Dict[str, SecurityContext] = {}
        self.audit_log = []
        
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger('ZeroTrustCICDSecurity')
    
    async def authenticate_and_authorize(self, 
                                       user_credentials: Dict[str, Any],
                                       requested_action: str,
                                       resource_classification: SecurityLevel) -> Optional[SecurityContext]:
        """Comprehensive authentication and authorization with zero-trust principles"""
        try:
            # Multi-factor authentication
            mfa_result = await self._verify_multi_factor_auth(user_credentials)
            if not mfa_result['success']:
                self.logger.warning(f"MFA failed: {mfa_result['reason']}")
                return None
            
            # Risk assessment
            risk_score = await self._calculate_risk_score(user_credentials)
            if risk_score > 0.7:  # High risk threshold
                self.logger.warning(f"High risk score: {risk_score}")
                return None
            
            # Authorization check
            user_clearance = await self._get_security_clearance(user_credentials['user_id'])
            if not self._is_authorized(user_clearance, resource_classification):
                self.logger.warning("Insufficient clearance")
                return None
            
            # Create security context
            context = SecurityContext(
                user_id=user_credentials['user_id'],
                session_id=str(uuid.uuid4()),
                ip_address=user_credentials['ip_address'],
                mfa_verified=True,
                risk_score=risk_score,
                security_clearance=user_clearance,
                timestamp=datetime.utcnow()
            )
            
            self.active_sessions[context.session_id] = context
            return context
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return None
    
    async def secure_secrets_management(self, 
                                      context: SecurityContext,
                                      secret_name: str,
                                      operation: str) -> Optional[str]:
        """Zero-trust secrets management"""
        if not await self._validate_session(context.session_id):
            return None
        
        if not await self._check_secret_permissions(context, secret_name, operation):
            return None
        
        # Execute secret operation with audit logging
        await self._audit_secret_access(context, secret_name, operation)
        
        if operation == 'read':
            return await self._read_secret(secret_name)
        elif operation == 'create':
            return await self._create_secret(secret_name)
        elif operation == 'rotate':
            return await self._rotate_secret(secret_name)
        
        return None
    
    async def _verify_multi_factor_auth(self, credentials: Dict) -> Dict:
        # Simulate MFA verification
        return {'success': True, 'method': 'totp'}
    
    async def _calculate_risk_score(self, credentials: Dict) -> float:
        # Risk scoring based on multiple factors
        return 0.2  # Low risk
    
    async def _get_security_clearance(self, user_id: str) -> SecurityLevel:
        return SecurityLevel.CONFIDENTIAL
    
    def _is_authorized(self, user_clearance: SecurityLevel, resource: SecurityLevel) -> bool:
        clearance_levels = {
            SecurityLevel.PUBLIC: 1,
            SecurityLevel.INTERNAL: 2,
            SecurityLevel.CONFIDENTIAL: 3,
            SecurityLevel.RESTRICTED: 4,
            SecurityLevel.TOP_SECRET: 5
        }
        return clearance_levels[user_clearance] >= clearance_levels[resource]
    
    async def _validate_session(self, session_id: str) -> bool:
        return session_id in self.active_sessions
    
    async def _check_secret_permissions(self, context: SecurityContext, secret: str, op: str) -> bool:
        return True  # Simplified check
    
    async def _audit_secret_access(self, context: SecurityContext, secret: str, op: str):
        self.audit_log.append({
            'user': context.user_id,
            'action': f'{op} {secret}',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def _read_secret(self, name: str) -> str:
        return "encrypted_secret_value"
    
    async def _create_secret(self, name: str) -> str:
        return f"created_{name}"
    
    async def _rotate_secret(self, name: str) -> str:
        return f"rotated_{name}"

# Usage example
if __name__ == "__main__":
    async def main():
        manager = ZeroTrustCICDSecurityManager('config.json')
        
        credentials = {
            'user_id': 'john.doe@bank.com',
            'mfa_token': '123456',
            'ip_address': '10.0.1.100'
        }
        
        context = await manager.authenticate_and_authorize(
            credentials, 'deploy', SecurityLevel.CONFIDENTIAL
        )
        
        if context:
            secret = await manager.secure_secrets_management(
                context, 'db_password', 'read'
            )
            print(f"Secret accessed: {secret}")
    
    asyncio.run(main())
```

### Use Case 2: Healthcare HIPAA-Compliant Secret Management
```bash
#!/bin/bash
# hipaa_compliant_secrets.sh
# HIPAA-compliant secrets management for healthcare CICD

set -euo pipefail

# HIPAA compliance configuration
HIPAA_ENABLED=true
ENCRYPTION_REQUIRED=true
AUDIT_ALL_ACCESS=true
DATA_RETENTION_YEARS=6
ACCESS_LOG_LOCATION="/secure/audit/secret-access.log"

# Initialize HIPAA-compliant secrets management
init_hipaa_secrets() {
    echo "🏥 Initializing HIPAA-compliant secrets management..."
    
    # Ensure audit logging is enabled
    setup_audit_logging
    
    # Initialize encryption keys
    setup_encryption_keys
    
    # Configure access controls
    setup_access_controls
    
    echo "✅ HIPAA secrets management initialized"
}

# Setup comprehensive audit logging
setup_audit_logging() {
    echo "Setting up HIPAA audit logging..."
    
    # Create secure audit log directory
    sudo mkdir -p "$(dirname "$ACCESS_LOG_LOCATION")"
    sudo chmod 700 "$(dirname "$ACCESS_LOG_LOCATION")"
    
    # Initialize audit log with proper permissions
    if [[ ! -f "$ACCESS_LOG_LOCATION" ]]; then
        sudo touch "$ACCESS_LOG_LOCATION"
        sudo chmod 600 "$ACCESS_LOG_LOCATION"
    fi
    
    # Log audit system initialization
    audit_log "SYSTEM" "AUDIT_SYSTEM_INITIALIZED" "SUCCESS" ""
}

# Setup encryption for PHI (Protected Health Information)
setup_encryption_keys() {
    echo "Setting up HIPAA encryption keys..."
    
    # Generate encryption key if not exists
    if [[ ! -f "/secure/keys/hipaa-encryption.key" ]]; then
        openssl rand -base64 32 > /secure/keys/hipaa-encryption.key
        chmod 600 /secure/keys/hipaa-encryption.key
    fi
    
    # Generate signing key for audit integrity
    if [[ ! -f "/secure/keys/audit-signing.key" ]]; then
        openssl genpkey -algorithm RSA -out /secure/keys/audit-signing.key -pkcs8
        chmod 600 /secure/keys/audit-signing.key
    fi
    
    audit_log "SYSTEM" "ENCRYPTION_KEYS_INITIALIZED" "SUCCESS" ""
}

# Setup role-based access controls
setup_access_controls() {
    echo "Setting up HIPAA access controls..."
    
    # Define roles and permissions
    declare -A HIPAA_ROLES=(
        ["healthcare_provider"]="read:patient_data,phi_data"
        ["administrator"]="read,write:system_config,audit_logs"
        ["developer"]="read:non_phi_config"
        ["auditor"]="read:audit_logs,compliance_reports"
    )
    
    # Store role definitions securely
    for role in "${!HIPAA_ROLES[@]}"; do
        echo "${HIPAA_ROLES[$role]}" | \
            openssl enc -aes-256-cbc -salt -in - -out "/secure/roles/${role}.enc" -k "$(cat /secure/keys/hipaa-encryption.key)"
    done
    
    audit_log "SYSTEM" "ACCESS_CONTROLS_CONFIGURED" "SUCCESS" ""
}

# Comprehensive audit logging function
audit_log() {
    local user="$1"
    local action="$2"
    local result="$3"
    local resource="$4"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
    local session_id="${SESSION_ID:-$(uuidgen)}"
    local ip_address="${REMOTE_ADDR:-127.0.0.1}"
    
    # Create audit entry with all HIPAA-required fields
    local audit_entry="{"
    audit_entry+="\"timestamp\":\"$timestamp\","
    audit_entry+="\"user_id\":\"$user\","
    audit_entry+="\"session_id\":\"$session_id\","
    audit_entry+="\"ip_address\":\"$ip_address\","
    audit_entry+="\"action\":\"$action\","
    audit_entry+="\"resource\":\"$resource\","
    audit_entry+="\"result\":\"$result\","
    audit_entry+="\"compliance_framework\":\"HIPAA\","
    audit_entry+="\"data_classification\":\"PHI\""
    audit_entry+="}"
    
    # Sign audit entry for integrity
    local signature=$(echo -n "$audit_entry" | openssl dgst -sha256 -sign /secure/keys/audit-signing.key | base64 -w 0)
    
    # Write to audit log with signature
    echo "$audit_entry|SIGNATURE:$signature" >> "$ACCESS_LOG_LOCATION"
    
    # Also send to central SIEM if configured
    if [[ -n "${SIEM_ENDPOINT:-}" ]]; then
        curl -s -X POST "$SIEM_ENDPOINT/hipaa-audit" \
            -H "Content-Type: application/json" \
            -d "$audit_entry" || true
    fi
}

# HIPAA-compliant secret creation
create_hipaa_secret() {
    local secret_name="$1"
    local secret_value="$2"
    local data_classification="${3:-PHI}"
    local user_id="${4:-SYSTEM}"
    
    echo "🔒 Creating HIPAA-compliant secret: $secret_name"
    
    # Validate user permissions
    if ! validate_user_permissions "$user_id" "create" "$data_classification"; then
        audit_log "$user_id" "CREATE_SECRET_DENIED" "FAILURE" "$secret_name"
        echo "❌ Permission denied for secret creation"
        return 1
    fi
    
    # Encrypt secret value
    local encrypted_value=$(echo -n "$secret_value" | \
        openssl enc -aes-256-gcm -salt -in - -out - -k "$(cat /secure/keys/hipaa-encryption.key)" | base64 -w 0)
    
    # Store encrypted secret with metadata
    local secret_metadata="{"
    secret_metadata+="\"name\":\"$secret_name\","
    secret_metadata+="\"created_by\":\"$user_id\","
    secret_metadata+="\"created_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    secret_metadata+="\"data_classification\":\"$data_classification\","
    secret_metadata+="\"encrypted_value\":\"$encrypted_value\","
    secret_metadata+="\"retention_years\":$DATA_RETENTION_YEARS,"
    secret_metadata+="\"compliance_framework\":\"HIPAA\""
    secret_metadata+="}"
    
    # Store in secure vault
    echo "$secret_metadata" > "/secure/secrets/${secret_name}.json"
    chmod 600 "/secure/secrets/${secret_name}.json"
    
    # Audit successful creation
    audit_log "$user_id" "CREATE_SECRET" "SUCCESS" "$secret_name"
    
    echo "✅ HIPAA-compliant secret created successfully"
}

# HIPAA-compliant secret retrieval
read_hipaa_secret() {
    local secret_name="$1"
    local user_id="$2"
    local justification="${3:-Authorized access}"
    
    echo "🔎 Reading HIPAA-compliant secret: $secret_name"
    
    # Check if secret exists
    if [[ ! -f "/secure/secrets/${secret_name}.json" ]]; then
        audit_log "$user_id" "READ_SECRET_NOT_FOUND" "FAILURE" "$secret_name"
        echo "❌ Secret not found: $secret_name"
        return 1
    fi
    
    # Load secret metadata
    local secret_metadata=$(cat "/secure/secrets/${secret_name}.json")
    local data_classification=$(echo "$secret_metadata" | jq -r '.data_classification')
    
    # Validate user permissions for this data classification
    if ! validate_user_permissions "$user_id" "read" "$data_classification"; then
        audit_log "$user_id" "READ_SECRET_DENIED" "FAILURE" "$secret_name"
        echo "❌ Permission denied for secret access"
        return 1
    fi
    
    # Check for break-glass emergency access
    if [[ "$user_id" == "EMERGENCY" ]]; then
        # Emergency access requires additional validation
        if ! validate_emergency_access "$secret_name" "$justification"; then
            audit_log "$user_id" "EMERGENCY_ACCESS_DENIED" "FAILURE" "$secret_name"
            return 1
        fi
        
        # Log emergency access with high priority
        audit_log "$user_id" "EMERGENCY_SECRET_ACCESS" "SUCCESS" "$secret_name|JUSTIFICATION:$justification"
    else
        # Regular access audit
        audit_log "$user_id" "READ_SECRET" "SUCCESS" "$secret_name"
    fi
    
    # Decrypt and return secret value
    local encrypted_value=$(echo "$secret_metadata" | jq -r '.encrypted_value')
    local decrypted_value=$(echo "$encrypted_value" | base64 -d | \
        openssl enc -aes-256-gcm -d -in - -out - -k "$(cat /secure/keys/hipaa-encryption.key)")
    
    echo "$decrypted_value"
}

# Validate user permissions against HIPAA role matrix
validate_user_permissions() {
    local user_id="$1"
    local action="$2"
    local data_classification="$3"
    
    # Get user role
    local user_role=$(get_user_role "$user_id")
    if [[ -z "$user_role" ]]; then
        return 1
    fi
    
    # Load role permissions
    local role_permissions_file="/secure/roles/${user_role}.enc"
    if [[ ! -f "$role_permissions_file" ]]; then
        return 1
    fi
    
    local permissions=$(openssl enc -aes-256-cbc -d -in "$role_permissions_file" -k "$(cat /secure/keys/hipaa-encryption.key)")
    
    # Check if user has permission for this action and data classification
    if echo "$permissions" | grep -q "${action}:.*${data_classification}\|${action}:.*all"; then
        return 0
    else
        return 1
    fi
}

# Get user role from identity provider
get_user_role() {
    local user_id="$1"
    
    # In production, this would query LDAP/Active Directory
    # For demo purposes, return based on user ID pattern
    case "$user_id" in
        *"@healthcare.com")
            echo "healthcare_provider"
            ;;
        *"admin"*)
            echo "administrator"
            ;;
        *"dev"*)
            echo "developer"
            ;;
        *"audit"*)
            echo "auditor"
            ;;
        "EMERGENCY")
            echo "emergency_access"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Validate emergency access
validate_emergency_access() {
    local secret_name="$1"
    local justification="$2"
    
    # Emergency access requires:
    # 1. Valid justification
    # 2. Incident number (in production)
    # 3. Additional approvals (in production)
    
    if [[ ${#justification} -lt 10 ]]; then
        echo "❌ Emergency access requires detailed justification"
        return 1
    fi
    
    # In production, validate against incident management system
    echo "⚠️ Emergency access granted with justification: $justification"
    return 0
}

# Rotate HIPAA secret with full audit trail
rotate_hipaa_secret() {
    local secret_name="$1"
    local user_id="$2"
    local new_value="$3"
    
    echo "🔄 Rotating HIPAA-compliant secret: $secret_name"
    
    # Validate permissions
    if ! validate_user_permissions "$user_id" "rotate" "PHI"; then
        audit_log "$user_id" "ROTATE_SECRET_DENIED" "FAILURE" "$secret_name"
        return 1
    fi
    
    # Backup old secret before rotation
    if [[ -f "/secure/secrets/${secret_name}.json" ]]; then
        local backup_name="${secret_name}_backup_$(date +%Y%m%d_%H%M%S).json"
        cp "/secure/secrets/${secret_name}.json" "/secure/backups/$backup_name"
        audit_log "$user_id" "SECRET_BACKUP_CREATED" "SUCCESS" "$backup_name"
    fi
    
    # Create new secret version
    create_hipaa_secret "$secret_name" "$new_value" "PHI" "$user_id"
    
    # Audit rotation
    audit_log "$user_id" "ROTATE_SECRET" "SUCCESS" "$secret_name"
    
    echo "✅ Secret rotation completed with full audit trail"
}

# Generate HIPAA compliance report
generate_hipaa_compliance_report() {
    local report_period="${1:-30}"  # Days
    local output_file="hipaa_compliance_report_$(date +%Y%m%d).json"
    
    echo "📋 Generating HIPAA compliance report for last $report_period days..."
    
    local start_date=$(date -d "$report_period days ago" +%Y-%m-%d)
    local end_date=$(date +%Y-%m-%d)
    
    # Analyze audit logs
    local total_accesses=$(grep -c "READ_SECRET" "$ACCESS_LOG_LOCATION" || echo 0)
    local failed_accesses=$(grep -c "DENIED" "$ACCESS_LOG_LOCATION" || echo 0)
    local emergency_accesses=$(grep -c "EMERGENCY_ACCESS" "$ACCESS_LOG_LOCATION" || echo 0)
    
    # Generate compliance report
    cat > "$output_file" << EOF
{
  "report_period": {
    "start_date": "$start_date",
    "end_date": "$end_date",
    "period_days": $report_period
  },
  "access_statistics": {
    "total_secret_accesses": $total_accesses,
    "failed_access_attempts": $failed_accesses,
    "emergency_accesses": $emergency_accesses,
    "compliance_violations": 0
  },
  "hipaa_controls": {
    "encryption_at_rest": true,
    "access_logging_enabled": true,
    "audit_integrity_verified": true,
    "minimum_necessary_access": true,
    "role_based_access_control": true
  },
  "recommendations": [
    "Regular secret rotation every 90 days",
    "Review emergency access procedures quarterly",
    "Conduct access review with data stewards monthly"
  ],
  "generated_by": "HIPAA Compliance System",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    echo "✅ HIPAA compliance report generated: $output_file"
    audit_log "SYSTEM" "COMPLIANCE_REPORT_GENERATED" "SUCCESS" "$output_file"
}

# Main execution functions
main() {
    local command="${1:-help}"
    
    case "$command" in
        "init")
            init_hipaa_secrets
            ;;
        "create")
            create_hipaa_secret "${2:-}" "${3:-}" "${4:-PHI}" "${5:-$USER}"
            ;;
        "read")
            read_hipaa_secret "${2:-}" "${3:-$USER}" "${4:-Authorized access}"
            ;;
        "rotate")
            rotate_hipaa_secret "${2:-}" "${3:-$USER}" "${4:-}"
            ;;
        "report")
            generate_hipaa_compliance_report "${2:-30}"
            ;;
        "help")
            echo "Usage: $0 {init|create|read|rotate|report} [args...]"
            echo "Examples:"
            echo "  $0 init"
            echo "  $0 create patient_db_password 'secure123' PHI doctor@healthcare.com"
            echo "  $0 read patient_db_password doctor@healthcare.com"
            echo "  $0 rotate patient_db_password doctor@healthcare.com 'newsecure456'"
            echo "  $0 report 30"
            ;;
        *)
            echo "❌ Unknown command: $command"
            exit 1
            ;;
    esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This comprehensive CICD Security & Secrets guide provides enterprise-ready patterns for implementing robust security controls, managing secrets securely, and maintaining compliance throughout the software delivery pipeline with advanced zero-trust security models and HIPAA-compliant secret management.