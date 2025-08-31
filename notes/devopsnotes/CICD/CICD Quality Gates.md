# CICD Quality Gates

Enterprise quality assurance patterns, automated gates, and quality metrics for ensuring software delivery excellence.

## Table of Contents
1. [Quality Gate Architecture](#quality-gate-architecture)
2. [Code Quality Gates](#code-quality-gates)
3. [Security Quality Gates](#security-quality-gates)
4. [Performance Quality Gates](#performance-quality-gates)
5. [Business Quality Gates](#business-quality-gates)
6. [Dynamic Gate Configuration](#dynamic-gate-configuration)
7. [Quality Metrics & Reporting](#quality-metrics--reporting)
8. [Gate Override & Exception Handling](#gate-override--exception-handling)

## Quality Gate Architecture

### Multi-Stage Quality Framework
```yaml
quality_gates:
  commit_stage:
    gates:
      - name: "code_standards"
        type: "automated"
        blocking: true
        criteria:
          - linting_pass: true
          - code_formatting: true
          - naming_conventions: true
      
      - name: "unit_tests"
        type: "automated"
        blocking: true
        criteria:
          - test_coverage: ">= 80%"
          - test_success_rate: "100%"
          - test_duration: "<= 5 minutes"
      
      - name: "static_analysis"
        type: "automated"
        blocking: true
        criteria:
          - code_smells: "<= 5"
          - duplicated_lines: "<= 3%"
          - maintainability_rating: ">= B"
          - reliability_rating: ">= B"

  integration_stage:
    gates:
      - name: "integration_tests"
        type: "automated"
        blocking: true
        criteria:
          - api_tests_pass: true
          - database_tests_pass: true
          - service_integration_pass: true
      
      - name: "security_scan"
        type: "automated"
        blocking: true
        criteria:
          - vulnerability_count_critical: "0"
          - vulnerability_count_high: "<= 2"
          - secret_scan_pass: true
      
      - name: "performance_baseline"
        type: "automated"
        blocking: false
        criteria:
          - response_time_p95: "<= 500ms"
          - throughput_degradation: "<= 10%"
          - error_rate: "<= 0.1%"

  staging_stage:
    gates:
      - name: "end_to_end_tests"
        type: "automated"
        blocking: true
        criteria:
          - e2e_success_rate: "100%"
          - browser_compatibility: true
          - mobile_compatibility: true
      
      - name: "load_testing"
        type: "automated"
        blocking: true
        criteria:
          - concurrent_users: ">= 1000"
          - response_time_under_load: "<= 1000ms"
          - system_stability: "99.9%"
      
      - name: "manual_approval"
        type: "manual"
        blocking: true
        criteria:
          - product_owner_approval: true
          - qa_sign_off: true
          - business_validation: true

  production_stage:
    gates:
      - name: "deployment_readiness"
        type: "automated"
        blocking: true
        criteria:
          - infrastructure_health: true
          - capacity_available: true
          - rollback_plan_ready: true
      
      - name: "compliance_check"
        type: "automated"
        blocking: true
        criteria:
          - regulatory_compliance: true
          - data_privacy_compliance: true
          - audit_trail_complete: true
```

### Dynamic Quality Gate Engine
```python
#!/usr/bin/env python3
# quality_gate_engine.py

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class GateStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"
    SKIPPED = "skipped"

class GateType(Enum):
    AUTOMATED = "automated"
    MANUAL = "manual"
    CONDITIONAL = "conditional"

@dataclass
class QualityGate:
    name: str
    type: GateType
    blocking: bool
    criteria: Dict[str, Any]
    timeout: Optional[int] = None
    retry_count: int = 0
    dependencies: List[str] = None

@dataclass
class GateResult:
    gate_name: str
    status: GateStatus
    score: float
    details: Dict[str, Any]
    execution_time: float
    timestamp: str

class QualityGateEngine:
    def __init__(self, config_path: str):
        self.logger = logging.getLogger(__name__)
        self.gates = self._load_gates_config(config_path)
        self.results = {}
        
    def _load_gates_config(self, config_path: str) -> Dict[str, QualityGate]:
        """Load quality gates configuration"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        gates = {}
        for stage_name, stage_config in config.get('quality_gates', {}).items():
            for gate_config in stage_config.get('gates', []):
                gate = QualityGate(
                    name=gate_config['name'],
                    type=GateType(gate_config['type']),
                    blocking=gate_config.get('blocking', True),
                    criteria=gate_config.get('criteria', {}),
                    timeout=gate_config.get('timeout'),
                    dependencies=gate_config.get('dependencies', [])
                )
                gates[f"{stage_name}_{gate.name}"] = gate
        
        return gates
    
    def evaluate_gate(self, gate_name: str, metrics: Dict[str, Any]) -> GateResult:
        """Evaluate a specific quality gate"""
        if gate_name not in self.gates:
            raise ValueError(f"Unknown gate: {gate_name}")
        
        gate = self.gates[gate_name]
        start_time = time.time()
        
        try:
            # Check dependencies
            if gate.dependencies:
                for dep in gate.dependencies:
                    if dep not in self.results or self.results[dep].status != GateStatus.PASSED:
                        return GateResult(
                            gate_name=gate_name,
                            status=GateStatus.PENDING,
                            score=0.0,
                            details={"reason": f"Waiting for dependency: {dep}"},
                            execution_time=0.0,
                            timestamp=datetime.utcnow().isoformat()
                        )
            
            # Evaluate criteria
            evaluation_result = self._evaluate_criteria(gate.criteria, metrics)
            
            result = GateResult(
                gate_name=gate_name,
                status=evaluation_result['status'],
                score=evaluation_result['score'],
                details=evaluation_result['details'],
                execution_time=time.time() - start_time,
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.results[gate_name] = result
            return result
            
        except Exception as e:
            self.logger.error(f"Error evaluating gate {gate_name}: {str(e)}")
            return GateResult(
                gate_name=gate_name,
                status=GateStatus.FAILED,
                score=0.0,
                details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def _evaluate_criteria(self, criteria: Dict[str, Any], metrics: Dict[str, Any]) -> Dict:
        """Evaluate gate criteria against metrics"""
        passed_criteria = 0
        total_criteria = len(criteria)
        details = {}
        
        for criterion, expected_value in criteria.items():
            if criterion not in metrics:
                details[criterion] = {
                    "status": "missing",
                    "expected": expected_value,
                    "actual": None
                }
                continue
            
            actual_value = metrics[criterion]
            criterion_passed = self._evaluate_criterion(criterion, expected_value, actual_value)
            
            if criterion_passed:
                passed_criteria += 1
            
            details[criterion] = {
                "status": "passed" if criterion_passed else "failed",
                "expected": expected_value,
                "actual": actual_value
            }
        
        score = passed_criteria / total_criteria if total_criteria > 0 else 1.0
        status = GateStatus.PASSED if score == 1.0 else GateStatus.FAILED
        
        return {
            "status": status,
            "score": score,
            "details": details
        }
    
    def _evaluate_criterion(self, name: str, expected: Any, actual: Any) -> bool:
        """Evaluate a single criterion"""
        try:
            if isinstance(expected, str):
                if expected.startswith('>='):
                    threshold = float(expected[2:].strip().rstrip('%'))
                    actual_val = float(str(actual).rstrip('%'))
                    return actual_val >= threshold
                elif expected.startswith('<='):
                    threshold = float(expected[2:].strip().rstrip('%'))
                    actual_val = float(str(actual).rstrip('%'))
                    return actual_val <= threshold
                elif expected.startswith('>'):
                    threshold = float(expected[1:].strip().rstrip('%'))
                    actual_val = float(str(actual).rstrip('%'))
                    return actual_val > threshold
                elif expected.startswith('<'):
                    threshold = float(expected[1:].strip().rstrip('%'))
                    actual_val = float(str(actual).rstrip('%'))
                    return actual_val < threshold
                else:
                    return str(actual) == expected
            
            elif isinstance(expected, bool):
                return bool(actual) == expected
            
            elif isinstance(expected, (int, float)):
                return float(actual) == float(expected)
            
            else:
                return actual == expected
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error evaluating criterion {name}: {e}")
            return False
    
    def evaluate_stage(self, stage_name: str, metrics: Dict[str, Any]) -> Dict[str, GateResult]:
        """Evaluate all gates in a stage"""
        stage_gates = {name: gate for name, gate in self.gates.items() 
                      if name.startswith(f"{stage_name}_")}
        
        results = {}
        for gate_name in stage_gates:
            result = self.evaluate_gate(gate_name, metrics)
            results[gate_name] = result
        
        return results
    
    def can_proceed(self, stage_name: str) -> bool:
        """Check if pipeline can proceed based on blocking gates"""
        stage_gates = {name: gate for name, gate in self.gates.items() 
                      if name.startswith(f"{stage_name}_")}
        
        for gate_name, gate in stage_gates.items():
            if gate.blocking and gate_name in self.results:
                if self.results[gate_name].status == GateStatus.FAILED:
                    return False
        
        return True
    
    def generate_report(self) -> Dict:
        """Generate comprehensive quality report"""
        report = {
            "summary": {
                "total_gates": len(self.gates),
                "passed": sum(1 for r in self.results.values() if r.status == GateStatus.PASSED),
                "failed": sum(1 for r in self.results.values() if r.status == GateStatus.FAILED),
                "warnings": sum(1 for r in self.results.values() if r.status == GateStatus.WARNING),
                "overall_score": sum(r.score for r in self.results.values()) / len(self.results) if self.results else 0
            },
            "stages": {},
            "blocking_failures": [],
            "recommendations": []
        }
        
        # Group results by stage
        for gate_name, result in self.results.items():
            stage_name = gate_name.split('_')[0]
            if stage_name not in report["stages"]:
                report["stages"][stage_name] = []
            
            report["stages"][stage_name].append({
                "gate": gate_name,
                "status": result.status.value,
                "score": result.score,
                "details": result.details,
                "blocking": self.gates[gate_name].blocking
            })
            
            # Track blocking failures
            if result.status == GateStatus.FAILED and self.gates[gate_name].blocking:
                report["blocking_failures"].append(gate_name)
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations()
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on results"""
        recommendations = []
        
        for gate_name, result in self.results.items():
            if result.status == GateStatus.FAILED:
                gate = self.gates[gate_name]
                
                if "test_coverage" in result.details:
                    coverage_detail = result.details["test_coverage"]
                    if coverage_detail["status"] == "failed":
                        recommendations.append(
                            f"Increase test coverage from {coverage_detail['actual']} "
                            f"to meet threshold of {coverage_detail['expected']}"
                        )
                
                if "vulnerability_count" in result.details:
                    vuln_detail = result.details["vulnerability_count"]
                    if vuln_detail["status"] == "failed":
                        recommendations.append(
                            f"Address {vuln_detail['actual']} security vulnerabilities "
                            f"to meet threshold of {vuln_detail['expected']}"
                        )
        
        return recommendations

# Quality Gate Integration with Jenkins Pipeline
def integrate_with_jenkins():
    """Example Jenkins integration"""
    jenkins_script = '''
    stage('Quality Gates') {
        steps {
            script {
                // Collect metrics from various sources
                def metrics = [
                    test_coverage: sh(script: "cat coverage/coverage-summary.json | jq '.total.lines.pct'", returnStdout: true).trim(),
                    vulnerability_count_critical: sh(script: "cat security-scan.json | jq '.vulnerabilities | map(select(.severity==\"critical\")) | length'", returnStdout: true).trim(),
                    code_smells: sh(script: "cat sonar-report.json | jq '.issues | map(select(.type==\"CODE_SMELL\")) | length'", returnStdout: true).trim(),
                    response_time_p95: sh(script: "cat performance-results.json | jq '.summary.p95'", returnStdout: true).trim()
                ]
                
                // Execute quality gate evaluation
                def result = sh(
                    script: "python quality_gate_engine.py evaluate --stage=integration --metrics='${groovy.json.JsonOutput.toJson(metrics)}'",
                    returnStdout: true
                ).trim()
                
                def gateResults = readJSON text: result
                
                // Check if pipeline can proceed
                if (!gateResults.can_proceed) {
                    error """
                    Quality gates failed:
                    Blocking failures: ${gateResults.blocking_failures.join(', ')}
                    Overall score: ${gateResults.summary.overall_score}
                    """
                }
                
                // Archive quality report
                writeFile file: 'quality-gate-report.json', text: result
                archiveArtifacts artifacts: 'quality-gate-report.json'
                
                // Publish to quality dashboard
                sh """
                curl -X POST "${QUALITY_DASHBOARD_URL}/reports" \\
                     -H "Content-Type: application/json" \\
                     -d '${result}'
                """
            }
        }
    }
    '''
    return jenkins_script

if __name__ == "__main__":
    import sys
    import time
    import datetime
    
    if len(sys.argv) < 2:
        print("Usage: python quality_gate_engine.py <command> [options]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "evaluate":
        # Parse command line arguments for metrics
        engine = QualityGateEngine("quality-gates-config.json")
        
        # Example usage
        metrics = {
            "test_coverage": "85%",
            "vulnerability_count_critical": 0,
            "code_smells": 3,
            "response_time_p95": "450ms"
        }
        
        results = engine.evaluate_stage("integration", metrics)
        report = engine.generate_report()
        
        print(json.dumps(report, indent=2))
```

This comprehensive CICD Quality Gates guide provides enterprise-ready patterns for implementing automated quality assurance, ensuring software delivery meets defined standards before progression through pipeline stages.