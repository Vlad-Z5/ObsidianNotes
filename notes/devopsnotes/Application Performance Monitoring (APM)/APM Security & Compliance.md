# APM Security & Compliance

APM Security & Compliance ensures that application performance monitoring systems meet security standards, protect sensitive data, maintain audit trails, and comply with regulatory requirements while providing comprehensive monitoring capabilities.

## Security Framework for APM

### 1. Data Security and Privacy Protection
```python
import hashlib
import hmac
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from enum import Enum
import logging
import json

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class PIIType(Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    USER_ID = "user_id"
    NAME = "name"

@dataclass
class SecurityConfig:
    encryption_enabled: bool = True
    data_retention_days: int = 90
    anonymization_enabled: bool = True
    audit_logging: bool = True
    allowed_data_classifications: Set[DataClassification] = field(default_factory=lambda: {DataClassification.PUBLIC, DataClassification.INTERNAL})
    pii_detection_enabled: bool = True
    secure_transmission: bool = True

class DataSanitizer:
    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
        self.pii_patterns = {
            PIIType.EMAIL: re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            PIIType.PHONE: re.compile(r'\b\d{3}-?\d{3}-?\d{4}\b'),
            PIIType.SSN: re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            PIIType.CREDIT_CARD: re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
            PIIType.IP_ADDRESS: re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        }
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key from environment or create new one"""
        # In production, this should come from secure key management
        password = secrets.token_bytes(32)
        salt = secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def detect_pii(self, text: str) -> Dict[PIIType, List[str]]:
        """Detect PII in text content"""
        detected_pii = {}
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_pii[pii_type] = matches
        
        return detected_pii
    
    def sanitize_data(self, data: Any, classification: DataClassification = DataClassification.INTERNAL) -> Any:
        """Sanitize data based on security configuration"""
        if not self.config.anonymization_enabled:
            return data
        
        if classification not in self.config.allowed_data_classifications:
            return "[REDACTED - UNAUTHORIZED ACCESS]"
        
        if isinstance(data, dict):
            return {key: self.sanitize_data(value, classification) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item, classification) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string content"""
        sanitized = text
        
        # Replace PII with hashed versions
        for pii_type, pattern in self.pii_patterns.items():
            def replace_with_hash(match):
                original = match.group(0)
                hashed = hashlib.sha256(original.encode()).hexdigest()[:8]
                return f"[{pii_type.value.upper()}:{hashed}]"
            
            sanitized = pattern.sub(replace_with_hash, sanitized)
        
        return sanitized
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not self.config.encryption_enabled:
            return data
        
        encrypted = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not self.config.encryption_enabled:
            return encrypted_data
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logging.error(f"Failed to decrypt data: {e}")
            return "[DECRYPTION_FAILED]"

class SecureAPMCollector:
    def __init__(self, security_config: SecurityConfig):
        self.security_config = security_config
        self.sanitizer = DataSanitizer(security_config)
        self.audit_logger = self._setup_audit_logging()
        self.access_control = AccessControlManager()
    
    def _setup_audit_logging(self):
        """Setup audit logging"""
        audit_logger = logging.getLogger('apm.security.audit')
        handler = logging.FileHandler('apm_security_audit.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        audit_logger.setLevel(logging.INFO)
        return audit_logger
    
    def collect_metric(self, metric_data: Dict, user_context: Dict = None) -> Dict:
        """Collect metric with security controls"""
        # Access control check
        if user_context and not self.access_control.can_collect_metric(user_context, metric_data):
            self.audit_logger.warning(f"Unauthorized metric collection attempt: {user_context}")
            return {"error": "Access denied"}
        
        # Classify data
        classification = self._classify_data(metric_data)
        
        # Sanitize sensitive data
        sanitized_data = self.sanitizer.sanitize_data(metric_data, classification)
        
        # Encrypt if required
        if classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]:
            sanitized_data = self._encrypt_metric_data(sanitized_data)
        
        # Audit log
        if self.security_config.audit_logging:
            self.audit_logger.info(f"Metric collected: {metric_data.get('metric_name', 'unknown')} - Classification: {classification.value}")
        
        return {
            **sanitized_data,
            'security_metadata': {
                'classification': classification.value,
                'encrypted': classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED],
                'sanitized': self.security_config.anonymization_enabled,
                'timestamp': time.time()
            }
        }
    
    def _classify_data(self, data: Dict) -> DataClassification:
        """Classify data based on content"""
        # Simple classification logic - can be enhanced with ML
        data_str = json.dumps(data, default=str).lower()
        
        restricted_keywords = ['password', 'secret', 'key', 'token', 'ssn', 'credit_card']
        confidential_keywords = ['email', 'phone', 'user_id', 'personal']
        
        if any(keyword in data_str for keyword in restricted_keywords):
            return DataClassification.RESTRICTED
        elif any(keyword in data_str for keyword in confidential_keywords):
            return DataClassification.CONFIDENTIAL
        elif 'internal' in data_str:
            return DataClassification.INTERNAL
        else:
            return DataClassification.PUBLIC
    
    def _encrypt_metric_data(self, data: Dict) -> Dict:
        """Encrypt sensitive portions of metric data"""
        encrypted_data = data.copy()
        
        sensitive_fields = ['user_data', 'request_body', 'response_body', 'error_details']
        
        for field in sensitive_fields:
            if field in encrypted_data:
                encrypted_data[field] = self.sanitizer.encrypt_sensitive_data(
                    json.dumps(encrypted_data[field], default=str)
                )
        
        return encrypted_data
```

