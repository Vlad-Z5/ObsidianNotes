# Architecture Healthcare

## Healthcare Architecture

Healthcare systems require specialized architectures that prioritize patient safety, data security, regulatory compliance, and seamless integration across diverse systems. This guide provides comprehensive implementations for HIPAA compliance, electronic health records, medical device integration, telemedicine platforms, and healthcare analytics.

### HIPAA Compliance

HIPAA (Health Insurance Portability and Accountability Act) compliance is fundamental to healthcare architecture, requiring robust data protection, access controls, audit logging, and privacy safeguards.

#### HIPAA Security Framework Implementation

```python
import asyncio
import hashlib
import hmac
import base64
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import cryptography.fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import asyncpg

class DataClassification(Enum):
    PHI = "PHI"  # Protected Health Information
    PII = "PII"  # Personally Identifiable Information
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"

class AccessLevel(Enum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    ADMIN = "ADMIN"

@dataclass
class HIPAAUser:
    user_id: str
    role: str
    department: str
    access_levels: Set[AccessLevel]
    data_classifications: Set[DataClassification]
    last_training_date: datetime
    mfa_enabled: bool = True
    
@dataclass
class AccessAttempt:
    user_id: str
    resource_id: str
    action: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    success: bool
    reason: Optional[str] = None

class HIPAASecurityManager:
    """HIPAA-compliant security and access control system"""
    
    def __init__(self, db_pool: asyncpg.Pool, encryption_key: bytes):
        self.db_pool = db_pool
        self.fernet = cryptography.fernet.Fernet(encryption_key)
        self.access_log = []
        self.failed_attempts = {}
        self.logger = logging.getLogger(__name__)
        
        # HIPAA minimum necessary access rules
        self.minimum_necessary_rules = {
            'nurse': {'PHI': ['patient_vitals', 'medication_list', 'care_plans']},
            'doctor': {'PHI': ['full_medical_record', 'lab_results', 'imaging']},
            'admin': {'PII': ['contact_info', 'insurance_data']},
            'billing': {'PII': ['insurance_data', 'payment_info']}
        }
        
    async def authenticate_user(
        self, 
        username: str, 
        password: str, 
        mfa_token: Optional[str] = None,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Optional[HIPAAUser]:
        """Authenticate user with HIPAA-compliant multi-factor authentication"""
        
        access_attempt = AccessAttempt(
            user_id=username,
            resource_id="authentication",
            action="login",
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
        
        try:
            # Check for account lockout
            if await self._is_account_locked(username):
                access_attempt.reason = "Account locked due to failed attempts"
                await self._log_access_attempt(access_attempt)
                return None
            
            # Verify password
            user_data = await self._verify_credentials(username, password)
            if not user_data:
                await self._record_failed_attempt(username)
                access_attempt.reason = "Invalid credentials"
                await self._log_access_attempt(access_attempt)
                return None
            
            # Verify MFA if enabled
            if user_data['mfa_enabled'] and not await self._verify_mfa(username, mfa_token):
                access_attempt.reason = "MFA verification failed"
                await self._log_access_attempt(access_attempt)
                return None
            
            # Check training compliance
            training_date = user_data['last_training_date']
            if training_date < datetime.utcnow() - timedelta(days=365):
                access_attempt.reason = "HIPAA training expired"
                await self._log_access_attempt(access_attempt)
                return None
            
            # Create user session
            user = HIPAAUser(
                user_id=user_data['user_id'],
                role=user_data['role'],
                department=user_data['department'],
                access_levels=set(AccessLevel(level) for level in user_data['access_levels']),
                data_classifications=set(DataClassification(cls) for cls in user_data['data_classifications']),
                last_training_date=training_date,
                mfa_enabled=user_data['mfa_enabled']
            )
            
            # Log successful access
            access_attempt.success = True
            access_attempt.user_id = user.user_id
            await self._log_access_attempt(access_attempt)
            
            # Clear failed attempts
            if username in self.failed_attempts:
                del self.failed_attempts[username]
            
            return user
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            access_attempt.reason = f"System error: {str(e)}"
            await self._log_access_attempt(access_attempt)
            return None
    
    async def authorize_access(
        self,
        user: HIPAAUser,
        resource_id: str,
        action: str,
        patient_id: Optional[str] = None
    ) -> bool:
        """Authorize access based on HIPAA minimum necessary principle"""
        
        try:
            # Get resource metadata
            resource_metadata = await self._get_resource_metadata(resource_id)
            if not resource_metadata:
                return False
            
            # Check if user has required access level
            required_access = AccessLevel(resource_metadata['required_access_level'])
            if required_access not in user.access_levels:
                await self._log_unauthorized_access(user, resource_id, action, "Insufficient access level")
                return False
            
            # Check data classification access
            data_classification = DataClassification(resource_metadata['data_classification'])
            if data_classification not in user.data_classifications:
                await self._log_unauthorized_access(user, resource_id, action, "Insufficient data classification access")
                return False
            
            # Apply minimum necessary rules
            if not await self._check_minimum_necessary(user, resource_id, patient_id):
                await self._log_unauthorized_access(user, resource_id, action, "Minimum necessary rule violation")
                return False
            
            # Check patient relationship (for PHI access)
            if data_classification == DataClassification.PHI and patient_id:
                if not await self._check_patient_relationship(user, patient_id):
                    await self._log_unauthorized_access(user, resource_id, action, "No patient relationship")
                    return False
            
            # Log authorized access
            await self._log_access_attempt(AccessAttempt(
                user_id=user.user_id,
                resource_id=resource_id,
                action=action,
                timestamp=datetime.utcnow(),
                ip_address="",  # Would be captured from request context
                user_agent="",
                success=True
            ))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Authorization error: {e}")
            return False
    
    async def encrypt_phi_data(self, data: Dict) -> str:
        """Encrypt PHI data using FIPS 140-2 compliant encryption"""
        try:
            # Serialize data
            json_data = json.dumps(data, default=str)
            
            # Encrypt using Fernet (AES 128 in CBC mode)
            encrypted_data = self.fernet.encrypt(json_data.encode())
            
            # Return base64 encoded for storage
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            self.logger.error(f"Encryption error: {e}")
            raise
    
    async def decrypt_phi_data(self, encrypted_data: str) -> Dict:
        """Decrypt PHI data"""
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            raise
    
    async def generate_audit_report(
        self, 
        start_date: datetime, 
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict:
        """Generate HIPAA audit report"""
        
        async with self.db_pool.acquire() as conn:
            # Base query
            query = """
                SELECT user_id, resource_id, action, timestamp, ip_address, 
                       success, reason, patient_id
                FROM access_log 
                WHERE timestamp BETWEEN $1 AND $2
            """
            params = [start_date, end_date]
            
            # Filter by user if specified
            if user_id:
                query += " AND user_id = $3"
                params.append(user_id)
            
            query += " ORDER BY timestamp DESC"
            
            access_records = await conn.fetch(query, *params)
            
            # Analyze access patterns
            total_attempts = len(access_records)
            successful_attempts = sum(1 for record in access_records if record['success'])
            failed_attempts = total_attempts - successful_attempts
            
            # Group by user
            user_activity = {}
            for record in access_records:
                user = record['user_id']
                if user not in user_activity:
                    user_activity[user] = {
                        'total_attempts': 0,
                        'successful_attempts': 0,
                        'failed_attempts': 0,
                        'resources_accessed': set(),
                        'patients_accessed': set()
                    }
                
                user_activity[user]['total_attempts'] += 1
                if record['success']:
                    user_activity[user]['successful_attempts'] += 1
                    user_activity[user]['resources_accessed'].add(record['resource_id'])
                    if record['patient_id']:
                        user_activity[user]['patients_accessed'].add(record['patient_id'])
                else:
                    user_activity[user]['failed_attempts'] += 1
            
            # Convert sets to counts for JSON serialization
            for user_data in user_activity.values():
                user_data['unique_resources'] = len(user_data['resources_accessed'])
                user_data['unique_patients'] = len(user_data['patients_accessed'])
                del user_data['resources_accessed']
                del user_data['patients_accessed']
            
            return {
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_access_attempts': total_attempts,
                    'successful_attempts': successful_attempts,
                    'failed_attempts': failed_attempts,
                    'success_rate': successful_attempts / total_attempts if total_attempts > 0 else 0
                },
                'user_activity': user_activity,
                'security_incidents': await self._identify_security_incidents(access_records),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def _check_minimum_necessary(
        self, 
        user: HIPAAUser, 
        resource_id: str, 
        patient_id: Optional[str]
    ) -> bool:
        """Check if access adheres to minimum necessary principle"""
        
        # Get allowed resources for user role
        allowed_resources = self.minimum_necessary_rules.get(user.role.lower(), {})
        
        # Get resource details
        resource_metadata = await self._get_resource_metadata(resource_id)
        resource_type = resource_metadata.get('resource_type')
        
        # Check if user role can access this resource type
        for classification, resources in allowed_resources.items():
            if resource_type in resources:
                return True
        
        return False
    
    async def _identify_security_incidents(self, access_records: List) -> List[Dict]:
        """Identify potential security incidents from access logs"""
        incidents = []
        
        # Group by user and check for suspicious patterns
        user_attempts = {}
        for record in access_records:
            user_id = record['user_id']
            if user_id not in user_attempts:
                user_attempts[user_id] = []
            user_attempts[user_id].append(record)
        
        for user_id, attempts in user_attempts.items():
            # Check for multiple failed attempts
            failed_attempts = [a for a in attempts if not a['success']]
            if len(failed_attempts) >= 5:
                incidents.append({
                    'type': 'Multiple Failed Login Attempts',
                    'user_id': user_id,
                    'count': len(failed_attempts),
                    'severity': 'HIGH',
                    'first_attempt': min(a['timestamp'] for a in failed_attempts).isoformat(),
                    'last_attempt': max(a['timestamp'] for a in failed_attempts).isoformat()
                })
            
            # Check for unusual access patterns (e.g., accessing many different patients)
            successful_attempts = [a for a in attempts if a['success']]
            unique_patients = set(a['patient_id'] for a in successful_attempts if a['patient_id'])
            if len(unique_patients) > 50:  # Threshold for suspicious activity
                incidents.append({
                    'type': 'Unusual Patient Access Pattern',
                    'user_id': user_id,
                    'unique_patients_accessed': len(unique_patients),
                    'severity': 'MEDIUM',
                    'time_period': f"{min(a['timestamp'] for a in successful_attempts).isoformat()} to {max(a['timestamp'] for a in successful_attempts).isoformat()}"
                })
        
        return incidents
```

