# CICD Testing Strategies

Advanced testing methodologies, automation frameworks, and quality assurance patterns for enterprise CICD pipelines.

## Table of Contents
1. [Testing Pyramid Architecture](#testing-pyramid-architecture)
2. [Automated Testing Frameworks](#automated-testing-frameworks)
3. [Test Environment Management](#test-environment-management)
4. [Performance & Load Testing](#performance--load-testing)
5. [Security Testing Integration](#security-testing-integration)
6. [Contract Testing & API Testing](#contract-testing--api-testing)
7. [Test Data Management](#test-data-management)
8. [Quality Gates & Metrics](#quality-gates--metrics)

## Testing Pyramid Architecture

### Comprehensive Testing Strategy
```yaml
testing_strategy:
  unit_tests:
    coverage_threshold: 85
    execution_time: "< 5 minutes"
    isolation: true
    mocking_strategy: "dependency_injection"
    frameworks:
      java: ["junit5", "mockito", "testcontainers"]
      javascript: ["jest", "mocha", "vitest"]
      python: ["pytest", "unittest", "mock"]
      golang: ["testify", "gomock", "ginkgo"]
      csharp: ["xunit", "nunit", "moq"]
  
  integration_tests:
    coverage_threshold: 70
    execution_time: "< 15 minutes"
    database_strategy: "testcontainers"
    external_services: "wiremock"
    frameworks:
      api_testing: ["rest-assured", "supertest", "requests"]
      database_testing: ["dbunit", "flyway", "liquibase"]
  
  contract_tests:
    provider_verification: true
    consumer_driven: true
    tools: ["pact", "spring-cloud-contract"]
    execution_frequency: "on_integration_branch"
  
  end_to_end_tests:
    execution_time: "< 30 minutes"
    browser_matrix: ["chrome", "firefox", "edge"]
    mobile_testing: ["android", "ios"]
    frameworks: ["selenium", "cypress", "playwright", "appium"]
  
  performance_tests:
    load_testing: true
    stress_testing: true
    volume_testing: true
    tools: ["k6", "jmeter", "gatling", "artillery"]
  
  security_tests:
    sast: ["sonarqube", "veracode", "checkmarx"]
    dast: ["owasp-zap", "burp-suite", "nessus"]
    dependency_scan: ["snyk", "whitesource", "dependency-track"]
```

### Test Execution Pipeline
```groovy
pipeline {
    agent none
    stages {
        stage('Test Pipeline') {
            parallel {
                stage('Unit Tests') {
                    agent { label 'test-runner' }
                    steps {
                        script {
                            sh 'make test-unit'
                            publishTestResults testResultsPattern: '**/target/surefire-reports/*.xml'
                            publishCoverage adapters: [jacocoAdapter('**/target/site/jacoco/jacoco.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'target/site/jacoco/**/*'
                        }
                    }
                }
                
                stage('Integration Tests') {
                    agent { label 'test-runner' }
                    environment {
                        TESTCONTAINERS_RYUK_DISABLED = 'true'
                    }
                    steps {
                        script {
                            sh 'docker-compose -f docker-compose.test.yml up -d'
                            sh 'make test-integration'
                        }
                    }
                    post {
                        always {
                            sh 'docker-compose -f docker-compose.test.yml down -v'
                        }
                    }
                }
                
                stage('Contract Tests') {
                    agent { label 'test-runner' }
                    when {
                        anyOf {
                            branch 'develop'
                            branch 'main'
                            changeRequest target: 'develop'
                        }
                    }
                    steps {
                        script {
                            sh 'make test-contracts'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'target/pact/reports',
                                reportFiles: 'index.html',
                                reportName: 'Pact Contract Tests'
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Quality Gates') {
            agent { label 'test-runner' }
            steps {
                script {
                    def qualityGate = waitForQualityGate()
                    if (qualityGate.status != 'OK') {
                        error "Pipeline aborted due to quality gate failure: ${qualityGate.status}"
                    }
                }
            }
        }
        
        stage('E2E Tests') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'main'
                }
            }
            parallel {
                stage('Web E2E') {
                    agent { label 'e2e-chrome' }
                    steps {
                        script {
                            sh 'npm run test:e2e:chrome'
                        }
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'cypress/reports',
                                reportFiles: 'index.html',
                                reportName: 'E2E Test Results'
                            ])
                            archiveArtifacts artifacts: 'cypress/videos/**/*.mp4,cypress/screenshots/**/*.png'
                        }
                    }
                }
                
                stage('Mobile E2E') {
                    agent { label 'mobile-test' }
                    steps {
                        script {
                            sh 'npm run test:mobile:android'
                        }
                    }
                }
                
                stage('Performance Tests') {
                    agent { label 'performance' }
                    steps {
                        script {
                            sh 'k6 run --out influxdb=http://influxdb:8086/k6 performance-tests.js'
                        }
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'performance-reports',
                                reportFiles: 'index.html',
                                reportName: 'Performance Test Results'
                            ])
                        }
                    }
                }
            }
        }
    }
}
```

## Real-World Testing Use Cases

### Use Case 1: Banking Platform Testing
```python
#!/usr/bin/env python3
# banking_platform_tests.py
# Comprehensive testing for financial services platform

import pytest
import requests
import time
import decimal
import uuid
from dataclasses import dataclass
from typing import List, Dict, Any
from unittest.mock import Mock, patch
from decimal import Decimal

@dataclass
class Transaction:
    id: str
    account_from: str
    account_to: str
    amount: Decimal
    currency: str
    timestamp: str
    status: str

class BankingPlatformTester:
    def __init__(self, base_url: str, compliance_level: str = "PCI-DSS"):
        self.base_url = base_url
        self.compliance_level = compliance_level
        self.test_accounts = []
        self.test_transactions = []
        
    @pytest.fixture(scope="function")
    def setup_test_accounts(self):
        """Setup isolated test accounts for each test"""
        accounts = [
            {"account_id": f"TEST_{uuid.uuid4()}", "balance": Decimal('10000.00'), "currency": "USD"},
            {"account_id": f"TEST_{uuid.uuid4()}", "balance": Decimal('5000.00'), "currency": "EUR"},
            {"account_id": f"TEST_{uuid.uuid4()}", "balance": Decimal('0.00'), "currency": "USD"}
        ]
        
        for account in accounts:
            response = requests.post(f"{self.base_url}/accounts", json=account)
            assert response.status_code == 201
            self.test_accounts.append(account)
        
        yield accounts
        
        # Cleanup test accounts
        for account in self.test_accounts:
            requests.delete(f"{self.base_url}/accounts/{account['account_id']}")
        self.test_accounts.clear()
    
    def test_money_transfer_accuracy(self, setup_test_accounts):
        """Test precise money transfer calculations"""
        accounts = setup_test_accounts
        source_account = accounts[0]
        target_account = accounts[2]
        
        # Test transfer with precise decimal arithmetic
        transfer_amount = Decimal('1234.56')
        
        transfer_request = {
            "from_account": source_account["account_id"],
            "to_account": target_account["account_id"],
            "amount": str(transfer_amount),
            "currency": "USD",
            "reference": "TEST_TRANSFER_001"
        }
        
        response = requests.post(f"{self.base_url}/transfers", json=transfer_request)
        assert response.status_code == 201
        
        # Verify source account balance
        source_balance_response = requests.get(
            f"{self.base_url}/accounts/{source_account['account_id']}/balance"
        )
        source_balance = Decimal(source_balance_response.json()["balance"])
        expected_source_balance = Decimal('10000.00') - transfer_amount
        assert source_balance == expected_source_balance
        
        # Verify target account balance
        target_balance_response = requests.get(
            f"{self.base_url}/accounts/{target_account['account_id']}/balance"
        )
        target_balance = Decimal(target_balance_response.json()["balance"])
        assert target_balance == transfer_amount
    
    def test_fraud_detection_system(self, setup_test_accounts):
        """Test fraud detection triggers"""
        accounts = setup_test_accounts
        test_account = accounts[0]
        
        # Simulate suspicious activity pattern
        suspicious_transfers = []
        for i in range(10):
            transfer = {
                "from_account": test_account["account_id"],
                "to_account": f"EXTERNAL_{i}",
                "amount": "999.99",  # Just under $1000 threshold
                "currency": "USD"
            }
            
            response = requests.post(f"{self.base_url}/transfers", json=transfer)
            suspicious_transfers.append(response)
            time.sleep(0.1)  # Rapid succession
        
        # First few transfers should succeed
        for i in range(3):
            assert suspicious_transfers[i].status_code == 201
        
        # Later transfers should be flagged/blocked
        fraud_detected = False
        for i in range(3, 10):
            if suspicious_transfers[i].status_code == 429:  # Rate limited
                fraud_detected = True
                break
        
        assert fraud_detected, "Fraud detection system should have triggered"
    
    def test_regulatory_compliance_reporting(self, setup_test_accounts):
        """Test compliance with financial regulations"""
        accounts = setup_test_accounts
        
        # Create large transaction that requires reporting
        large_transfer = {
            "from_account": accounts[0]["account_id"],
            "to_account": accounts[1]["account_id"],
            "amount": "15000.00",  # Above $10k reporting threshold
            "currency": "USD",
            "customer_info": {
                "name": "John Doe",
                "ssn": "***-**-****",  # Masked for testing
                "address": "123 Test St, Test City, TC 12345"
            }
        }
        
        response = requests.post(f"{self.base_url}/transfers", json=large_transfer)
        assert response.status_code == 202  # Accepted but pending compliance
        
        transfer_id = response.json()["transfer_id"]
        
        # Verify CTR (Currency Transaction Report) was generated
        ctr_response = requests.get(f"{self.base_url}/compliance/ctr/{transfer_id}")
        assert ctr_response.status_code == 200
        
        ctr_data = ctr_response.json()
        assert ctr_data["transaction_amount"] == "15000.00"
        assert ctr_data["reporting_threshold_exceeded"] is True
        assert "customer_due_diligence" in ctr_data
    
    def test_payment_processing_resilience(self, setup_test_accounts):
        """Test system resilience under load"""
        accounts = setup_test_accounts
        
        # Simulate high-frequency trading scenario
        concurrent_transfers = []
        
        import concurrent.futures
        import threading
        
        def execute_transfer(transfer_id):
            transfer_request = {
                "from_account": accounts[0]["account_id"],
                "to_account": accounts[1]["account_id"],
                "amount": "10.00",
                "currency": "USD",
                "idempotency_key": f"TEST_CONCURRENT_{transfer_id}"
            }
            
            return requests.post(f"{self.base_url}/transfers", json=transfer_request)
        
        # Execute 100 concurrent transfers
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(execute_transfer, i) for i in range(100)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify system handled load appropriately
        successful_transfers = sum(1 for r in results if r.status_code == 201)
        rate_limited = sum(1 for r in results if r.status_code == 429)
        
        # Should have some successful transfers and appropriate rate limiting
        assert successful_transfers > 0
        assert successful_transfers + rate_limited == 100
        
        # Verify data consistency after concurrent operations
        final_balance_response = requests.get(
            f"{self.base_url}/accounts/{accounts[0]['account_id']}/balance"
        )
        
        expected_deduction = Decimal('10.00') * successful_transfers
        actual_balance = Decimal(final_balance_response.json()["balance"])
        expected_balance = Decimal('10000.00') - expected_deduction
        
        assert actual_balance == expected_balance, "Balance inconsistency detected"
    
    def test_disaster_recovery_procedures(self, setup_test_accounts):
        """Test disaster recovery and failover"""
        accounts = setup_test_accounts
        
        # Test database failover
        # Simulate primary database failure
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.ConnectionError("Database unavailable")
            
            # System should gracefully handle the failure
            transfer_request = {
                "from_account": accounts[0]["account_id"],
                "to_account": accounts[1]["account_id"],
                "amount": "100.00",
                "currency": "USD"
            }
            
            try:
                response = requests.post(f"{self.base_url}/transfers", json=transfer_request)
                # Should return service unavailable or queue for later processing
                assert response.status_code in [503, 202]
            except requests.ConnectionError:
                # Connection error is acceptable during disaster recovery
                pass
        
        # Test backup system activation
        backup_url = self.base_url.replace("primary", "backup")
        health_response = requests.get(f"{backup_url}/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

# Performance testing with K6
performance_test_script = """
// k6_banking_performance.js
// Banking platform performance tests

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const transactionRate = new Rate('successful_transactions');

export let options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp-up
    { duration: '5m', target: 500 },   // Peak load
    { duration: '2m', target: 1000 },  // Stress test
    { duration: '1m', target: 0 },     // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],        // 95% of requests < 2s
    http_req_failed: ['rate<0.01'],           // Error rate < 1%
    errors: ['rate<0.05'],                    // Application errors < 5%
    successful_transactions: ['rate>0.95'],    // Transaction success > 95%
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://api.banking-platform.com';

export default function() {
  // Test account balance inquiry
  const accountId = `TEST_${Math.random().toString(36).substr(2, 9)}`;
  const balanceResponse = http.get(`${BASE_URL}/accounts/${accountId}/balance`);
  
  const balanceCheck = check(balanceResponse, {
    'balance inquiry status is 200': (r) => r.status === 200,
    'balance inquiry response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  errorRate.add(!balanceCheck);
  
  // Test money transfer
  const transferPayload = JSON.stringify({
    from_account: `TEST_FROM_${Math.random().toString(36).substr(2, 9)}`,
    to_account: `TEST_TO_${Math.random().toString(36).substr(2, 9)}`,
    amount: (Math.random() * 1000).toFixed(2),
    currency: 'USD',
    idempotency_key: `TEST_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  });
  
  const transferResponse = http.post(`${BASE_URL}/transfers`, transferPayload, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer test-token'
    },
  });
  
  const transferCheck = check(transferResponse, {
    'transfer status is 201 or 202': (r) => [201, 202].includes(r.status),
    'transfer response time < 1000ms': (r) => r.timings.duration < 1000,
    'transfer has transaction id': (r) => r.json('transaction_id') !== undefined,
  });
  
  transactionRate.add(transferCheck);
  errorRate.add(!transferCheck);
  
  // Test transaction history
  const historyResponse = http.get(`${BASE_URL}/accounts/${accountId}/transactions?limit=10`);
  
  check(historyResponse, {
    'history status is 200': (r) => r.status === 200,
    'history response time < 300ms': (r) => r.timings.duration < 300,
  });
  
  sleep(1); // Think time between requests
}

export function handleSummary(data) {
  return {
    'performance-summary.html': htmlReport(data),
    'performance-results.json': JSON.stringify(data),
  };
}

function htmlReport(data) {
  return `
  <!DOCTYPE html>
  <html>
  <head>
    <title>Banking Platform Performance Test Results</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 20px; }
      .metric { margin: 10px 0; padding: 10px; border: 1px solid #ccc; }
      .pass { background-color: #d4edda; }
      .fail { background-color: #f8d7da; }
    </style>
  </head>
  <body>
    <h1>Performance Test Results</h1>
    <div class="metric ${data.metrics.http_req_duration.values.p95 < 2000 ? 'pass' : 'fail'}">
      <h3>Response Time (95th percentile)</h3>
      <p>${data.metrics.http_req_duration.values.p95.toFixed(2)}ms (Target: < 2000ms)</p>
    </div>
    <div class="metric ${data.metrics.http_req_failed.values.rate < 0.01 ? 'pass' : 'fail'}">
      <h3>Error Rate</h3>
      <p>${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}% (Target: < 1%)</p>
    </div>
    <div class="metric">
      <h3>Total Requests</h3>
      <p>${data.metrics.http_reqs.values.count}</p>
    </div>
    <div class="metric">
      <h3>Virtual Users</h3>
      <p>Peak: ${Math.max(...Object.values(data.metrics.vus.values))}</p>
    </div>
  </body>
  </html>
  `;
}
"""

# Chaos Engineering Tests
class ChaosEngineeringTests:
    def __init__(self, system_url: str):
        self.system_url = system_url
    
    def test_network_partition_resilience(self):
        """Test system behavior during network partitions"""
        # Simulate network partition using toxiproxy
        import subprocess
        
        try:
            # Create network latency
            subprocess.run([
                "toxiproxy-cli", "toxic", "add", 
                "banking-service", "-t", "latency", 
                "-a", "latency=1000", "-a", "jitter=500"
            ])
            
            # Test system behavior under network stress
            response = requests.get(f"{self.system_url}/health", timeout=5)
            
            # System should degrade gracefully
            assert response.status_code in [200, 503]
            
        finally:
            # Remove toxic
            subprocess.run(["toxiproxy-cli", "toxic", "remove", "banking-service", "latency"])
    
    def test_database_failure_recovery(self):
        """Test recovery from database failures"""
        # Simulate database connection pool exhaustion
        import threading
        import time
        
        def create_db_load():
            # Create multiple long-running database queries
            for _ in range(100):
                try:
                    requests.post(f"{self.system_url}/stress-db", timeout=0.1)
                except requests.RequestException:
                    pass  # Expected timeouts
        
        # Start stress test
        stress_thread = threading.Thread(target=create_db_load)
        stress_thread.start()
        
        time.sleep(2)  # Let stress build up
        
        # Test normal operations during stress
        response = requests.get(f"{self.system_url}/accounts/TEST/balance")
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 503, 429]
        
        stress_thread.join(timeout=5)
    
    def test_memory_pressure_handling(self):
        """Test system behavior under memory pressure"""
        # Create memory pressure
        large_payload = "x" * (10 * 1024 * 1024)  # 10MB payload
        
        responses = []
        for i in range(10):
            try:
                response = requests.post(
                    f"{self.system_url}/stress-memory", 
                    data=large_payload, 
                    timeout=5
                )
                responses.append(response.status_code)
            except requests.RequestException:
                responses.append(0)  # Connection failed
        
        # Should handle memory pressure gracefully
        success_count = sum(1 for r in responses if r == 200)
        graceful_failure_count = sum(1 for r in responses if r in [429, 503])
        
        # At least some requests should succeed or fail gracefully
        assert success_count + graceful_failure_count >= 5

# Security Testing Suite
class SecurityTestSuite:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks"""
        malicious_inputs = [
            "'; DROP TABLE accounts; --",
            "' OR '1'='1",
            "'; UPDATE accounts SET balance=999999 WHERE account_id='TEST'; --",
            "' UNION SELECT * FROM accounts WHERE '1'='1"
        ]
        
        for malicious_input in malicious_inputs:
            response = requests.get(
                f"{self.base_url}/accounts", 
                params={"account_id": malicious_input}
            )
            
            # Should reject malicious input
            assert response.status_code in [400, 403, 422]
            assert "error" in response.json()
    
    def test_authentication_bypass_attempts(self):
        """Test protection against authentication bypass"""
        bypass_attempts = [
            {},  # No auth header
            {"Authorization": "Bearer invalid_token"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic YWRtaW46YWRtaW4="},  # admin:admin
            {"X-Forwarded-User": "admin"},  # Header injection
        ]
        
        for headers in bypass_attempts:
            response = requests.get(
                f"{self.base_url}/admin/users", 
                headers=headers
            )
            
            # Should reject unauthorized access
            assert response.status_code in [401, 403]
    
    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure in responses"""
        response = requests.get(f"{self.base_url}/accounts/TEST123")
        
        if response.status_code == 200:
            data = response.json()
            
            # Should not expose sensitive data
            sensitive_patterns = [
                r'\d{4}-\d{4}-\d{4}-\d{4}',  # Credit card
                r'\d{3}-\d{2}-\d{4}',         # SSN
                r'password',                  # Password fields
                r'secret',                    # Secrets
                r'private_key',               # Private keys
            ]
            
            import re
            response_text = str(data).lower()
            
            for pattern in sensitive_patterns:
                matches = re.findall(pattern, response_text)
                assert len(matches) == 0, f"Sensitive data exposed: {pattern}"

if __name__ == "__main__":
    # Run banking platform tests
    tester = BankingPlatformTester("https://api.banking-test.com")
    
    # Run specific test scenarios
    print("🏦 Running banking platform test suite...")
    pytest.main(["-v", "banking_platform_tests.py"])
    
    # Run chaos engineering tests
    chaos_tester = ChaosEngineeringTests("https://api.banking-test.com")
    print("🌪️ Running chaos engineering tests...")
    
    # Run security tests
    security_tester = SecurityTestSuite("https://api.banking-test.com")
    print("🔒 Running security test suite...")
```

### Use Case 2: Healthcare Platform E2E Testing
```javascript
// healthcare_e2e_tests.js
// Comprehensive E2E testing for HIPAA-compliant healthcare platform

const { test, expect } = require('@playwright/test');
const { faker } = require('@faker-js/faker');

// HIPAA-compliant test data generation
class HIPAATestDataGenerator {
  static generatePatient() {
    return {
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      dateOfBirth: faker.date.birthdate({ min: 18, max: 90, mode: 'age' }).toISOString().split('T')[0],
      ssn: 'XXX-XX-' + faker.string.numeric(4), // Masked for testing
      phone: faker.phone.number('###-###-####'),
      email: faker.internet.email(),
      address: {
        street: faker.location.streetAddress(),
        city: faker.location.city(),
        state: faker.location.stateAbbr(),
        zipCode: faker.location.zipCode()
      },
      insuranceNumber: 'TEST_' + faker.string.alphanumeric(8),
      medicalRecordNumber: 'MRN' + faker.string.numeric(6)
    };
  }
  
  static generateProvider() {
    return {
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      npi: faker.string.numeric(10), // National Provider Identifier
      specialty: faker.helpers.arrayElement([
        'Cardiology', 'Dermatology', 'Internal Medicine', 
        'Pediatrics', 'Oncology', 'Psychiatry'
      ]),
      licenseNumber: faker.string.alphanumeric(8),
      phone: faker.phone.number('###-###-####'),
      email: faker.internet.email()
    };
  }
  
  static generateAppointment(patientId, providerId) {
    return {
      patientId,
      providerId,
      appointmentType: faker.helpers.arrayElement([
        'Annual Physical', 'Follow-up', 'Consultation', 
        'Emergency', 'Telehealth', 'Lab Results Review'
      ]),
      scheduledDateTime: faker.date.future({ years: 0.25 }).toISOString(),
      duration: faker.helpers.arrayElement([15, 30, 45, 60]), // minutes
      reason: faker.lorem.sentence(),
      status: 'scheduled'
    };
  }
}

// Patient Portal E2E Tests
test.describe('Patient Portal - HIPAA Compliant', () => {
  let patient, provider, appointment;
  
  test.beforeEach(async ({ page }) => {
    // Generate test data
    patient = HIPAATestDataGenerator.generatePatient();
    provider = HIPAATestDataGenerator.generateProvider();
    
    // Setup test environment
    await page.goto('/admin/setup-test-data');
    await page.fill('[data-testid="patient-data"]', JSON.stringify(patient));
    await page.fill('[data-testid="provider-data"]', JSON.stringify(provider));
    await page.click('[data-testid="create-test-data"]');
    
    // Generate appointment
    appointment = HIPAATestDataGenerator.generateAppointment(
      patient.medicalRecordNumber, 
      provider.npi
    );
  });
  
  test('Patient Registration and HIPAA Consent', async ({ page }) => {
    await page.goto('/register');
    
    // Fill patient registration form
    await page.fill('[data-testid="first-name"]', patient.firstName);
    await page.fill('[data-testid="last-name"]', patient.lastName);
    await page.fill('[data-testid="date-of-birth"]', patient.dateOfBirth);
    await page.fill('[data-testid="phone"]', patient.phone);
    await page.fill('[data-testid="email"]', patient.email);
    
    // Address information
    await page.fill('[data-testid="street-address"]', patient.address.street);
    await page.fill('[data-testid="city"]', patient.address.city);
    await page.selectOption('[data-testid="state"]', patient.address.state);
    await page.fill('[data-testid="zip-code"]', patient.address.zipCode);
    
    // Insurance information
    await page.fill('[data-testid="insurance-number"]', patient.insuranceNumber);
    
    // HIPAA authorization - critical for compliance
    await expect(page.locator('[data-testid="hipaa-notice"]')).toBeVisible();
    await expect(page.locator('[data-testid="hipaa-notice"]')).toContainText('Notice of Privacy Practices');
    
    // Verify HIPAA consent checkboxes
    await page.check('[data-testid="hipaa-consent-treatment"]');
    await page.check('[data-testid="hipaa-consent-payment"]');
    await page.check('[data-testid="hipaa-consent-operations"]');
    
    // Optional consents
    await page.check('[data-testid="marketing-consent"]'); // Patient chooses to opt-in
    
    await page.click('[data-testid="register-patient"]');
    
    // Verify successful registration
    await expect(page.locator('[data-testid="registration-success"]')).toBeVisible();
    await expect(page.locator('[data-testid="patient-portal-link"]')).toBeVisible();
    
    // Verify HIPAA audit trail
    const auditResponse = await page.request.get('/api/audit/hipaa-consents', {
      data: { patientId: patient.medicalRecordNumber }
    });
    expect(auditResponse.status()).toBe(200);
    
    const auditData = await auditResponse.json();
    expect(auditData.consents).toContainEqual(
      expect.objectContaining({
        type: 'treatment',
        granted: true,
        timestamp: expect.any(String)
      })
    );
  });
  
  test('Secure Patient Login and MFA', async ({ page }) => {
    await page.goto('/login');
    
    // Primary authentication
    await page.fill('[data-testid="username"]', patient.email);
    await page.fill('[data-testid="password"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    // Multi-factor authentication (required for HIPAA)
    await expect(page.locator('[data-testid="mfa-challenge"]')).toBeVisible();
    
    // Simulate SMS MFA (in real test, would use test SMS service)
    const mfaCode = '123456'; // Test code
    await page.fill('[data-testid="mfa-code"]', mfaCode);
    await page.click('[data-testid="verify-mfa"]');
    
    // Verify successful authentication
    await expect(page.locator('[data-testid="patient-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="welcome-message"]')).toContainText(patient.firstName);
    
    // Verify session security
    const sessionCookie = await page.context().cookies();
    const authCookie = sessionCookie.find(c => c.name === 'auth-token');
    expect(authCookie.secure).toBe(true);
    expect(authCookie.httpOnly).toBe(true);
    expect(authCookie.sameSite).toBe('Strict');
  });
  
  test('Medical Records Access and Privacy Controls', async ({ page }) => {
    // Login as patient
    await page.goto('/login');
    await page.fill('[data-testid="username"]', patient.email);
    await page.fill('[data-testid="password"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    // Skip MFA for test speed
    await page.fill('[data-testid="mfa-code"]', '123456');
    await page.click('[data-testid="verify-mfa"]');
    
    // Navigate to medical records
    await page.click('[data-testid="medical-records-tab"]');
    
    // Verify patient can only see their own records
    await expect(page.locator('[data-testid="patient-name"]')).toContainText(`${patient.firstName} ${patient.lastName}`);
    await expect(page.locator('[data-testid="medical-record-number"]')).toContainText(patient.medicalRecordNumber);
    
    // Test medical record sections
    const recordSections = [
      'diagnoses', 'medications', 'allergies', 
      'lab-results', 'imaging', 'visit-notes'
    ];
    
    for (const section of recordSections) {
      await page.click(`[data-testid="${section}-section"]`);
      await expect(page.locator(`[data-testid="${section}-content"]`)).toBeVisible();
      
      // Verify no other patient data is visible
      const content = await page.locator(`[data-testid="${section}-content"]`).textContent();
      expect(content).not.toContain('DOE, JANE'); // Common test data that shouldn't appear
      expect(content).not.toContain('SMITH, JOHN');
    }
    
    // Test record download (with audit trail)
    await page.click('[data-testid="download-records"]');
    
    // Verify download consent dialog
    await expect(page.locator('[data-testid="download-consent-dialog"]')).toBeVisible();
    await page.check('[data-testid="download-consent-checkbox"]');
    await page.click('[data-testid="confirm-download"]');
    
    // Verify audit trail for record access
    const downloadPromise = page.waitForDownload();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/medical-records-.+\.pdf/);
    
    // Verify audit log entry
    const auditResponse = await page.request.get('/api/audit/record-access', {
      data: { patientId: patient.medicalRecordNumber }
    });
    const auditData = await auditResponse.json();
    expect(auditData.activities).toContainEqual(
      expect.objectContaining({
        action: 'record_download',
        patientId: patient.medicalRecordNumber,
        timestamp: expect.any(String)
      })
    );
  });
  
  test('Appointment Scheduling with Provider Availability', async ({ page }) => {
    // Login as patient
    await page.goto('/login');
    await page.fill('[data-testid="username"]', patient.email);
    await page.fill('[data-testid="password"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    await page.fill('[data-testid="mfa-code"]', '123456');
    await page.click('[data-testid="verify-mfa"]');
    
    // Navigate to appointment scheduling
    await page.click('[data-testid="schedule-appointment"]');
    
    // Search for providers
    await page.fill('[data-testid="provider-search"]', provider.specialty);
    await page.click('[data-testid="search-providers"]');
    
    // Select provider
    await page.click(`[data-testid="select-provider-${provider.npi}"]`);
    
    // View provider availability
    await expect(page.locator('[data-testid="provider-calendar"]')).toBeVisible();
    
    // Select available time slot
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];
    
    await page.click(`[data-testid="calendar-date-${tomorrowStr}"]`);
    await page.click('[data-testid="time-slot-10-00"]');
    
    // Fill appointment details
    await page.selectOption('[data-testid="appointment-type"]', 'Follow-up');
    await page.fill('[data-testid="reason-for-visit"]', 'Annual check-up and medication review');
    
    // Special instructions
    await page.fill('[data-testid="special-instructions"]', 'Patient prefers morning appointments');
    
    // Confirm appointment
    await page.click('[data-testid="confirm-appointment"]');
    
    // Verify appointment confirmation
    await expect(page.locator('[data-testid="appointment-confirmation"]')).toBeVisible();
    await expect(page.locator('[data-testid="confirmation-number"]')).toBeVisible();
    
    // Verify appointment in patient's schedule
    await page.click('[data-testid="my-appointments"]');
    await expect(page.locator('[data-testid="upcoming-appointments"]')).toContainText(provider.lastName);
    await expect(page.locator('[data-testid="upcoming-appointments"]')).toContainText('Follow-up');
    
    // Test appointment modification
    await page.click('[data-testid="modify-appointment"]');
    await page.click('[data-testid="time-slot-14-00"]'); // Change to 2:00 PM
    await page.click('[data-testid="confirm-modification"]');
    
    // Verify modification confirmation
    await expect(page.locator('[data-testid="modification-success"]')).toBeVisible();
  });
  
  test('Telehealth Video Consultation', async ({ page }) => {
    // Setup appointment for telehealth
    await page.goto('/admin/create-telehealth-appointment');
    await page.fill('[data-testid="patient-id"]', patient.medicalRecordNumber);
    await page.fill('[data-testid="provider-id"]', provider.npi);
    await page.click('[data-testid="create-appointment"]');
    
    // Patient joins telehealth session
    await page.goto('/login');
    await page.fill('[data-testid="username"]', patient.email);
    await page.fill('[data-testid="password"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    await page.fill('[data-testid="mfa-code"]', '123456');
    await page.click('[data-testid="verify-mfa"]');
    
    // Navigate to telehealth
    await page.click('[data-testid="telehealth-tab"]');
    await expect(page.locator('[data-testid="upcoming-telehealth"]')).toBeVisible();
    
    // Join video call
    await page.click('[data-testid="join-telehealth-call"]');
    
    // Verify video call interface
    await expect(page.locator('[data-testid="video-container"]')).toBeVisible();
    await expect(page.locator('[data-testid="local-video"]')).toBeVisible();
    await expect(page.locator('[data-testid="remote-video"]')).toBeVisible();
    
    // Test video controls
    await page.click('[data-testid="mute-microphone"]');
    await expect(page.locator('[data-testid="microphone-muted"]')).toBeVisible();
    
    await page.click('[data-testid="disable-camera"]');
    await expect(page.locator('[data-testid="camera-disabled"]')).toBeVisible();
    
    // Test screen sharing
    await page.click('[data-testid="share-screen"]');
    await expect(page.locator('[data-testid="screen-sharing-active"]')).toBeVisible();
    
    // Test chat functionality
    await page.click('[data-testid="open-chat"]');
    await page.fill('[data-testid="chat-input"]', 'Can you hear me clearly?');
    await page.click('[data-testid="send-message"]');
    await expect(page.locator('[data-testid="chat-messages"]')).toContainText('Can you hear me clearly?');
    
    // End call
    await page.click('[data-testid="end-call"]');
    await expect(page.locator('[data-testid="call-ended-message"]')).toBeVisible();
    
    // Verify call was recorded in audit log
    const auditResponse = await page.request.get('/api/audit/telehealth-sessions', {
      data: { patientId: patient.medicalRecordNumber }
    });
    const auditData = await auditResponse.json();
    expect(auditData.sessions).toContainEqual(
      expect.objectContaining({
        type: 'telehealth_video_call',
        duration: expect.any(Number),
        participants: expect.arrayContaining([patient.medicalRecordNumber, provider.npi])
      })
    );
  });
  
  test('HIPAA Breach Detection and Response', async ({ page }) => {
    // Simulate potential HIPAA breach scenarios
    await page.goto('/admin/security-testing');
    
    // Test 1: Unauthorized access attempt
    await page.goto('/api/patients/' + patient.medicalRecordNumber);
    // Should be redirected to login
    await expect(page.url()).toContain('/login');
    
    // Test 2: Multiple failed login attempts (should trigger security alert)
    await page.goto('/login');
    
    for (let i = 0; i < 5; i++) {
      await page.fill('[data-testid="username"]', patient.email);
      await page.fill('[data-testid="password"]', 'WrongPassword');
      await page.click('[data-testid="login-button"]');
      await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
    }
    
    // Account should be locked
    await page.fill('[data-testid="username"]', patient.email);
    await page.fill('[data-testid="password"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="account-locked"]')).toBeVisible();
    
    // Verify security incident was logged
    const incidentResponse = await page.request.get('/api/security/incidents', {
      headers: { 'Authorization': 'Bearer admin-token' }
    });
    const incidents = await incidentResponse.json();
    expect(incidents.data).toContainEqual(
      expect.objectContaining({
        type: 'multiple_failed_logins',
        severity: 'medium',
        patientId: patient.medicalRecordNumber
      })
    );
    
    // Test 3: Unusual data access pattern
    // (Would require admin login to simulate)
    const adminResponse = await page.request.post('/api/admin/simulate-breach', {
      data: {
        type: 'bulk_record_access',
        patientCount: 100,
        accessTime: new Date().toISOString()
      },
      headers: { 'Authorization': 'Bearer admin-token' }
    });
    
    expect(adminResponse.status()).toBe(200);
    
    // Verify breach detection alert
    const alertResponse = await page.request.get('/api/security/alerts');
    const alerts = await alertResponse.json();
    expect(alerts.data).toContainEqual(
      expect.objectContaining({
        type: 'potential_hipaa_breach',
        severity: 'high',
        description: expect.stringContaining('bulk_record_access')
      })
    );
  });
  
  test.afterEach(async ({ page }) => {
    // Cleanup test data
    await page.request.delete('/api/admin/test-data', {
      data: { patientId: patient.medicalRecordNumber }
    });
  });
});

// Provider Portal Tests
test.describe('Provider Portal - Clinical Workflow', () => {
  test('Clinical Documentation and ICD-10 Coding', async ({ page }) => {
    // Test clinical note creation with proper medical coding
    const visit = {
      patientId: patient.medicalRecordNumber,
      providerId: provider.npi,
      visitDate: new Date().toISOString(),
      chiefComplaint: 'Annual physical examination',
      vitalSigns: {
        temperature: '98.6°F',
        bloodPressure: '120/80 mmHg',
        heartRate: '72 bpm',
        respiratoryRate: '16/min',
        oxygenSaturation: '98%',
        weight: '150 lbs',
        height: '5\'6\"',
        bmi: 24.2
      }
    };
    
    await page.goto('/provider/login');
    await page.fill('[data-testid="provider-username"]', provider.email);
    await page.fill('[data-testid="provider-password"]', 'ProviderPassword123!');
    await page.click('[data-testid="provider-login"]');
    
    // Create clinical note
    await page.click('[data-testid="new-visit-note"]');
    await page.selectOption('[data-testid="patient-select"]', patient.medicalRecordNumber);
    
    // Document vital signs
    await page.fill('[data-testid="temperature"]', visit.vitalSigns.temperature);
    await page.fill('[data-testid="blood-pressure"]', visit.vitalSigns.bloodPressure);
    await page.fill('[data-testid="heart-rate"]', visit.vitalSigns.heartRate);
    
    // Clinical assessment
    await page.fill('[data-testid="assessment"]', 'Patient appears healthy, annual physical exam normal');
    
    // ICD-10 diagnosis coding
    await page.fill('[data-testid="diagnosis-search"]', 'routine health examination');
    await page.click('[data-testid="search-icd10"]');
    await page.click('[data-testid="select-icd10-Z00.00"]'); // Encounter for general adult medical examination without abnormal findings
    
    // Save clinical note
    await page.click('[data-testid="save-clinical-note"]');
    await expect(page.locator('[data-testid="note-saved-confirmation"]')).toBeVisible();
    
    // Verify note in patient record
    await page.click(`[data-testid="patient-chart-${patient.medicalRecordNumber}"]`);
    await expect(page.locator('[data-testid="recent-visits"]')).toContainText('Z00.00');
    await expect(page.locator('[data-testid="recent-visits"]')).toContainText('routine health examination');
  });
});
```

This comprehensive CICD Testing Strategies guide provides enterprise-ready patterns for implementing comprehensive testing across all levels of the testing pyramid, ensuring code quality and system reliability with real-world use cases covering banking platforms, healthcare systems, and specialized testing scenarios for highly regulated industries.