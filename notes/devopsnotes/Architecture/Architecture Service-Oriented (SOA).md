# Architecture Service-Oriented (SOA)

## SOA Principles

Service-Oriented Architecture (SOA) is an architectural pattern that organizes software design around discrete services that communicate over well-defined interfaces. SOA emphasizes enterprise-wide service reuse, standardization, and governance to create flexible, maintainable systems.

### Service Characteristics

#### Loose Coupling
**Definition:** Services maintain minimal dependencies on each other and interact through well-defined interfaces.

**Example - Banking Services Loose Coupling:**
```python
# Good: Loose coupling through interface abstraction
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Service Interface Definitions
class AccountServiceInterface(ABC):
    """Interface for account operations"""
    
    @abstractmethod
    def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get current account balance"""
        pass
    
    @abstractmethod
    def validate_account(self, account_id: str) -> bool:
        """Validate if account exists and is active"""
        pass
    
    @abstractmethod
    def freeze_account(self, account_id: str, reason: str) -> bool:
        """Freeze account for security reasons"""
        pass

class TransactionServiceInterface(ABC):
    """Interface for transaction operations"""
    
    @abstractmethod
    def process_transfer(self, transfer_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process money transfer between accounts"""
        pass
    
    @abstractmethod
    def get_transaction_history(self, account_id: str, limit: int = 50) -> List[Dict]:
        """Get transaction history for an account"""
        pass

class NotificationServiceInterface(ABC):
    """Interface for notification operations"""
    
    @abstractmethod
    def send_transaction_alert(self, account_id: str, transaction_details: Dict) -> bool:
        """Send transaction notification to account holder"""
        pass

# Loosely coupled service implementation
class TransferService:
    """Money transfer service that depends on interfaces, not implementations"""
    
    def __init__(self, 
                 account_service: AccountServiceInterface,
                 transaction_service: TransactionServiceInterface,
                 notification_service: NotificationServiceInterface):
        self.account_service = account_service
        self.transaction_service = transaction_service
        self.notification_service = notification_service
    
    def execute_transfer(self, from_account: str, to_account: str, amount: float) -> Dict[str, Any]:
        """Execute transfer with proper validation and notifications"""
        
        # Validate accounts through interface (implementation details hidden)
        if not self.account_service.validate_account(from_account):
            return {"success": False, "error": "Invalid source account"}
        
        if not self.account_service.validate_account(to_account):
            return {"success": False, "error": "Invalid destination account"}
        
        # Check balance through interface
        balance_info = self.account_service.get_account_balance(from_account)
        if balance_info["balance"] < amount:
            return {"success": False, "error": "Insufficient funds"}
        
        # Process transfer through interface
        transfer_request = {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "currency": "USD",
            "reference": f"TRANSFER-{uuid.uuid4()}"
        }
        
        result = self.transaction_service.process_transfer(transfer_request)
        
        if result["success"]:
            # Send notifications through interface
            self.notification_service.send_transaction_alert(
                from_account, 
                {"type": "debit", "amount": amount, "reference": result["transaction_id"]}
            )
            self.notification_service.send_transaction_alert(
                to_account,
                {"type": "credit", "amount": amount, "reference": result["transaction_id"]}
            )
        
        return result

# Bad: Tight coupling (services directly depend on implementations)
class BadTransferService:
    """Tightly coupled service - harder to test and maintain"""
    
    def __init__(self):
        # Direct dependencies on concrete classes
        self.database = MySQLDatabase("prod_db")
        self.smtp_client = SMTPClient("mail.bank.com")
        self.audit_logger = FileAuditLogger("/var/log/transfers.log")
    
    def execute_transfer(self, from_account: str, to_account: str, amount: float):
        # Business logic mixed with infrastructure concerns
        # Difficult to test, change, or reuse
        sql = "SELECT balance FROM accounts WHERE id = %s"
        result = self.database.execute(sql, (from_account,))
        # ... rest of tightly coupled implementation
```

#### Service Contracts
**Definition:** Formal agreements that define service capabilities, interfaces, and quality attributes.