### Electronic Health Records

EHR systems require robust data standardization, interoperability, and clinical workflow integration to ensure seamless care coordination.

#### FHIR-Compliant EHR Implementation

```python
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import aiohttp
import asyncpg

class ResourceType(Enum):
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    OBSERVATION = "Observation"
    MEDICATION_REQUEST = "MedicationRequest"
    CONDITION = "Condition"
    ENCOUNTER = "Encounter"
    DIAGNOSTIC_REPORT = "DiagnosticReport"

class ObservationStatus(Enum):
    FINAL = "final"
    PRELIMINARY = "preliminary"
    AMENDED = "amended"
    CANCELLED = "cancelled"

@dataclass
class FHIRResource:
    id: str
    resourceType: ResourceType
    meta: Dict = field(default_factory=dict)
    text: Dict = field(default_factory=dict)
    
@dataclass
class Patient(FHIRResource):
    identifier: List[Dict] = field(default_factory=list)
    name: List[Dict] = field(default_factory=list)
    telecom: List[Dict] = field(default_factory=list)
    gender: str = ""
    birthDate: str = ""
    address: List[Dict] = field(default_factory=list)
    maritalStatus: Dict = field(default_factory=dict)
    contact: List[Dict] = field(default_factory=list)
    
@dataclass
class Observation(FHIRResource):
    status: ObservationStatus = ObservationStatus.FINAL
    category: List[Dict] = field(default_factory=list)
    code: Dict = field(default_factory=dict)
    subject: Dict = field(default_factory=dict)
    encounter: Dict = field(default_factory=dict)
    effectiveDateTime: str = ""
    valueQuantity: Dict = field(default_factory=dict)
    interpretation: List[Dict] = field(default_factory=list)
    referenceRange: List[Dict] = field(default_factory=list)

class FHIRRepository:
    """FHIR-compliant Electronic Health Record repository"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.terminology_server_url = "https://tx.fhir.org/r4"
        
    async def create_patient(self, patient_data: Dict) -> Patient:
        """Create a new patient record"""
        
        patient = Patient(
            id=str(uuid.uuid4()),
            resourceType=ResourceType.PATIENT,
            identifier=patient_data.get('identifier', []),
            name=patient_data.get('name', []),
            telecom=patient_data.get('telecom', []),
            gender=patient_data.get('gender', ''),
            birthDate=patient_data.get('birthDate', ''),
            address=patient_data.get('address', []),
            maritalStatus=patient_data.get('maritalStatus', {}),
            contact=patient_data.get('contact', [])
        )
        
        # Add metadata
        patient.meta = {
            'versionId': '1',
            'lastUpdated': datetime.utcnow().isoformat() + 'Z',
            'profile': ['http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient']
        }
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fhir_resources (id, resource_type, version_id, data, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, 
            patient.id, patient.resourceType.value, '1', 
            json.dumps(patient.__dict__, default=str),
            datetime.utcnow(), datetime.utcnow())
        
        return patient
    
    async def create_observation(
        self,
        patient_id: str,
        code: Dict,
        value: Dict,
        encounter_id: Optional[str] = None,
        effective_date: Optional[datetime] = None
    ) -> Observation:
        """Create a clinical observation"""
        
        observation = Observation(
            id=str(uuid.uuid4()),
            resourceType=ResourceType.OBSERVATION,
            status=ObservationStatus.FINAL,
            category=[{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'vital-signs',
                    'display': 'Vital Signs'
                }]
            }],
            code=code,
            subject={'reference': f'Patient/{patient_id}'},
            effectiveDateTime=(effective_date or datetime.utcnow()).isoformat() + 'Z',
            valueQuantity=value
        )
        
        if encounter_id:
            observation.encounter = {'reference': f'Encounter/{encounter_id}'}
        
        # Add metadata
        observation.meta = {
            'versionId': '1',
            'lastUpdated': datetime.utcnow().isoformat() + 'Z',
            'profile': ['http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab']
        }
        
        # Validate against reference ranges
        await self._validate_observation_values(observation)
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fhir_resources (id, resource_type, version_id, data, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
            observation.id, observation.resourceType.value, '1',
            json.dumps(observation.__dict__, default=str),
            datetime.utcnow(), datetime.utcnow())
        
        # Trigger clinical decision support
        await self._trigger_clinical_alerts(observation)
        
        return observation
    
    async def search_resources(
        self,
        resource_type: ResourceType,
        search_params: Dict[str, Any]
    ) -> List[Dict]:
        """Search for FHIR resources using standard search parameters"""
        
        query_conditions = []
        query_params = []
        param_count = 1
        
        # Build dynamic query based on search parameters
        base_query = """
            SELECT id, resource_type, version_id, data, created_at, updated_at
            FROM fhir_resources 
            WHERE resource_type = $1
        """
        query_params.append(resource_type.value)
        param_count += 1
        
        # Handle common search parameters
        if 'patient' in search_params:
            query_conditions.append(f"data->>'subject' LIKE ${param_count}")
            query_params.append(f"%Patient/{search_params['patient']}%")
            param_count += 1
        
        if 'date' in search_params:
            # Parse date range
            date_range = search_params['date']
            if 'ge' in date_range:  # Greater than or equal
                query_conditions.append(f"(data->>'effectiveDateTime')::timestamp >= ${param_count}")
                query_params.append(date_range['ge'])
                param_count += 1
            if 'le' in date_range:  # Less than or equal
                query_conditions.append(f"(data->>'effectiveDateTime')::timestamp <= ${param_count}")
                query_params.append(date_range['le'])
                param_count += 1
        
        if 'code' in search_params:
            query_conditions.append(f"data->'code'->'coding' @> ${param_count}")
            query_params.append(json.dumps([{'code': search_params['code']}]))
            param_count += 1
        
        # Combine conditions
        if query_conditions:
            base_query += " AND " + " AND ".join(query_conditions)
        
        base_query += " ORDER BY created_at DESC LIMIT 100"
        
        async with self.db_pool.acquire() as conn:
            records = await conn.fetch(base_query, *query_params)
            
            return [
                {
                    'id': record['id'],
                    'resourceType': record['resource_type'],
                    'versionId': record['version_id'],
                    'lastUpdated': record['updated_at'].isoformat() + 'Z',
                    **json.loads(record['data'])
                }
                for record in records
            ]
    
    async def get_patient_summary(self, patient_id: str) -> Dict:
        """Generate comprehensive patient summary"""
        
        # Get patient demographics
        patient_data = await self.search_resources(
            ResourceType.PATIENT,
            {'_id': patient_id}
        )
        
        if not patient_data:
            raise ValueError(f"Patient {patient_id} not found")
        
        patient = patient_data[0]
        
        # Get recent observations
        recent_observations = await self.search_resources(
            ResourceType.OBSERVATION,
            {
                'patient': patient_id,
                'date': {'ge': (datetime.utcnow() - timedelta(days=30)).isoformat()}
            }
        )
        
        # Get active conditions
        active_conditions = await self.search_resources(
            ResourceType.CONDITION,
            {'patient': patient_id, 'clinical-status': 'active'}
        )
        
        # Get recent medications
        active_medications = await self.search_resources(
            ResourceType.MEDICATION_REQUEST,
            {
                'patient': patient_id,
                'status': 'active'
            }
        )
        
        # Generate clinical summary
        return {
            'patient': patient,
            'summary': {
                'demographics': {
                    'age': self._calculate_age(patient.get('birthDate', '')),
                    'gender': patient.get('gender', ''),
                    'mrn': self._extract_mrn(patient.get('identifier', []))
                },
                'vital_signs': self._extract_vital_signs(recent_observations),
                'active_conditions': [
                    {
                        'code': condition.get('code', {}),
                        'onsetDateTime': condition.get('onsetDateTime', ''),
                        'severity': condition.get('severity', {})
                    }
                    for condition in active_conditions
                ],
                'active_medications': [
                    {
                        'medicationCodeableConcept': med.get('medicationCodeableConcept', {}),
                        'dosageInstruction': med.get('dosageInstruction', []),
                        'authoredOn': med.get('authoredOn', '')
                    }
                    for med in active_medications
                ],
                'recent_encounters': await self._get_recent_encounters(patient_id),
                'alerts': await self._get_patient_alerts(patient_id)
            },
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    async def _validate_observation_values(self, observation: Observation) -> None:
        """Validate observation values against clinical reference ranges"""
        
        code = observation.code.get('coding', [{}])[0].get('code', '')
        value = observation.valueQuantity
        
        # Common vital signs reference ranges
        reference_ranges = {
            '8480-6': {'min': 90, 'max': 140, 'unit': 'mmHg'},    # Systolic BP
            '8462-4': {'min': 60, 'max': 90, 'unit': 'mmHg'},     # Diastolic BP
            '8867-4': {'min': 60, 'max': 100, 'unit': '/min'},    # Heart Rate
            '8310-5': {'min': 36.1, 'max': 37.2, 'unit': 'Cel'},  # Body Temperature
            '33747-0': {'min': 18.5, 'max': 24.9, 'unit': 'kg/m2'} # BMI
        }
        
        if code in reference_ranges:
            ref_range = reference_ranges[code]
            obs_value = value.get('value', 0)
            
            # Add reference range to observation
            observation.referenceRange = [{
                'low': {'value': ref_range['min'], 'unit': ref_range['unit']},
                'high': {'value': ref_range['max'], 'unit': ref_range['unit']},
                'type': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/referencerange-meaning',
                        'code': 'normal',
                        'display': 'Normal Range'
                    }]
                }
            }]
            
            # Add interpretation
            if obs_value < ref_range['min']:
                observation.interpretation = [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                        'code': 'L',
                        'display': 'Low'
                    }]
                }]
            elif obs_value > ref_range['max']:
                observation.interpretation = [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                        'code': 'H',
                        'display': 'High'
                    }]
                }]
            else:
                observation.interpretation = [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                        'code': 'N',
                        'display': 'Normal'
                    }]
                }]
    
    async def _trigger_clinical_alerts(self, observation: Observation) -> None:
        """Trigger clinical decision support alerts based on observation values"""
        
        code = observation.code.get('coding', [{}])[0].get('code', '')
        value = observation.valueQuantity.get('value', 0)
        patient_ref = observation.subject.get('reference', '')
        
        alerts = []
        
        # Critical value alerts
        critical_values = {
            '8480-6': {'critical_high': 180, 'critical_low': 70},   # Systolic BP
            '8462-4': {'critical_high': 110, 'critical_low': 40},   # Diastolic BP
            '8867-4': {'critical_high': 120, 'critical_low': 50},   # Heart Rate
            '8310-5': {'critical_high': 39.0, 'critical_low': 35.0} # Temperature
        }
        
        if code in critical_values:
            critical_range = critical_values[code]
            
            if value >= critical_range['critical_high']:
                alerts.append({
                    'type': 'CRITICAL_HIGH_VALUE',
                    'message': f"Critical high {observation.code.get('coding', [{}])[0].get('display', '')}: {value}",
                    'severity': 'CRITICAL',
                    'patient': patient_ref,
                    'observation_id': observation.id
                })
            elif value <= critical_range['critical_low']:
                alerts.append({
                    'type': 'CRITICAL_LOW_VALUE',
                    'message': f"Critical low {observation.code.get('coding', [{}])[0].get('display', '')}: {value}",
                    'severity': 'CRITICAL',
                    'patient': patient_ref,
                    'observation_id': observation.id
                })
        
        # Send alerts to clinical staff
        for alert in alerts:
            await self._send_clinical_alert(alert)
    
    async def _send_clinical_alert(self, alert: Dict) -> None:
        """Send clinical alert to appropriate healthcare providers"""
        
        # This would integrate with notification systems, paging systems, etc.
        alert_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'type': alert['type'],
            'severity': alert['severity'],
            'message': alert['message'],
            'patient': alert['patient'],
            'observation_id': alert.get('observation_id'),
            'acknowledged': False
        }
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO clinical_alerts (id, alert_type, severity, message, patient_ref, 
                                           observation_id, created_at, acknowledged)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            alert_data['id'], alert_data['type'], alert_data['severity'],
            alert_data['message'], alert_data['patient'], alert_data.get('observation_id'),
            datetime.utcnow(), False)
```