### 2. Access Control and Authentication
```python
import jwt
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
from enum import Enum

class Role(Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"
    SYSTEM = "system"

class Permission(Enum):
    READ_METRICS = "read_metrics"
    WRITE_METRICS = "write_metrics"
    VIEW_TRACES = "view_traces"
    MANAGE_ALERTS = "manage_alerts"
    ADMIN_CONFIG = "admin_config"
    EXPORT_DATA = "export_data"

class AccessControlManager:
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.role_permissions = {
            Role.VIEWER: {Permission.READ_METRICS, Permission.VIEW_TRACES},
            Role.ANALYST: {Permission.READ_METRICS, Permission.VIEW_TRACES, Permission.MANAGE_ALERTS, Permission.EXPORT_DATA},
            Role.ADMIN: {Permission.READ_METRICS, Permission.WRITE_METRICS, Permission.VIEW_TRACES, 
                        Permission.MANAGE_ALERTS, Permission.ADMIN_CONFIG, Permission.EXPORT_DATA},
            Role.SYSTEM: {Permission.READ_METRICS, Permission.WRITE_METRICS, Permission.VIEW_TRACES}
        }
        self.user_sessions: Dict[str, Dict] = {}
    
    def create_jwt_token(self, user_id: str, role: Role, expires_in_hours: int = 24) -> str:
        """Create JWT token for user authentication"""
        payload = {
            'user_id': user_id,
            'role': role.value,
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'iat': datetime.utcnow(),
            'permissions': [p.value for p in self.role_permissions.get(role, set())]
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Store session info
        self.user_sessions[user_id] = {
            'token': token,
            'role': role,
            'last_activity': datetime.utcnow(),
            'permissions': self.role_permissions.get(role, set())
        }
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return user info"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
            
            # Update last activity
            if user_id in self.user_sessions:
                self.user_sessions[user_id]['last_activity'] = datetime.utcnow()
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def has_permission(self, user_context: Dict, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_role = Role(user_context.get('role', 'viewer'))
        user_permissions = self.role_permissions.get(user_role, set())
        return permission in user_permissions
    
    def can_collect_metric(self, user_context: Dict, metric_data: Dict) -> bool:
        """Check if user can collect specific metric"""
        if not self.has_permission(user_context, Permission.WRITE_METRICS):
            return False
        
        # Additional metric-specific access control
        metric_name = metric_data.get('metric_name', '')
        
        # System metrics require system role
        if metric_name.startswith('system.') and user_context.get('role') != Role.SYSTEM.value:
            return False
        
        return True
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user context (implementation depends on framework)
                user_context = kwargs.get('user_context') or self._get_current_user_context()
                
                if not user_context or not self.has_permission(user_context, permission):
                    raise PermissionError(f"Permission {permission.value} required")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _get_current_user_context(self) -> Optional[Dict]:
        """Get current user context (implementation depends on framework)"""
        # This would be implemented based on your web framework
        # For Flask: return session.get('user_context')
        # For FastAPI: return request.state.user_context
        pass

class SecureAPMEndpoints:
    def __init__(self, access_control: AccessControlManager):
        self.access_control = access_control
    
    @access_control.require_permission(Permission.READ_METRICS)
    def get_metrics(self, user_context: Dict = None) -> Dict:
        """Get metrics with access control"""
        # Implementation with security controls
        return {"metrics": "data"}
    
    @access_control.require_permission(Permission.EXPORT_DATA)
    def export_data(self, export_request: Dict, user_context: Dict = None) -> Dict:
        """Export data with audit logging"""
        # Log data export request
        logging.info(f"Data export requested by user {user_context.get('user_id')}")
        
        # Implementation with data sanitization
        return {"export_url": "secure_url"}
```