**Example - Comprehensive Service Contract:**
```xml
<!-- WSDL (Web Service Description Language) for Payment Service -->
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:tns="http://bank.example.com/payment"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             targetNamespace="http://bank.example.com/payment">

  <!-- Data Types -->
  <types>
    <schema xmlns="http://www.w3.org/2001/XMLSchema"
            targetNamespace="http://bank.example.com/payment">
      
      <complexType name="PaymentRequest">
        <sequence>
          <element name="fromAccount" type="string" minOccurs="1" maxOccurs="1"/>
          <element name="toAccount" type="string" minOccurs="1" maxOccurs="1"/>
          <element name="amount" type="decimal" minOccurs="1" maxOccurs="1"/>
          <element name="currency" type="string" minOccurs="1" maxOccurs="1"/>
          <element name="reference" type="string" minOccurs="0" maxOccurs="1"/>
          <element name="metadata" type="string" minOccurs="0" maxOccurs="1"/>
        </sequence>
      </complexType>
      
      <complexType name="PaymentResponse">
        <sequence>
          <element name="transactionId" type="string"/>
          <element name="status" type="string"/>
          <element name="timestamp" type="dateTime"/>
          <element name="fees" type="decimal"/>
          <element name="exchangeRate" type="decimal" minOccurs="0"/>
        </sequence>
      </complexType>
      
      <complexType name="PaymentFault">
        <sequence>
          <element name="errorCode" type="string"/>
          <element name="errorMessage" type="string"/>
          <element name="timestamp" type="dateTime"/>
        </sequence>
      </complexType>
    </schema>
  </types>

  <!-- Messages -->
  <message name="ProcessPaymentRequest">
    <part name="request" type="tns:PaymentRequest"/>
  </message>
  
  <message name="ProcessPaymentResponse">
    <part name="response" type="tns:PaymentResponse"/>
  </message>
  
  <message name="PaymentFault">
    <part name="fault" type="tns:PaymentFault"/>
  </message>

  <!-- Port Type (Interface) -->
  <portType name="PaymentServicePortType">
    <operation name="processPayment">
      <documentation>Process a payment between two accounts</documentation>
      <input message="tns:ProcessPaymentRequest"/>
      <output message="tns:ProcessPaymentResponse"/>
      <fault name="paymentFault" message="tns:PaymentFault"/>
    </operation>
  </portType>

  <!-- Binding -->
  <binding name="PaymentServiceSOAPBinding" type="tns:PaymentServicePortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="processPayment">
      <soap:operation soapAction="http://bank.example.com/payment/processPayment"/>
      <input>
        <soap:body use="literal"/>
      </input>
      <output>
        <soap:body use="literal"/>
      </output>
      <fault name="paymentFault">
        <soap:fault name="paymentFault" use="literal"/>
      </fault>
    </operation>
  </binding>

  <!-- Service -->
  <service name="PaymentService">
    <documentation>Payment processing service for internal bank operations</documentation>
    <port name="PaymentServiceSOAPPort" binding="tns:PaymentServiceSOAPBinding">
      <soap:address location="https://services.bank.com/payment/v2"/>
    </port>
  </service>
</definitions>
```

**Modern Service Contract (OpenAPI/Swagger):**
```yaml
# OpenAPI 3.0 Service Contract for Payment Service
openapi: 3.0.0
info:
  title: Payment Service API
  version: 2.1.0
  description: |
    Enterprise payment processing service for inter-account transfers.
    Supports domestic and international payments with real-time processing.
  contact:
    name: Payment Service Team
    email: payments@bank.com
  license:
    name: Internal Use Only

servers:
  - url: https://api.bank.com/payment/v2
    description: Production environment
  - url: https://staging-api.bank.com/payment/v2
    description: Staging environment

# Service Level Agreements
x-sla:
  availability: 99.9%
  response_time: "< 2 seconds for 95% of requests"
  throughput: "1000 requests/second"
  
# Security Requirements
security:
  - BearerAuth: []
  - ApiKeyAuth: []

paths:
  /payments:
    post:
      summary: Process a payment
      description: |
        Process a payment between two accounts with validation,
        fraud detection, and compliance checks.
      operationId: processPayment
      tags:
        - payments
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PaymentRequest'
            examples:
              domestic_transfer:
                summary: Domestic transfer example
                value:
                  fromAccount: "1234567890"
                  toAccount: "9876543210"
                  amount: 1000.00
                  currency: "USD"
                  reference: "Monthly rent payment"
      responses:
        '200':
          description: Payment processed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentResponse'
        '400':
          description: Invalid request data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          description: Authentication required
        '403':
          description: Insufficient permissions
        '409':
          description: Duplicate transaction
        '422':
          description: Business rule violation (insufficient funds, etc.)
        '500':
          description: Internal server error

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

  schemas:
    PaymentRequest:
      type: object
      required:
        - fromAccount
        - toAccount
        - amount
        - currency
      properties:
        fromAccount:
          type: string
          pattern: '^[0-9]{10}$'
          description: Source account number
          example: "1234567890"
        toAccount:
          type: string
          pattern: '^[0-9]{10}$'
          description: Destination account number
          example: "9876543210"
        amount:
          type: number
          format: decimal
          minimum: 0.01
          maximum: 1000000
          multipleOf: 0.01
          description: Payment amount
          example: 1000.00
        currency:
          type: string
          enum: ["USD", "EUR", "GBP", "JPY"]
          description: Currency code (ISO 4217)
          example: "USD"
        reference:
          type: string
          maxLength: 140
          description: Payment reference/description
          example: "Monthly rent payment"
        metadata:
          type: object
          additionalProperties: true
          description: Additional metadata for the payment

    PaymentResponse:
      type: object
      properties:
        transactionId:
          type: string
          format: uuid
          description: Unique transaction identifier
          example: "550e8400-e29b-41d4-a716-446655440000"
        status:
          type: string
          enum: ["completed", "pending", "failed"]
          description: Payment status
          example: "completed"
        timestamp:
          type: string
          format: date-time
          description: Processing timestamp
          example: "2023-12-01T10:30:00Z"
        fees:
          type: number
          format: decimal
          description: Processing fees applied
          example: 2.50
        exchangeRate:
          type: number
          format: decimal
          description: Exchange rate applied (if currency conversion)
          example: 1.0847

    ErrorResponse:
      type: object
      properties:
        errorCode:
          type: string
          description: Machine-readable error code
          example: "INSUFFICIENT_FUNDS"
        errorMessage:
          type: string
          description: Human-readable error message
          example: "Account balance is insufficient for this transaction"
        timestamp:
          type: string
          format: date-time
          description: Error timestamp
        requestId:
          type: string
          description: Request identifier for tracking
```