### Medical Device Integration

Medical device integration requires real-time data collection, device connectivity, safety protocols, and seamless integration with EHR systems.

#### Medical Device Integration Framework

```python
import asyncio
import struct
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import socket
import serial
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
import aiohttp
import asyncpg

class DeviceType(Enum):
    PATIENT_MONITOR = "PATIENT_MONITOR"
    VENTILATOR = "VENTILATOR"
    INFUSION_PUMP = "INFUSION_PUMP"
    ECG_MONITOR = "ECG_MONITOR"
    PULSE_OXIMETER = "PULSE_OXIMETER"
    BLOOD_PRESSURE = "BLOOD_PRESSURE"
    TEMPERATURE_PROBE = "TEMPERATURE_PROBE"

class DeviceStatus(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    ALARM = "ALARM"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"

class AlarmPriority(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    TECHNICAL = "TECHNICAL"

@dataclass
class MedicalDevice:
    device_id: str
    device_type: DeviceType
    manufacturer: str
    model: str
    serial_number: str
    location: str
    ip_address: Optional[str] = None
    port: Optional[int] = None
    protocol: str = "TCP"
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_heartbeat: Optional[datetime] = None
    firmware_version: str = ""
    
@dataclass
class DeviceReading:
    device_id: str
    parameter: str
    value: float
    unit: str
    timestamp: datetime
    quality: str = "GOOD"
    alarm_status: Optional[str] = None

@dataclass
class DeviceAlarm:
    alarm_id: str
    device_id: str
    alarm_code: str
    priority: AlarmPriority
    message: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

class MedicalDeviceManager:
    """Medical device integration and monitoring system"""
    
    def __init__(self, db_pool: asyncpg.Pool, fhir_repository: 'FHIRRepository'):
        self.db_pool = db_pool
        self.fhir_repository = fhir_repository
        self.devices: Dict[str, MedicalDevice] = {}
        self.device_connections: Dict[str, Any] = {}
        self.alarm_handlers: List[Callable] = []
        self.data_processors: Dict[DeviceType, Callable] = {}
        self.is_running = False
        
        # Configure device-specific data processors
        self._setup_data_processors()
        
    def register_device(self, device: MedicalDevice) -> None:
        """Register a medical device for monitoring"""
        self.devices[device.device_id] = device
        
    async def start_monitoring(self) -> None:
        """Start monitoring all registered devices"""
        self.is_running = True
        
        # Start monitoring tasks for each device
        tasks = []
        for device_id, device in self.devices.items():
            task = asyncio.create_task(self._monitor_device(device))
            tasks.append(task)
        
        # Start alarm processing task
        alarm_task = asyncio.create_task(self._process_alarms())
        tasks.append(alarm_task)
        
        # Wait for all tasks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring all devices"""
        self.is_running = False
        
        # Close all device connections
        for device_id, connection in self.device_connections.items():
            try:
                if hasattr(connection, 'close'):
                    connection.close()
            except Exception as e:
                print(f"Error closing connection for device {device_id}: {e}")
        
        self.device_connections.clear()
    
    async def _monitor_device(self, device: MedicalDevice) -> None:
        """Monitor a specific medical device"""
        while self.is_running:
            try:
                # Establish connection if not connected
                if device.device_id not in self.device_connections:
                    await self._connect_device(device)
                
                # Read data from device
                readings = await self._read_device_data(device)
                
                # Process readings
                for reading in readings:
                    await self._process_device_reading(reading)
                
                # Update device status
                device.status = DeviceStatus.ONLINE
                device.last_heartbeat = datetime.utcnow()
                
                await self._update_device_status(device)
                
                # Wait before next reading
                await asyncio.sleep(1)  # 1-second polling interval
                
            except Exception as e:
                print(f"Error monitoring device {device.device_id}: {e}")
                device.status = DeviceStatus.ERROR
                await self._update_device_status(device)
                
                # Retry after delay
                await asyncio.sleep(5)
    
    async def _connect_device(self, device: MedicalDevice) -> None:
        """Establish connection to medical device"""
        
        if device.protocol == "TCP":
            # TCP/IP connection (e.g., for patient monitors)
            try:
                reader, writer = await asyncio.open_connection(
                    device.ip_address, 
                    device.port or 2575
                )
                self.device_connections[device.device_id] = {
                    'reader': reader,
                    'writer': writer,
                    'type': 'TCP'
                }
                
            except Exception as e:
                raise ConnectionError(f"Failed to connect to device {device.device_id}: {e}")
        
        elif device.protocol == "MODBUS":
            # Modbus TCP connection (e.g., for infusion pumps)
            try:
                master = modbus_tcp.TcpMaster(host=device.ip_address, port=device.port or 502)
                master.set_timeout(2.0)
                self.device_connections[device.device_id] = {
                    'master': master,
                    'type': 'MODBUS'
                }
                
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Modbus device {device.device_id}: {e}")
        
        elif device.protocol == "SERIAL":
            # Serial connection (e.g., for older devices)
            try:
                serial_conn = serial.Serial(
                    port=device.ip_address,  # Serial port path
                    baudrate=9600,
                    timeout=2.0
                )
                self.device_connections[device.device_id] = {
                    'serial': serial_conn,
                    'type': 'SERIAL'
                }
                
            except Exception as e:
                raise ConnectionError(f"Failed to connect to serial device {device.device_id}: {e}")
    
    async def _read_device_data(self, device: MedicalDevice) -> List[DeviceReading]:
        """Read data from medical device based on device type"""
        
        if device.device_id not in self.device_connections:
            return []
        
        connection = self.device_connections[device.device_id]
        readings = []
        
        try:
            if device.device_type == DeviceType.PATIENT_MONITOR:
                readings = await self._read_patient_monitor(device, connection)
            elif device.device_type == DeviceType.VENTILATOR:
                readings = await self._read_ventilator(device, connection)
            elif device.device_type == DeviceType.INFUSION_PUMP:
                readings = await self._read_infusion_pump(device, connection)
            elif device.device_type == DeviceType.PULSE_OXIMETER:
                readings = await self._read_pulse_oximeter(device, connection)
            else:
                # Generic device reading
                readings = await self._read_generic_device(device, connection)
                
        except Exception as e:
            print(f"Error reading data from device {device.device_id}: {e}")
            # Generate alarm for communication failure
            alarm = DeviceAlarm(
                alarm_id=f"COMM_{device.device_id}_{int(datetime.utcnow().timestamp())}",
                device_id=device.device_id,
                alarm_code="COMM_FAILURE",
                priority=AlarmPriority.HIGH,
                message=f"Communication failure with {device.device_type.value}",
                timestamp=datetime.utcnow()
            )
            await self._handle_device_alarm(alarm)
        
        return readings
    
    async def _read_patient_monitor(
        self, 
        device: MedicalDevice, 
        connection: Dict
    ) -> List[DeviceReading]:
        """Read data from patient monitor (e.g., Philips IntelliVue)"""
        
        readings = []
        timestamp = datetime.utcnow()
        
        if connection['type'] == 'TCP':
            try:
                # Send data request (simplified protocol)
                request = b'\x0C\x00\x00\x01\x00\x00\x00\x00'  # Request vital signs
                connection['writer'].write(request)
                await connection['writer'].drain()
                
                # Read response
                response = await connection['reader'].read(1024)
                
                # Parse response (device-specific parsing)
                vital_signs = self._parse_patient_monitor_data(response)
                
                for parameter, value, unit in vital_signs:
                    reading = DeviceReading(
                        device_id=device.device_id,
                        parameter=parameter,
                        value=value,
                        unit=unit,
                        timestamp=timestamp
                    )
                    readings.append(reading)
                    
            except Exception as e:
                raise e
        
        return readings
    
    async def _read_ventilator(
        self, 
        device: MedicalDevice, 
        connection: Dict
    ) -> List[DeviceReading]:
        """Read data from mechanical ventilator"""
        
        readings = []
        timestamp = datetime.utcnow()
        
        if connection['type'] == 'MODBUS':
            try:
                master = connection['master']
                
                # Read ventilator parameters from Modbus registers
                # Register addresses are device-specific
                registers = master.execute(1, cst.READ_HOLDING_REGISTERS, 0, 20)
                
                # Parse ventilator parameters
                parameters = {
                    'respiratory_rate': registers[0] / 10.0,  # breaths/min
                    'tidal_volume': registers[1],             # mL
                    'peep': registers[2] / 10.0,              # cmH2O
                    'peak_pressure': registers[3] / 10.0,     # cmH2O
                    'fio2': registers[4] / 10.0,              # %
                    'minute_volume': registers[5] / 100.0     # L/min
                }
                
                for param, value in parameters.items():
                    unit = self._get_parameter_unit(param)
                    reading = DeviceReading(
                        device_id=device.device_id,
                        parameter=param,
                        value=value,
                        unit=unit,
                        timestamp=timestamp
                    )
                    
                    # Check for alarm conditions
                    if self._check_ventilator_alarms(param, value):
                        reading.alarm_status = "ALARM"
                    
                    readings.append(reading)
                    
            except Exception as e:
                raise e
        
        return readings
    
    async def _process_device_reading(self, reading: DeviceReading) -> None:
        """Process and store device reading"""
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO device_readings (
                    device_id, parameter, value, unit, timestamp, quality, alarm_status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            reading.device_id, reading.parameter, reading.value, reading.unit,
            reading.timestamp, reading.quality, reading.alarm_status)
        
        # Get device info
        device = self.devices.get(reading.device_id)
        if not device:
            return
        
        # Process device-specific data
        processor = self.data_processors.get(device.device_type)
        if processor:
            await processor(reading)
        
        # Create FHIR Observation if configured
        await self._create_fhir_observation(reading)
        
        # Check for alarm conditions
        if reading.alarm_status == "ALARM":
            alarm = DeviceAlarm(
                alarm_id=f"PARAM_{reading.device_id}_{reading.parameter}_{int(reading.timestamp.timestamp())}",
                device_id=reading.device_id,
                alarm_code=f"{reading.parameter.upper()}_ALARM",
                priority=self._determine_alarm_priority(reading.parameter, reading.value),
                message=f"{reading.parameter} alarm: {reading.value} {reading.unit}",
                timestamp=reading.timestamp
            )
            await self._handle_device_alarm(alarm)
    
    async def _create_fhir_observation(self, reading: DeviceReading) -> None:
        """Create FHIR Observation from device reading"""
        
        # Get patient associated with device
        patient_id = await self._get_device_patient(reading.device_id)
        if not patient_id:
            return
        
        # Map device parameter to LOINC code
        loinc_code = self._map_parameter_to_loinc(reading.parameter)
        if not loinc_code:
            return
        
        # Create FHIR observation
        await self.fhir_repository.create_observation(
            patient_id=patient_id,
            code={
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': loinc_code['code'],
                    'display': loinc_code['display']
                }]
            },
            value={
                'value': reading.value,
                'unit': reading.unit,
                'system': 'http://unitsofmeasure.org',
                'code': reading.unit
            },
            effective_date=reading.timestamp
        )
    
    def _setup_data_processors(self) -> None:
        """Setup device-specific data processors"""
        
        self.data_processors[DeviceType.VENTILATOR] = self._process_ventilator_data
        self.data_processors[DeviceType.INFUSION_PUMP] = self._process_infusion_data
        self.data_processors[DeviceType.PATIENT_MONITOR] = self._process_monitor_data
    
    async def _process_ventilator_data(self, reading: DeviceReading) -> None:
        """Process ventilator-specific data"""
        
        # Calculate derived parameters
        if reading.parameter == 'tidal_volume' and reading.value < 300:
            # Low tidal volume alert for ARDS protocols
            await self._create_clinical_alert(
                reading.device_id,
                "LOW_TIDAL_VOLUME",
                f"Tidal volume below 300mL: {reading.value}mL",
                AlarmPriority.MEDIUM
            )
    
    async def _handle_device_alarm(self, alarm: DeviceAlarm) -> None:
        """Handle device alarm"""
        
        # Store alarm in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO device_alarms (
                    alarm_id, device_id, alarm_code, priority, message, 
                    timestamp, acknowledged, acknowledged_by, acknowledged_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            alarm.alarm_id, alarm.device_id, alarm.alarm_code, 
            alarm.priority.value, alarm.message, alarm.timestamp,
            alarm.acknowledged, alarm.acknowledged_by, alarm.acknowledged_at)
        
        # Send to alarm processing system
        for handler in self.alarm_handlers:
            try:
                await handler(alarm)
            except Exception as e:
                print(f"Error in alarm handler: {e}")
```