### 3. Compliance Framework
```python
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

class ComplianceStandard(Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"

@dataclass
class ComplianceRequirement:
    standard: ComplianceStandard
    requirement_id: str
    description: str
    implementation_status: str = "pending"  # pending, implemented, validated
    evidence: List[str] = field(default_factory=list)
    last_audit: Optional[datetime] = None

class ComplianceManager:
    def __init__(self):
        self.requirements: Dict[str, ComplianceRequirement] = {}
        self.compliance_reports: List[Dict] = []
        self.data_retention_policies: Dict[ComplianceStandard, int] = {
            ComplianceStandard.GDPR: 730,  # 2 years max
            ComplianceStandard.HIPAA: 2555,  # 7 years
            ComplianceStandard.SOX: 2555,   # 7 years
            ComplianceStandard.PCI_DSS: 365,  # 1 year min
            ComplianceStandard.SOC2: 365    # 1 year
        }
        self._initialize_requirements()
    
    def _initialize_requirements(self):
        """Initialize compliance requirements"""
        # GDPR Requirements
        gdpr_requirements = [
            ComplianceRequirement(
                ComplianceStandard.GDPR,
                "GDPR-7.1",
                "Data must be processed lawfully, fairly and in a transparent manner",
                evidence=["consent_management_system", "privacy_policy"]
            ),
            ComplianceRequirement(
                ComplianceStandard.GDPR,
                "GDPR-7.3", 
                "Data must be adequate, relevant and limited to what is necessary",
                evidence=["data_minimization_policy", "data_classification"]
            ),
            ComplianceRequirement(
                ComplianceStandard.GDPR,
                "GDPR-17",
                "Right to erasure - data subjects can request deletion",
                evidence=["data_deletion_procedures", "automated_deletion_system"]
            )
        ]
        
        # HIPAA Requirements
        hipaa_requirements = [
            ComplianceRequirement(
                ComplianceStandard.HIPAA,
                "HIPAA-164.308(a)(1)",
                "Implement policies and procedures to prevent unauthorized access",
                evidence=["access_control_system", "audit_logs"]
            ),
            ComplianceRequirement(
                ComplianceStandard.HIPAA,
                "HIPAA-164.312(a)(1)",
                "Implement technical safeguards for PHI",
                evidence=["encryption_implementation", "access_logs"]
            )
        ]
        
        # Add all requirements
        for req in gdpr_requirements + hipaa_requirements:
            self.requirements[f"{req.standard.value}_{req.requirement_id}"] = req
    
    def assess_compliance(self, standard: ComplianceStandard) -> Dict:
        """Assess compliance with specific standard"""
        relevant_requirements = [
            req for req in self.requirements.values() 
            if req.standard == standard
        ]
        
        total_requirements = len(relevant_requirements)
        implemented = sum(1 for req in relevant_requirements if req.implementation_status == "implemented")
        validated = sum(1 for req in relevant_requirements if req.implementation_status == "validated")
        
        compliance_score = (implemented + validated * 1.5) / (total_requirements * 1.5) * 100
        
        assessment = {
            'standard': standard.value,
            'compliance_score': compliance_score,
            'total_requirements': total_requirements,
            'implemented': implemented,
            'validated': validated,
            'pending': total_requirements - implemented - validated,
            'requirements_status': [
                {
                    'id': req.requirement_id,
                    'description': req.description,
                    'status': req.implementation_status,
                    'evidence_count': len(req.evidence),
                    'last_audit': req.last_audit.isoformat() if req.last_audit else None
                }
                for req in relevant_requirements
            ],
            'assessment_date': datetime.utcnow().isoformat()
        }
        
        self.compliance_reports.append(assessment)
        return assessment
    
    def implement_gdpr_controls(self, apm_system) -> Dict:
        """Implement GDPR-specific controls"""
        implementations = []
        
        # Data Subject Access Request (DSAR)
        def handle_data_access_request(user_id: str) -> Dict:
            user_data = apm_system.get_user_data(user_id)
            return {
                'user_id': user_id,
                'data_collected': user_data,
                'collection_date': datetime.utcnow().isoformat(),
                'retention_period': f"{self.data_retention_policies[ComplianceStandard.GDPR]} days"
            }
        
        # Data Deletion (Right to be Forgotten)
        def handle_data_deletion_request(user_id: str) -> Dict:
            deleted_records = apm_system.delete_user_data(user_id)
            
            # Log deletion for audit trail
            audit_entry = {
                'action': 'data_deletion',
                'user_id': user_id,
                'deleted_records': deleted_records,
                'deletion_date': datetime.utcnow().isoformat(),
                'compliance_basis': 'GDPR Article 17'
            }
            
            return audit_entry
        
        # Data Portability
        def export_user_data(user_id: str, format: str = 'json') -> str:
            user_data = apm_system.get_user_data(user_id)
            
            if format == 'json':
                return json.dumps(user_data, indent=2, default=str)
            elif format == 'csv':
                # Convert to CSV format
                return self._convert_to_csv(user_data)
            
            return str(user_data)
        
        implementations.extend([
            {'control': 'data_access_request', 'function': handle_data_access_request},
            {'control': 'data_deletion_request', 'function': handle_data_deletion_request},
            {'control': 'data_export', 'function': export_user_data}
        ])
        
        return {'implementations': implementations}
    
    def implement_data_retention_policies(self) -> Dict:
        """Implement automated data retention policies"""
        retention_jobs = []
        
        for standard, retention_days in self.data_retention_policies.items():
            def create_retention_job(std, days):
                def retention_job():
                    cutoff_date = datetime.utcnow() - timedelta(days=days)
                    
                    # This would integrate with your APM data store
                    deleted_count = self._cleanup_old_data(cutoff_date, std)
                    
                    logging.info(f"Data retention cleanup for {std.value}: {deleted_count} records deleted")
                    
                    return {
                        'standard': std.value,
                        'retention_days': days,
                        'cutoff_date': cutoff_date.isoformat(),
                        'deleted_records': deleted_count
                    }
                
                return retention_job
            
            retention_jobs.append({
                'standard': standard.value,
                'job_function': create_retention_job(standard, retention_days)
            })
        
        return {'retention_jobs': retention_jobs}
    
    def _cleanup_old_data(self, cutoff_date: datetime, standard: ComplianceStandard) -> int:
        """Cleanup old data based on retention policy"""
        # Implementation would depend on your data store
        # This is a placeholder for the actual cleanup logic
        return 0
    
    def _convert_to_csv(self, data: Dict) -> str:
        """Convert data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        
        if isinstance(data, list) and data:
            fieldnames = data[0].keys() if isinstance(data[0], dict) else ['value']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                if isinstance(row, dict):
                    writer.writerow(row)
                else:
                    writer.writerow({'value': row})
        
        return output.getvalue()
    
    def generate_compliance_report(self, standards: List[ComplianceStandard] = None) -> Dict:
        """Generate comprehensive compliance report"""
        if not standards:
            standards = list(ComplianceStandard)
        
        report = {
            'report_date': datetime.utcnow().isoformat(),
            'standards_assessed': [std.value for std in standards],
            'assessments': []
        }
        
        for standard in standards:
            assessment = self.assess_compliance(standard)
            report['assessments'].append(assessment)
        
        # Overall compliance score
        if report['assessments']:
            overall_score = sum(a['compliance_score'] for a in report['assessments']) / len(report['assessments'])
            report['overall_compliance_score'] = overall_score
        
        return report
```