#### Service Autonomy
**Definition:** Services have control over their own logic and resources, making independent decisions.

**Example - Autonomous Risk Assessment Service:**
```python
class RiskAssessmentService:
    """Autonomous service for evaluating transaction risk"""
    
    def __init__(self, risk_config: Dict[str, Any]):
        self.risk_config = risk_config
        self.risk_models = self._load_risk_models()
        self.blacklist_cache = self._initialize_blacklist_cache()
        self.ml_model = self._load_ml_model()
    
    def assess_transaction_risk(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Autonomously assess transaction risk using multiple factors"""
        
        # Service makes its own decisions about risk assessment
        risk_score = 0
        risk_factors = []
        
        # 1. Amount-based risk assessment (service's own logic)
        amount_risk = self._assess_amount_risk(transaction['amount'])
        risk_score += amount_risk['score']
        if amount_risk['risk_factors']:
            risk_factors.extend(amount_risk['risk_factors'])
        
        # 2. Account behavior analysis (service's own data and logic)
        behavior_risk = self._assess_account_behavior(
            transaction['fromAccount'],
            transaction['amount']
        )
        risk_score += behavior_risk['score']
        if behavior_risk['risk_factors']:
            risk_factors.extend(behavior_risk['risk_factors'])
        
        # 3. Geographic risk assessment (service's own rules)
        geo_risk = self._assess_geographic_risk(transaction)
        risk_score += geo_risk['score']
        if geo_risk['risk_factors']:
            risk_factors.extend(geo_risk['risk_factors'])
        
        # 4. Machine learning risk prediction (service's own models)
        ml_risk = self._ml_risk_prediction(transaction)
        risk_score += ml_risk['score']
        if ml_risk['risk_factors']:
            risk_factors.extend(ml_risk['risk_factors'])
        
        # 5. Real-time blacklist check (service's own data)
        blacklist_risk = self._check_blacklists(transaction)
        risk_score += blacklist_risk['score']
        if blacklist_risk['risk_factors']:
            risk_factors.extend(blacklist_risk['risk_factors'])
        
        # Service autonomously determines risk level and required actions
        risk_level = self._calculate_risk_level(risk_score)
        required_actions = self._determine_required_actions(risk_level, risk_factors)
        
        return {
            "riskScore": risk_score,
            "riskLevel": risk_level,
            "riskFactors": risk_factors,
            "requiredActions": required_actions,
            "assessmentId": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "modelVersion": self.ml_model.version,
            "confidence": self._calculate_confidence(risk_factors)
        }
    
    def _assess_amount_risk(self, amount: float) -> Dict[str, Any]:
        """Service's own logic for amount-based risk assessment"""
        risk_score = 0
        risk_factors = []
        
        # High amount transactions
        if amount > self.risk_config['high_amount_threshold']:
            risk_score += 30
            risk_factors.append("HIGH_AMOUNT_TRANSACTION")
        
        # Unusual amount patterns (e.g., round numbers might be suspicious)
        if amount % 1000 == 0 and amount >= 10000:
            risk_score += 15
            risk_factors.append("ROUND_AMOUNT_PATTERN")
        
        # Micro-transaction fraud patterns
        if amount < 1.0:
            risk_score += 10
            risk_factors.append("MICRO_TRANSACTION")
        
        return {"score": risk_score, "risk_factors": risk_factors}
    
    def _assess_account_behavior(self, account_id: str, amount: float) -> Dict[str, Any]:
        """Service autonomously analyzes account behavior patterns"""
        risk_score = 0
        risk_factors = []
        
        # Service maintains its own view of account behavior
        account_history = self._get_account_transaction_history(account_id, days=30)
        
        # Calculate behavioral metrics autonomously
        avg_transaction_amount = sum(t['amount'] for t in account_history) / len(account_history) if account_history else 0
        transaction_frequency = len(account_history)
        
        # Deviation from normal behavior
        if amount > avg_transaction_amount * 5:
            risk_score += 25
            risk_factors.append("AMOUNT_DEVIATION_FROM_PATTERN")
        
        # Sudden increase in transaction frequency
        recent_transactions = [t for t in account_history if self._is_recent(t['timestamp'], hours=24)]
        if len(recent_transactions) > self.risk_config['normal_daily_transactions'] * 2:
            risk_score += 20
            risk_factors.append("HIGH_TRANSACTION_FREQUENCY")
        
        # New account risk
        account_age = self._get_account_age(account_id)
        if account_age < 30:  # Account less than 30 days old
            risk_score += 15
            risk_factors.append("NEW_ACCOUNT")
        
        return {"score": risk_score, "risk_factors": risk_factors}
    
    def _assess_geographic_risk(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Service's own geographic risk assessment logic"""
        risk_score = 0
        risk_factors = []
        
        # Service maintains its own geographic risk database
        source_location = self._get_account_location(transaction['fromAccount'])
        destination_location = self._get_account_location(transaction['toAccount'])
        
        # Cross-border transaction risk
        if source_location['country'] != destination_location['country']:
            risk_score += 20
            risk_factors.append("CROSS_BORDER_TRANSACTION")
            
            # High-risk country check
            if destination_location['country'] in self.risk_config['high_risk_countries']:
                risk_score += 30
                risk_factors.append("HIGH_RISK_DESTINATION_COUNTRY")
        
        # Time zone analysis
        source_timezone = source_location['timezone']
        current_hour = datetime.now(timezone(source_timezone)).hour
        
        # Unusual time transaction
        if current_hour < 6 or current_hour > 23:
            risk_score += 10
            risk_factors.append("UNUSUAL_TIME_TRANSACTION")
        
        return {"score": risk_score, "risk_factors": risk_factors}
    
    def _ml_risk_prediction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Service uses its own ML models for risk prediction"""
        risk_score = 0
        risk_factors = []
        
        # Service autonomously maintains and updates its ML models
        features = self._extract_features(transaction)
        
        # Fraud probability from ML model
        fraud_probability = self.ml_model.predict_fraud_probability(features)
        
        if fraud_probability > 0.8:
            risk_score += 40
            risk_factors.append("HIGH_ML_FRAUD_PROBABILITY")
        elif fraud_probability > 0.6:
            risk_score += 25
            risk_factors.append("MEDIUM_ML_FRAUD_PROBABILITY")
        elif fraud_probability > 0.4:
            risk_score += 10
            risk_factors.append("LOW_ML_FRAUD_PROBABILITY")
        
        # Anomaly detection
        anomaly_score = self.ml_model.detect_anomaly(features)
        if anomaly_score > 0.7:
            risk_score += 20
            risk_factors.append("TRANSACTION_ANOMALY_DETECTED")
        
        return {"score": risk_score, "risk_factors": risk_factors}
    
    def _check_blacklists(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Service maintains its own blacklist data"""
        risk_score = 0
        risk_factors = []
        
        from_account = transaction['fromAccount']
        to_account = transaction['toAccount']
        
        # Check account blacklists
        if self.blacklist_cache.is_blacklisted(from_account):
            risk_score += 100  # Maximum risk
            risk_factors.append("SOURCE_ACCOUNT_BLACKLISTED")
        
        if self.blacklist_cache.is_blacklisted(to_account):
            risk_score += 100  # Maximum risk
            risk_factors.append("DESTINATION_ACCOUNT_BLACKLISTED")
        
        # Check transaction pattern blacklists
        transaction_pattern = f"{from_account}-{to_account}-{transaction['amount']}"
        if self.blacklist_cache.is_pattern_blacklisted(transaction_pattern):
            risk_score += 80
            risk_factors.append("BLACKLISTED_TRANSACTION_PATTERN")
        
        return {"score": risk_score, "risk_factors": risk_factors}
    
    def _calculate_risk_level(self, risk_score: int) -> str:
        """Service autonomously determines risk level"""
        if risk_score >= 80:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _determine_required_actions(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Service autonomously determines what actions are required"""
        actions = []
        
        if risk_level == "HIGH":
            actions.extend(["BLOCK_TRANSACTION", "MANUAL_REVIEW", "NOTIFY_COMPLIANCE"])
        elif risk_level == "MEDIUM":
            actions.extend(["ADDITIONAL_VERIFICATION", "ENHANCED_MONITORING"])
        elif risk_level == "LOW":
            actions.append("STANDARD_MONITORING")
        
        # Specific actions based on risk factors
        if "CROSS_BORDER_TRANSACTION" in risk_factors:
            actions.append("VERIFY_BENEFICIARY_DETAILS")
        
        if "HIGH_AMOUNT_TRANSACTION" in risk_factors:
            actions.append("VERIFY_TRANSACTION_PURPOSE")
        
        if any("BLACKLISTED" in factor for factor in risk_factors):
            actions.append("IMMEDIATE_ESCALATION")
        
        return list(set(actions))  # Remove duplicates
    
    # Service manages its own data and caches
    def _get_account_transaction_history(self, account_id: str, days: int) -> List[Dict]:
        """Service maintains its own view of transaction history"""
        # Implementation would query service's own database
        pass
    
    def _get_account_location(self, account_id: str) -> Dict[str, str]:
        """Service maintains its own geographic data"""
        # Implementation would query service's own location database
        pass
    
    def _load_risk_models(self) -> Any:
        """Service manages its own ML models"""
        # Implementation would load service's own trained models
        pass
```