### Telemedicine Platforms

Telemedicine platforms require secure video conferencing, document sharing, prescription management, and integration with billing systems.

#### Telemedicine Platform Implementation

```python
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import aiohttp
import asyncpg
import jwt
import hashlib
import base64

class AppointmentStatus(Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

class AppointmentType(Enum):
    CONSULTATION = "CONSULTATION"
    FOLLOW_UP = "FOLLOW_UP"
    URGENT_CARE = "URGENT_CARE"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    SPECIALIST = "SPECIALIST"

@dataclass
class TelehealthAppointment:
    appointment_id: str
    patient_id: str
    provider_id: str
    appointment_type: AppointmentType
    scheduled_time: datetime
    duration_minutes: int = 30
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    meeting_room_id: Optional[str] = None
    notes: str = ""
    prescriptions: List[Dict] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    
@dataclass
class VideoSession:
    session_id: str
    appointment_id: str
    participants: List[str]
    started_at: datetime
    ended_at: Optional[datetime] = None
    recording_url: Optional[str] = None
    chat_transcript: List[Dict] = field(default_factory=list)

class TelehealthPlatform:
    """Comprehensive telemedicine platform"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.video_service_url = "https://api.videosdk.live"
        self.prescription_service_url = "https://api.prescriptions.com"
        self.active_sessions: Dict[str, VideoSession] = {}
        
    async def schedule_appointment(
        self,
        patient_id: str,
        provider_id: str,
        appointment_type: AppointmentType,
        scheduled_time: datetime,
        duration_minutes: int = 30
    ) -> TelehealthAppointment:
        """Schedule a telemedicine appointment"""
        
        appointment = TelehealthAppointment(
            appointment_id=str(uuid.uuid4()),
            patient_id=patient_id,
            provider_id=provider_id,
            appointment_type=appointment_type,
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes
        )
        
        # Validate availability
        if not await self._check_provider_availability(provider_id, scheduled_time, duration_minutes):
            raise ValueError("Provider not available at requested time")
        
        # Create virtual meeting room
        meeting_room = await self._create_meeting_room(appointment.appointment_id)
        appointment.meeting_room_id = meeting_room['room_id']
        
        # Store appointment
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO telehealth_appointments (
                    appointment_id, patient_id, provider_id, appointment_type,
                    scheduled_time, duration_minutes, status, meeting_room_id, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            appointment.appointment_id, appointment.patient_id, appointment.provider_id,
            appointment.appointment_type.value, appointment.scheduled_time,
            appointment.duration_minutes, appointment.status.value,
            appointment.meeting_room_id, appointment.notes)
        
        # Send appointment confirmations
        await self._send_appointment_notifications(appointment)
        
        return appointment
    
    async def start_video_session(
        self,
        appointment_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Start a video session for an appointment"""
        
        # Get appointment details
        appointment = await self._get_appointment(appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        # Verify user is participant
        if user_id not in [appointment['patient_id'], appointment['provider_id']]:
            raise ValueError("User not authorized for this appointment")
        
        # Check appointment time
        now = datetime.utcnow()
        scheduled_time = appointment['scheduled_time']
        if now < scheduled_time - timedelta(minutes=15):
            raise ValueError("Appointment not ready to start")
        
        # Create or join video session
        session_id = appointment['meeting_room_id']
        
        if session_id not in self.active_sessions:
            # Create new session
            video_session = VideoSession(
                session_id=session_id,
                appointment_id=appointment_id,
                participants=[user_id],
                started_at=now
            )
            self.active_sessions[session_id] = video_session
            
            # Update appointment status
            await self._update_appointment_status(appointment_id, AppointmentStatus.IN_PROGRESS)
        else:
            # Join existing session
            session = self.active_sessions[session_id]
            if user_id not in session.participants:
                session.participants.append(user_id)
        
        # Generate access token for video SDK
        access_token = await self._generate_video_token(user_id, session_id)
        
        return {
            'session_id': session_id,
            'access_token': access_token,
            'video_sdk_config': {
                'meeting_id': session_id,
                'name': await self._get_user_display_name(user_id),
                'micEnabled': True,
                'webcamEnabled': True
            }
        }
    
    async def end_video_session(self, session_id: str, user_id: str) -> None:
        """End a video session"""
        
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.ended_at = datetime.utcnow()
        
        # Save session data
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO video_sessions (
                    session_id, appointment_id, participants, started_at, ended_at, 
                    recording_url, chat_transcript
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            session.session_id, session.appointment_id, json.dumps(session.participants),
            session.started_at, session.ended_at, session.recording_url,
            json.dumps(session.chat_transcript))
        
        # Update appointment status
        await self._update_appointment_status(session.appointment_id, AppointmentStatus.COMPLETED)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
    
    async def create_prescription(
        self,
        appointment_id: str,
        provider_id: str,
        patient_id: str,
        medication: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create electronic prescription during telehealth visit"""
        
        # Verify provider authorization
        if not await self._verify_prescribing_authority(provider_id):
            raise ValueError("Provider not authorized to prescribe")
        
        # Create prescription
        prescription = {
            'prescription_id': str(uuid.uuid4()),
            'appointment_id': appointment_id,
            'provider_id': provider_id,
            'patient_id': patient_id,
            'medication': medication,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'PENDING'
        }
        
        # Drug interaction check
        interactions = await self._check_drug_interactions(patient_id, medication)
        if interactions:
            prescription['warnings'] = interactions
        
        # Send to pharmacy via e-prescribing network
        try:
            eprescription_response = await self._send_eprescription(prescription)
            prescription['eprescription_id'] = eprescription_response['id']
            prescription['status'] = 'SENT'
        except Exception as e:
            prescription['status'] = 'FAILED'
            prescription['error'] = str(e)
        
        # Store prescription
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO prescriptions (
                    prescription_id, appointment_id, provider_id, patient_id,
                    medication_data, status, created_at, eprescription_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            prescription['prescription_id'], appointment_id, provider_id, patient_id,
            json.dumps(medication), prescription['status'], datetime.utcnow(),
            prescription.get('eprescription_id'))
        
        return prescription
    
    async def share_document(
        self,
        appointment_id: str,
        user_id: str,
        document_data: bytes,
        document_name: str,
        document_type: str
    ) -> str:
        """Share document during telehealth session"""
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Encrypt document for HIPAA compliance
        encrypted_document = await self._encrypt_document(document_data)
        
        # Store document
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO shared_documents (
                    document_id, appointment_id, shared_by, document_name,
                    document_type, encrypted_data, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            document_id, appointment_id, user_id, document_name,
            document_type, encrypted_document, datetime.utcnow())
        
        # Notify other participants
        await self._notify_document_shared(appointment_id, user_id, document_name)
        
        return document_id
    
    async def generate_visit_summary(self, appointment_id: str) -> Dict[str, Any]:
        """Generate comprehensive visit summary"""
        
        # Get appointment details
        appointment = await self._get_appointment(appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        # Get session data
        session_data = await self._get_session_data(appointment_id)
        
        # Get prescriptions
        prescriptions = await self._get_appointment_prescriptions(appointment_id)
        
        # Get shared documents
        documents = await self._get_shared_documents(appointment_id)
        
        # Generate summary
        summary = {
            'appointment_id': appointment_id,
            'patient_id': appointment['patient_id'],
            'provider_id': appointment['provider_id'],
            'appointment_type': appointment['appointment_type'],
            'date': appointment['scheduled_time'].isoformat(),
            'duration': session_data.get('duration_minutes', 0) if session_data else 0,
            'status': appointment['status'],
            'chief_complaint': appointment.get('notes', ''),
            'prescriptions': [
                {
                    'medication': json.loads(p['medication_data']),
                    'status': p['status'],
                    'created_at': p['created_at'].isoformat()
                }
                for p in prescriptions
            ],
            'documents_shared': [
                {
                    'document_name': d['document_name'],
                    'document_type': d['document_type'],
                    'shared_by': d['shared_by'],
                    'created_at': d['created_at'].isoformat()
                }
                for d in documents
            ],
            'next_steps': await self._extract_next_steps(appointment_id),
            'follow_up_required': await self._determine_follow_up(appointment_id),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return summary
    
    async def _create_meeting_room(self, appointment_id: str) -> Dict[str, str]:
        """Create virtual meeting room"""
        
        # This would integrate with video SDK (e.g., Twilio, Agora, VideoSDK)
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {self._get_video_api_key()}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'roomName': f'telehealth_{appointment_id}',
                'enableRecording': True,
                'enableChat': True,
                'maxParticipants': 2
            }
            
            async with session.post(
                f"{self.video_service_url}/rooms",
                headers=headers,
                json=data
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    return {
                        'room_id': result['roomId'],
                        'room_url': result['roomUrl']
                    }
                else:
                    raise Exception(f"Failed to create meeting room: {response.status}")
    
    async def _send_eprescription(self, prescription: Dict) -> Dict:
        """Send prescription to pharmacy via e-prescribing network"""
        
        # This would integrate with e-prescribing networks like Surescripts
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {self._get_prescription_api_key()}',
                'Content-Type': 'application/json'
            }
            
            # Format prescription for e-prescribing standard
            eprescription_data = {
                'prescriber': {
                    'npi': await self._get_provider_npi(prescription['provider_id']),
                    'dea': await self._get_provider_dea(prescription['provider_id'])
                },
                'patient': {
                    'id': prescription['patient_id'],
                    'demographics': await self._get_patient_demographics(prescription['patient_id'])
                },
                'medication': prescription['medication'],
                'pharmacy': prescription.get('pharmacy_id'),
                'prescription_date': datetime.utcnow().isoformat()
            }
            
            async with session.post(
                f"{self.prescription_service_url}/prescriptions",
                headers=headers,
                json=eprescription_data
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"Failed to send e-prescription: {response.status}")
```

This comprehensive Healthcare Architecture guide provides production-ready implementations for HIPAA compliance, electronic health records, medical device integration, and telemedicine platforms. Each component is designed with patient safety, data security, and regulatory compliance as primary concerns.