### 4. Audit Trail and Monitoring
```python
class SecurityAuditLogger:
    def __init__(self, storage_backend: str = "file"):
        self.storage_backend = storage_backend
        self.audit_logger = self._setup_audit_logger()
        self.security_events: List[Dict] = []
        
    def _setup_audit_logger(self):
        """Setup structured audit logging"""
        logger = logging.getLogger('apm.security.audit')
        logger.setLevel(logging.INFO)
        
        # JSON formatter for structured logs
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                
                # Add extra fields if present
                if hasattr(record, 'user_id'):
                    log_entry['user_id'] = record.user_id
                if hasattr(record, 'action'):
                    log_entry['action'] = record.action
                if hasattr(record, 'resource'):
                    log_entry['resource'] = record.resource
                
                return json.dumps(log_entry)
        
        handler = logging.FileHandler('apm_security_audit.jsonl')
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        return logger
    
    def log_access_event(self, user_id: str, action: str, resource: str, 
                        success: bool, additional_info: Dict = None):
        """Log access events"""
        event = {
            'event_type': 'access',
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': self._get_client_ip(),
            'user_agent': self._get_user_agent(),
            'additional_info': additional_info or {}
        }
        
        self.audit_logger.info(
            f"Access event: {action} on {resource}",
            extra={
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'success': success
            }
        )
        
        self.security_events.append(event)
    
    def log_data_event(self, user_id: str, data_type: str, operation: str, 
                      classification: DataClassification, record_count: int = 1):
        """Log data handling events"""
        event = {
            'event_type': 'data_handling',
            'user_id': user_id,
            'data_type': data_type,
            'operation': operation,  # create, read, update, delete, export
            'classification': classification.value,
            'record_count': record_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.audit_logger.info(
            f"Data event: {operation} {record_count} {data_type} records",
            extra={
                'user_id': user_id,
                'action': f"data_{operation}",
                'resource': data_type
            }
        )
        
        self.security_events.append(event)
    
    def log_security_event(self, event_type: str, severity: str, description: str,
                          user_id: str = None, additional_data: Dict = None):
        """Log security events"""
        event = {
            'event_type': 'security_incident',
            'security_event_type': event_type,
            'severity': severity,
            'description': description,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'additional_data': additional_data or {}
        }
        
        self.audit_logger.warning(
            f"Security event: {event_type} - {description}",
            extra={
                'user_id': user_id or 'system',
                'action': event_type,
                'resource': 'security'
            }
        )
        
        self.security_events.append(event)
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Implementation depends on web framework
        return "0.0.0.0"  # Placeholder
    
    def _get_user_agent(self) -> str:
        """Get client user agent"""
        # Implementation depends on web framework
        return "unknown"  # Placeholder
    
    def detect_anomalous_behavior(self) -> List[Dict]:
        """Detect anomalous security behavior"""
        anomalies = []
        
        # Group events by user and analyze patterns
        user_events = {}
        for event in self.security_events[-1000:]:  # Last 1000 events
            user_id = event.get('user_id')
            if user_id:
                if user_id not in user_events:
                    user_events[user_id] = []
                user_events[user_id].append(event)
        
        for user_id, events in user_events.items():
            # Check for suspicious patterns
            
            # Multiple failed access attempts
            recent_failures = [
                e for e in events[-50:] 
                if e.get('event_type') == 'access' and not e.get('success')
            ]
            
            if len(recent_failures) >= 5:
                anomalies.append({
                    'type': 'repeated_access_failures',
                    'user_id': user_id,
                    'count': len(recent_failures),
                    'severity': 'high',
                    'description': f"User {user_id} had {len(recent_failures)} failed access attempts"
                })
            
            # Unusual data export activity
            exports = [
                e for e in events[-100:]
                if e.get('event_type') == 'data_handling' and e.get('operation') == 'export'
            ]
            
            if len(exports) >= 3:
                total_records = sum(e.get('record_count', 0) for e in exports)
                anomalies.append({
                    'type': 'unusual_data_export',
                    'user_id': user_id,
                    'export_count': len(exports),
                    'total_records': total_records,
                    'severity': 'medium',
                    'description': f"User {user_id} performed {len(exports)} data exports"
                })
        
        return anomalies
```