This demonstrates true service autonomy where the Risk Assessment Service:
- Makes its own decisions about risk scoring
- Maintains its own data and models
- Implements its own business logic
- Doesn't depend on other services for core functionality
- Can evolve its algorithms independently

#### Service Abstraction
**Definition:** Services hide their implementation details and expose only necessary information through interfaces.

**Example - Customer Service with Multiple Implementations:**
```python
# Abstract service interface that hides implementation details
class CustomerServiceInterface(ABC):
    """Abstract interface for customer operations"""
    
    @abstractmethod
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get customer profile information"""
        pass
    
    @abstractmethod
    def update_customer_contact(self, customer_id: str, contact_info: Dict) -> bool:
        """Update customer contact information"""
        pass
    
    @abstractmethod
    def get_customer_risk_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get customer risk assessment"""
        pass

# Implementation 1: Database-backed customer service
class DatabaseCustomerService(CustomerServiceInterface):
    """Customer service implementation using database storage"""
    
    def __init__(self, database_connection):
        self._db = database_connection
        self._cache = {}
    
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Implementation details hidden from consumers"""
        # Check cache first
        if customer_id in self._cache:
            cached_data, cache_time = self._cache[customer_id]
            if time.time() - cache_time < 300:  # 5 minute cache
                return cached_data
        
        # Query database
        query = """
            SELECT c.*, r.risk_level, r.risk_score 
            FROM customers c 
            LEFT JOIN customer_risk r ON c.id = r.customer_id 
            WHERE c.id = %s AND c.active = true
        """
        
        result = self._db.execute(query, (customer_id,)).fetchone()
        
        if result:
            profile = {
                "customerId": result['id'],
                "firstName": result['first_name'],
                "lastName": result['last_name'],
                "email": result['email'],
                "phone": result['phone'],
                "dateOfBirth": result['date_of_birth'].isoformat(),
                "kycStatus": result['kyc_status'],
                "riskProfile": {
                    "level": result['risk_level'],
                    "score": result['risk_score']
                },
                "lastUpdated": result['updated_at'].isoformat()
            }
            
            # Cache the result
            self._cache[customer_id] = (profile, time.time())
            return profile
        
        raise CustomerNotFoundError(f"Customer {customer_id} not found")
    
    def update_customer_contact(self, customer_id: str, contact_info: Dict) -> bool:
        """Update contact info with validation and audit trail"""
        # Implementation-specific validation
        self._validate_contact_info(contact_info)
        
        # Update database with transaction
        with self._db.transaction():
            # Update customer record
            update_query = """
                UPDATE customers 
                SET email = %s, phone = %s, updated_at = NOW() 
                WHERE id = %s
            """
            self._db.execute(update_query, (
                contact_info.get('email'),
                contact_info.get('phone'),
                customer_id
            ))
            
            # Create audit record
            audit_query = """
                INSERT INTO customer_audit 
                (customer_id, action, old_values, new_values, timestamp) 
                VALUES (%s, %s, %s, %s, NOW())
            """
            self._db.execute(audit_query, (
                customer_id,
                'CONTACT_UPDATE',
                json.dumps(self._get_current_contact(customer_id)),
                json.dumps(contact_info)
            ))
        
        # Invalidate cache
        if customer_id in self._cache:
            del self._cache[customer_id]
        
        return True

# Implementation 2: Microservice-backed customer service
class MicroserviceCustomerService(CustomerServiceInterface):
    """Customer service implementation using microservice calls"""
    
    def __init__(self, service_discovery, circuit_breaker):
        self._service_discovery = service_discovery
        self._circuit_breaker = circuit_breaker
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Implementation details hidden - uses microservice calls"""
        
        @self._circuit_breaker.call
        async def _fetch_customer_data():
            # Get customer service URL
            customer_service_url = await self._service_discovery.get_service_url("customer-service")
            
            # Call customer microservice
            response = await self._client.get(
                f"{customer_service_url}/api/v1/customers/{customer_id}",
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        
        @self._circuit_breaker.call
        async def _fetch_risk_data():
            # Get risk service URL
            risk_service_url = await self._service_discovery.get_service_url("risk-service")
            
            # Call risk microservice
            response = await self._client.get(
                f"{risk_service_url}/api/v1/risk-profiles/{customer_id}",
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        
        try:
            # Parallel calls to different microservices
            customer_data, risk_data = await asyncio.gather(
                _fetch_customer_data(),
                _fetch_risk_data()
            )
            
            # Combine data from different services
            return {
                "customerId": customer_data["id"],
                "firstName": customer_data["firstName"],
                "lastName": customer_data["lastName"],
                "email": customer_data["email"],
                "phone": customer_data["phone"],
                "dateOfBirth": customer_data["dateOfBirth"],
                "kycStatus": customer_data["kycStatus"],
                "riskProfile": {
                    "level": risk_data["riskLevel"],
                    "score": risk_data["riskScore"]
                },
                "lastUpdated": max(customer_data["lastUpdated"], risk_data["lastUpdated"])
            }
            
        except ServiceUnavailableError:
            # Fallback to cached or basic data
            return await self._get_fallback_profile(customer_id)

# Implementation 3: Hybrid customer service (cache + database + external APIs)
class HybridCustomerService(CustomerServiceInterface):
    """Customer service with multiple data sources and caching"""
    
    def __init__(self, database, redis_cache, external_api_client):
        self._db = database
        self._cache = redis_cache
        self._external_api = external_api_client
    
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Complex implementation hidden behind simple interface"""
        
        # 1. Try Redis cache first
        cached_profile = self._cache.get(f"customer:{customer_id}")
        if cached_profile:
            return json.loads(cached_profile)
        
        # 2. Get base data from database
        base_profile = self._get_base_profile_from_db(customer_id)
        
        # 3. Enrich with external data sources
        enriched_profile = self._enrich_profile(base_profile)
        
        # 4. Cache the result
        self._cache.setex(
            f"customer:{customer_id}",
            300,  # 5 minute expiry
            json.dumps(enriched_profile)
        )
        
        return enriched_profile
    
    def _enrich_profile(self, base_profile: Dict) -> Dict:
        """Enrich profile with external data sources"""
        enriched = base_profile.copy()
        
        try:
            # Get credit score from external service
            credit_data = self._external_api.get_credit_score(base_profile['customerId'])
            enriched['creditScore'] = credit_data['score']
            enriched['creditHistory'] = credit_data['history']
        except ExternalServiceError:
            # Continue without credit data
            enriched['creditScore'] = None
        
        try:
            # Get fraud indicators from external service
            fraud_data = self._external_api.check_fraud_indicators(base_profile['customerId'])
            enriched['fraudIndicators'] = fraud_data['indicators']
            enriched['fraudRiskLevel'] = fraud_data['riskLevel']
        except ExternalServiceError:
            # Continue without fraud data
            enriched['fraudIndicators'] = []
        
        return enriched

# Service consumer doesn't need to know implementation details
class PaymentProcessingService:
    """Service that uses customer service without knowing implementation"""
    
    def __init__(self, customer_service: CustomerServiceInterface):
        self.customer_service = customer_service  # Works with any implementation
    
    def process_payment(self, payment_request: Dict) -> Dict:
        """Process payment using customer service abstraction"""
        
        # Get customer profile (implementation details abstracted)
        customer = self.customer_service.get_customer_profile(
            payment_request['customerId']
        )
        
        # Use customer data for payment processing
        if customer['kycStatus'] != 'VERIFIED':
            return {"success": False, "error": "Customer KYC not verified"}
        
        if customer['riskProfile']['level'] == 'HIGH':
            return {"success": False, "error": "Customer risk level too high"}
        
        # Process payment...
        return {"success": True, "transactionId": str(uuid.uuid4())}

# Service configuration can switch implementations without changing consumers
def create_customer_service(config: Dict) -> CustomerServiceInterface:
    """Factory method that returns appropriate implementation"""
    
    if config['customer_service_type'] == 'database':
        return DatabaseCustomerService(config['database'])
    elif config['customer_service_type'] == 'microservice':
        return MicroserviceCustomerService(
            config['service_discovery'],
            config['circuit_breaker']
        )
    elif config['customer_service_type'] == 'hybrid':
        return HybridCustomerService(
            config['database'],
            config['redis_cache'],
            config['external_api_client']
        )
    else:
        raise ValueError(f"Unknown customer service type: {config['customer_service_type']}")
```