### 5. Secure Configuration Management
```python
import os
from pathlib import Path
import yaml

class SecureConfigurationManager:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "apm_security_config.yaml"
        self.config = self._load_security_config()
        self.validate_configuration()
    
    def _load_security_config(self) -> Dict:
        """Load security configuration"""
        default_config = {
            'security': {
                'encryption': {
                    'enabled': True,
                    'algorithm': 'AES-256-GCM',
                    'key_rotation_days': 90
                },
                'authentication': {
                    'jwt_expiry_hours': 24,
                    'password_policy': {
                        'min_length': 12,
                        'require_uppercase': True,
                        'require_lowercase': True,
                        'require_numbers': True,
                        'require_symbols': True
                    }
                },
                'data_classification': {
                    'default_classification': 'internal',
                    'auto_classification': True
                },
                'audit_logging': {
                    'enabled': True,
                    'log_level': 'INFO',
                    'retention_days': 2555  # 7 years
                },
                'compliance': {
                    'standards': ['gdpr', 'soc2'],
                    'data_retention_days': 730,
                    'anonymization_enabled': True
                }
            },
            'monitoring': {
                'security_metrics': {
                    'enabled': True,
                    'alert_thresholds': {
                        'failed_logins_per_hour': 10,
                        'data_export_size_mb': 1000,
                        'concurrent_sessions_per_user': 3
                    }
                }
            }
        }
        
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
                # Merge with defaults
                return self._merge_configs(default_config, loaded_config)
        
        return default_config
    
    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """Recursively merge configuration dictionaries"""
        merged = default.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def validate_configuration(self):
        """Validate security configuration"""
        errors = []
        
        # Validate encryption settings
        if not self.config['security']['encryption']['enabled']:
            errors.append("Encryption is disabled - this is not recommended for production")
        
        # Validate password policy
        policy = self.config['security']['authentication']['password_policy']
        if policy['min_length'] < 8:
            errors.append("Password minimum length should be at least 8 characters")
        
        # Validate compliance settings
        compliance = self.config['security']['compliance']
        if compliance['data_retention_days'] < 30:
            errors.append("Data retention period should be at least 30 days")
        
        # Validate audit logging
        if not self.config['security']['audit_logging']['enabled']:
            errors.append("Audit logging is disabled - this may violate compliance requirements")
        
        if errors:
            raise ValueError(f"Security configuration validation failed: {'; '.join(errors)}")
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }

# Example usage and deployment
class SecureAPMService:
    def __init__(self):
        self.config_manager = SecureConfigurationManager()
        self.security_config = SecurityConfig()
        self.sanitizer = DataSanitizer(self.security_config)
        self.access_control = AccessControlManager()
        self.compliance_manager = ComplianceManager()
        self.audit_logger = SecurityAuditLogger()
        
    async def initialize_security_controls(self):
        """Initialize all security controls"""
        # Set up encryption
        if self.config_manager.config['security']['encryption']['enabled']:
            self.sanitizer.config.encryption_enabled = True
        
        # Initialize compliance controls
        gdpr_controls = self.compliance_manager.implement_gdpr_controls(self)
        retention_policies = self.compliance_manager.implement_data_retention_policies()
        
        # Start security monitoring
        self._start_security_monitoring()
        
        return {
            'encryption_enabled': self.security_config.encryption_enabled,
            'compliance_standards': [std.value for std in [ComplianceStandard.GDPR, ComplianceStandard.SOC2]],
            'audit_logging_enabled': True,
            'gdpr_controls_count': len(gdpr_controls['implementations']),
            'retention_policies_count': len(retention_policies['retention_jobs'])
        }
    
    def _start_security_monitoring(self):
        """Start continuous security monitoring"""
        import asyncio
        import threading
        
        def security_monitor():
            while True:
                try:
                    # Check for anomalous behavior
                    anomalies = self.audit_logger.detect_anomalous_behavior()
                    
                    for anomaly in anomalies:
                        self.audit_logger.log_security_event(
                            anomaly['type'],
                            anomaly['severity'],
                            anomaly['description'],
                            anomaly.get('user_id')
                        )
                    
                    time.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    logging.error(f"Security monitoring error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=security_monitor, daemon=True)
        monitor_thread.start()

# Docker security configuration
security_dockerfile = """
FROM python:3.9-slim

# Create non-root user
RUN groupadd -r apmuser && useradd -r -g apmuser apmuser

# Set security-focused environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

WORKDIR /app

# Install security dependencies
COPY requirements-security.txt .
RUN pip install --no-cache-dir -r requirements-security.txt

# Copy application code
COPY --chown=apmuser:apmuser src/ .
COPY --chown=apmuser:apmuser config/security/ ./config/

# Set secure permissions
RUN chmod -R 750 /app
RUN chmod -R 640 /app/config/

# Switch to non-root user
USER apmuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py

EXPOSE 8080

CMD ["python", "-m", "apm.secure_service"]
"""

# Kubernetes security configuration
k8s_security_config = """
apiVersion: v1
kind: SecurityContext
metadata:
  name: apm-security-context
spec:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  seccompProfile:
    type: RuntimeDefault
  seLinuxOptions:
    level: "s0:c123,c456"

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: apm-network-policy
spec:
  podSelector:
    matchLabels:
      app: apm-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
"""
```

This comprehensive APM Security & Compliance framework provides enterprise-grade security controls, regulatory compliance, audit trails, and secure deployment configurations while maintaining full monitoring capabilities.