**Benefits of Service Abstraction:**
1. **Implementation Independence:** Consumers don't depend on specific implementations
2. **Technology Flexibility:** Can switch from database to microservices without changing consumers
3. **Testing Simplification:** Easy to mock services for testing
4. **Evolution Support:** Services can evolve internally without breaking consumers
5. **Deployment Options:** Different environments can use different implementations

#### Service Composability
**Definition:** Services can be combined and recombined to create new business functionality.

**Example - Loan Application Workflow Composition:**
```python
class LoanApplicationWorkflow:
    """Composite service that orchestrates multiple services for loan processing"""
    
    def __init__(self, 
                 customer_service: CustomerServiceInterface,
                 credit_service: CreditServiceInterface,
                 risk_service: RiskServiceInterface,
                 document_service: DocumentServiceInterface,
                 notification_service: NotificationServiceInterface,
                 approval_service: ApprovalServiceInterface):
        
        # Composed of multiple specialized services
        self.customer_service = customer_service
        self.credit_service = credit_service
        self.risk_service = risk_service
        self.document_service = document_service
        self.notification_service = notification_service
        self.approval_service = approval_service
    
    def process_loan_application(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Compose multiple services to process loan application"""
        
        workflow_id = str(uuid.uuid4())
        
        try:
            # Step 1: Validate customer (composing customer service)
            customer_validation = self._validate_customer(application['customerId'])
            if not customer_validation['valid']:
                return self._create_rejection_response(
                    workflow_id, 
                    "CUSTOMER_VALIDATION_FAILED", 
                    customer_validation['reasons']
                )
            
            # Step 2: Check credit score (composing credit service)
            credit_check = self._perform_credit_check(application['customerId'], application['loanAmount'])
            if not credit_check['approved']:
                return self._create_rejection_response(
                    workflow_id,
                    "CREDIT_CHECK_FAILED",
                    credit_check['reasons']
                )
            
            # Step 3: Assess risk (composing risk service)
            risk_assessment = self._assess_loan_risk(application, customer_validation['profile'], credit_check)
            if risk_assessment['riskLevel'] == 'HIGH':
                return self._create_rejection_response(
                    workflow_id,
                    "HIGH_RISK_ASSESSMENT",
                    risk_assessment['riskFactors']
                )
            
            # Step 4: Verify documents (composing document service)
            document_verification = self._verify_documents(application['documents'])
            if not document_verification['allVerified']:
                return self._create_conditional_approval(
                    workflow_id,
                    application,
                    "PENDING_DOCUMENT_VERIFICATION",
                    document_verification['missingDocuments']
                )
            
            # Step 5: Determine approval level needed (composing approval service)
            approval_requirement = self._determine_approval_requirement(
                application['loanAmount'],
                risk_assessment['riskLevel'],
                credit_check['creditScore']
            )
            
            # Step 6: Process approval (composing approval service)
            approval_result = self._process_approval(application, approval_requirement)
            
            # Step 7: Send notifications (composing notification service)
            self._send_notifications(application['customerId'], approval_result)
            
            return self._create_approval_response(workflow_id, approval_result)
            
        except Exception as e:
            # Handle workflow errors
            self.notification_service.send_error_notification(
                application['customerId'],
                f"Loan application processing failed: {str(e)}"
            )
            return self._create_error_response(workflow_id, str(e))
    
    def _validate_customer(self, customer_id: str) -> Dict[str, Any]:
        """Compose customer service for validation"""
        try:
            customer_profile = self.customer_service.get_customer_profile(customer_id)
            
            validation_result = {
                'valid': True,
                'profile': customer_profile,
                'reasons': []
            }
            
            # Validation logic
            if customer_profile['kycStatus'] != 'VERIFIED':
                validation_result['valid'] = False
                validation_result['reasons'].append('KYC not verified')
            
            if not customer_profile.get('email') or not customer_profile.get('phone'):
                validation_result['valid'] = False
                validation_result['reasons'].append('Incomplete contact information')
            
            # Check if customer has any blocked accounts
            if customer_profile.get('accountStatus') == 'BLOCKED':
                validation_result['valid'] = False
                validation_result['reasons'].append('Customer account blocked')
            
            return validation_result
            
        except CustomerNotFoundError:
            return {
                'valid': False,
                'profile': None,
                'reasons': ['Customer not found']
            }
    
    def _perform_credit_check(self, customer_id: str, loan_amount: float) -> Dict[str, Any]:
        """Compose credit service for credit evaluation"""
        try:
            # Get credit score
            credit_score = self.credit_service.get_credit_score(customer_id)
            
            # Get credit history
            credit_history = self.credit_service.get_credit_history(customer_id)
            
            # Determine approval based on credit criteria
            approval_criteria = self._get_credit_approval_criteria(loan_amount)
            
            approved = (
                credit_score['score'] >= approval_criteria['minimum_score'] and
                credit_history['delinquencies'] <= approval_criteria['max_delinquencies'] and
                credit_history['debt_to_income_ratio'] <= approval_criteria['max_debt_ratio']
            )
            
            return {
                'approved': approved,
                'creditScore': credit_score['score'],
                'creditHistory': credit_history,
                'reasons': [] if approved else self._generate_credit_rejection_reasons(
                    credit_score, credit_history, approval_criteria
                )
            }
            
        except CreditServiceError as e:
            return {
                'approved': False,
                'creditScore': None,
                'creditHistory': None,
                'reasons': [f'Credit check failed: {str(e)}']
            }
    
    def _assess_loan_risk(self, application: Dict, customer_profile: Dict, credit_check: Dict) -> Dict[str, Any]:
        """Compose risk service for comprehensive risk assessment"""
        
        risk_factors = {
            'loanAmount': application['loanAmount'],
            'loanPurpose': application['purpose'],
            'customerAge': customer_profile.get('age'),
            'employmentStatus': application.get('employmentStatus'),
            'annualIncome': application.get('annualIncome'),
            'creditScore': credit_check.get('creditScore'),
            'existingDebts': credit_check.get('creditHistory', {}).get('total_debt', 0),
            'collateral': application.get('collateral')
        }
        
        return self.risk_service.assess_loan_risk(risk_factors)
    
    def _verify_documents(self, documents: List[Dict]) -> Dict[str, Any]:
        """Compose document service for document verification"""
        
        required_documents = ['IDENTITY_PROOF', 'INCOME_PROOF', 'ADDRESS_PROOF']
        verification_results = []
        
        for doc_type in required_documents:
            document = next((d for d in documents if d['type'] == doc_type), None)
            
            if document:
                verification = self.document_service.verify_document(document)
                verification_results.append({
                    'type': doc_type,
                    'verified': verification['verified'],
                    'confidence': verification['confidence'],
                    'issues': verification.get('issues', [])
                })
            else:
                verification_results.append({
                    'type': doc_type,
                    'verified': False,
                    'confidence': 0,
                    'issues': ['Document not provided']
                })
        
        all_verified = all(result['verified'] for result in verification_results)
        missing_documents = [
            result['type'] for result in verification_results 
            if not result['verified']
        ]
        
        return {
            'allVerified': all_verified,
            'verificationResults': verification_results,
            'missingDocuments': missing_documents
        }
    
    def _determine_approval_requirement(self, loan_amount: float, risk_level: str, credit_score: int) -> Dict[str, Any]:
        """Compose approval service to determine required approval level"""
        
        approval_criteria = {
            'amount': loan_amount,
            'riskLevel': risk_level,
            'creditScore': credit_score
        }
        
        return self.approval_service.determine_approval_requirement(approval_criteria)
    
    def _process_approval(self, application: Dict, approval_requirement: Dict) -> Dict[str, Any]:
        """Compose approval service for processing approval workflow"""
        
        if approval_requirement['autoApprovalEligible']:
            # Automatic approval
            return self.approval_service.auto_approve_loan(application)
        else:
            # Manual approval required
            return self.approval_service.submit_for_manual_approval(
                application, 
                approval_requirement['requiredApprovalLevel']
            )
    
    def _send_notifications(self, customer_id: str, approval_result: Dict):
        """Compose notification service for customer communication"""
        
        if approval_result['status'] == 'APPROVED':
            self.notification_service.send_loan_approval_notification(
                customer_id, 
                approval_result
            )
        elif approval_result['status'] == 'PENDING':
            self.notification_service.send_loan_pending_notification(
                customer_id,
                approval_result
            )
        else:
            self.notification_service.send_loan_rejection_notification(
                customer_id,
                approval_result
            )

# Different workflow compositions for different loan types
class MortgageLoanWorkflow(LoanApplicationWorkflow):
    """Specialized composition for mortgage loans"""
    
    def __init__(self, *args, property_valuation_service, insurance_service, **kwargs):
        super().__init__(*args, **kwargs)
        self.property_valuation_service = property_valuation_service
        self.insurance_service = insurance_service
    
    def process_loan_application(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Extended composition for mortgage-specific requirements"""
        
        # First run the standard loan workflow
        standard_result = super().process_loan_application(application)
        
        if standard_result['status'] in ['APPROVED', 'CONDITIONALLY_APPROVED']:
            # Additional mortgage-specific steps
            
            # Property valuation
            valuation_result = self.property_valuation_service.evaluate_property(
                application['propertyDetails']
            )
            
            if valuation_result['value'] < application['loanAmount'] * 0.8:  # 80% LTV max
                return self._create_rejection_response(
                    standard_result['workflowId'],
                    "INSUFFICIENT_COLLATERAL_VALUE",
                    [f"Property value ${valuation_result['value']} insufficient for loan amount"]
                )
            
            # Insurance verification
            insurance_check = self.insurance_service.verify_property_insurance(
                application['propertyDetails']
            )
            
            if not insurance_check['adequate']:
                return self._create_conditional_approval(
                    standard_result['workflowId'],
                    application,
                    "PENDING_INSURANCE_VERIFICATION",
                    insurance_check['requirements']
                )
        
        return standard_result

class PersonalLoanWorkflow(LoanApplicationWorkflow):
    """Simplified composition for personal loans"""
    
    def process_loan_application(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Streamlined composition for personal loans"""
        
        # Personal loans have simpler requirements
        # Skip some steps like collateral verification
        
        workflow_id = str(uuid.uuid4())
        
        # Simplified workflow composition
        customer_validation = self._validate_customer(application['customerId'])
        if not customer_validation['valid']:
            return self._create_rejection_response(workflow_id, "CUSTOMER_VALIDATION_FAILED", customer_validation['reasons'])
        
        credit_check = self._perform_credit_check(application['customerId'], application['loanAmount'])
        if not credit_check['approved']:
            return self._create_rejection_response(workflow_id, "CREDIT_CHECK_FAILED", credit_check['reasons'])
        
        # For personal loans, we might have different risk criteria
        risk_assessment = self._assess_personal_loan_risk(application, customer_validation['profile'], credit_check)
        
        if risk_assessment['riskLevel'] in ['HIGH', 'VERY_HIGH']:
            return self._create_rejection_response(workflow_id, "HIGH_RISK_ASSESSMENT", risk_assessment['riskFactors'])
        
        # Auto-approval for low-risk personal loans
        if risk_assessment['riskLevel'] == 'LOW' and application['loanAmount'] <= 10000:
            approval_result = self.approval_service.auto_approve_loan(application)
            self._send_notifications(application['customerId'], approval_result)
            return self._create_approval_response(workflow_id, approval_result)
        
        # Manual approval for higher amounts or medium risk
        approval_requirement = {'autoApprovalEligible': False, 'requiredApprovalLevel': 'MANAGER'}
        approval_result = self._process_approval(application, approval_requirement)
        self._send_notifications(application['customerId'], approval_result)
        
        return self._create_approval_response(workflow_id, approval_result)
```

This demonstrates service composability where:
- **Base Workflow:** Composes standard services for common loan processing
- **Mortgage Workflow:** Extends composition with property valuation and insurance services
- **Personal Loan Workflow:** Simplifies composition for streamlined processing
- **Flexible Composition:** Services can be recombined for different business needs
- **Service Reuse:** Same underlying services used in different compositions

This comprehensive section demonstrates the core SOA principles with production-ready examples showing how services maintain loose coupling, clear contracts, autonomy, abstraction, and composability in real enterprise scenarios.