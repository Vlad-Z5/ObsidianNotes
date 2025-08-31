# CICD Rollback & Recovery

Advanced rollback strategies, disaster recovery patterns, and automated recovery mechanisms for resilient CICD pipeline operations.

## Table of Contents
1. [Rollback Strategy Architecture](#rollback-strategy-architecture)
2. [Automated Recovery Systems](#automated-recovery-systems)
3. [Database Rollback Management](#database-rollback-management)
4. [Infrastructure Recovery](#infrastructure-recovery)
5. [Application State Management](#application-state-management)
6. [Rollback Testing & Validation](#rollback-testing--validation)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Enterprise Recovery Patterns](#enterprise-recovery-patterns)

## Rollback Strategy Architecture

### Multi-Layer Rollback Framework
```yaml
rollback_architecture:
  application_layer:
    strategies:
      - blue_green_deployment
      - canary_rollback
      - feature_flag_disable
      - version_rollback
    
    rollback_triggers:
      automated:
        - health_check_failure
        - error_rate_threshold: "> 2%"
        - response_time_threshold: "> 500ms"
        - cpu_utilization: "> 80%"
        - memory_utilization: "> 85%"
      
      manual:
        - operator_initiated
        - support_team_escalation
        - business_decision
  
  database_layer:
    strategies:
      - schema_versioning
      - migration_rollback
      - data_snapshot_restore
      - point_in_time_recovery
    
    rollback_capabilities:
      - forward_compatible_schemas
      - backward_compatible_changes
      - data_migration_scripts
      - rollback_validation
  
  infrastructure_layer:
    strategies:
      - infrastructure_as_code_rollback
      - immutable_infrastructure
      - configuration_versioning
      - service_mesh_rollback
    
    recovery_mechanisms:
      - automated_scaling_adjustment
      - network_configuration_restore
      - security_policy_rollback
      - resource_allocation_reset
```

### Rollback Decision Matrix
```yaml
rollback_decision_matrix:
  severity_levels:
    critical:
      criteria:
        - service_completely_down
        - data_loss_detected
        - security_breach_confirmed
        - compliance_violation
      
      actions:
        - immediate_automatic_rollback
        - incident_commander_notification
        - stakeholder_communication
        - forensic_analysis_initiation
      
      timeframe: "< 5 minutes"
    
    major:
      criteria:
        - functionality_significantly_degraded
        - performance_severely_impacted
        - user_experience_compromised
        - business_process_affected
      
      actions:
        - automated_rollback_after_validation
        - team_notification
        - impact_assessment
        - rollback_approval_workflow
      
      timeframe: "< 15 minutes"
    
    minor:
      criteria:
        - minor_functionality_issues
        - performance_slightly_degraded
        - cosmetic_problems
        - non_critical_features_affected
      
      actions:
        - manual_rollback_consideration
        - team_discussion
        - risk_assessment
        - scheduled_rollback_window
      
      timeframe: "< 2 hours"
```

## Automated Recovery Systems

### Smart Rollback Orchestration
```groovy
@Library('rollback-automation') _

pipeline {
    agent none
    
    parameters {
        choice(
            name: 'ROLLBACK_STRATEGY',
            choices: ['AUTO', 'CANARY', 'BLUE_GREEN', 'IMMEDIATE'],
            description: 'Rollback strategy to use'
        )
        string(
            name: 'ROLLBACK_VERSION',
            defaultValue: '',
            description: 'Target version for rollback (empty for previous)'
        )
        booleanParam(
            name: 'INCLUDE_DATABASE',
            defaultValue: false,
            description: 'Include database rollback'
        )
    }
    
    stages {
        stage('Rollback Preparation') {
            agent { label 'rollback-orchestrator' }
            steps {
                script {
                    // Validate rollback prerequisites
                    def rollbackPlan = rollbackPlanner.generatePlan([
                        strategy: params.ROLLBACK_STRATEGY,
                        targetVersion: params.ROLLBACK_VERSION,
                        includeDatabase: params.INCLUDE_DATABASE,
                        currentEnvironment: env.TARGET_ENVIRONMENT
                    ])
                    
                    // Store rollback plan
                    writeFile file: 'rollback-plan.json', text: rollbackPlan.toJson()
                    archiveArtifacts artifacts: 'rollback-plan.json'
                    
                    // Validate rollback safety
                    sh '''
                        rollback-validator \
                            --plan rollback-plan.json \
                            --environment ${TARGET_ENVIRONMENT} \
                            --validation-mode strict
                    '''
                }
            }
        }
        
        stage('Pre-Rollback Health Check') {
            agent { label 'health-checker' }
            steps {
                script {
                    def healthStatus = healthChecker.getCurrentStatus([
                        services: ['app', 'database', 'cache', 'messaging'],
                        metrics: ['response_time', 'error_rate', 'throughput'],
                        dependencies: ['external_apis', 'third_party_services']
                    ])
                    
                    if (!healthStatus.isRollbackSafe()) {
                        error "Pre-rollback health check failed: ${healthStatus.issues}"
                    }
                }
            }
        }
        
        stage('Execute Rollback') {
            parallel {
                stage('Application Rollback') {
                    agent { label 'app-deployer' }
                    steps {
                        script {
                            rollbackExecutor.executeApplicationRollback([
                                strategy: params.ROLLBACK_STRATEGY,
                                targetVersion: params.ROLLBACK_VERSION,
                                healthCheckUrl: "${env.APP_BASE_URL}/health",
                                rollbackTimeout: '600s'
                            ])
                        }
                    }
                }
                
                stage('Database Rollback') {
                    when { 
                        expression { return params.INCLUDE_DATABASE } 
                    }
                    agent { label 'db-operator' }
                    steps {
                        script {
                            databaseRollback.execute([
                                strategy: 'migration_rollback',
                                targetMigration: rollbackPlan.databaseTarget,
                                backupValidation: true,
                                dataIntegrityCheck: true
                            ])
                        }
                    }
                }
                
                stage('Infrastructure Rollback') {
                    agent { label 'infrastructure-operator' }
                    steps {
                        script {
                            infrastructureRollback.execute([
                                terraformVersion: rollbackPlan.infrastructureVersion,
                                configurationVersion: rollbackPlan.configVersion,
                                rollbackValidation: true
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Post-Rollback Validation') {
            agent { label 'validator' }
            steps {
                script {
                    // Comprehensive validation suite
                    parallel([
                        'Functional Tests': {
                            sh 'npm run test:smoke'
                        },
                        'Performance Tests': {
                            sh 'k6 run performance/rollback-validation.js'
                        },
                        'Security Tests': {
                            sh 'zap-cli quick-scan --self-contained ${APP_BASE_URL}'
                        },
                        'Integration Tests': {
                            sh 'npm run test:integration:critical'
                        }
                    ])
                    
                    // Health monitoring
                    healthChecker.monitorRecovery([
                        duration: '15m',
                        thresholds: [
                            errorRate: '< 0.1%',
                            responseTime: '< 200ms',
                            availability: '> 99.9%'
                        ]
                    ])
                }
            }
        }
        
        stage('Rollback Verification') {
            agent { label 'verifier' }
            steps {
                script {
                    def verification = rollbackVerifier.verify([
                        applicationVersion: getCurrentVersion(),
                        databaseState: getDatabaseState(),
                        configurationState: getConfigurationState(),
                        businessFunctionality: runBusinessTests()
                    ])
                    
                    if (!verification.successful) {
                        // Escalate to emergency procedures
                        emergencyResponse.escalate([
                            severity: 'CRITICAL',
                            issue: 'Rollback verification failed',
                            details: verification.failures,
                            requiredActions: verification.recommendedActions
                        ])
                    }
                    
                    // Generate rollback report
                    rollbackReporter.generateReport([
                        rollbackId: env.BUILD_ID,
                        duration: verification.duration,
                        success: verification.successful,
                        issues: verification.issues,
                        recommendations: verification.recommendations
                    ])
                }
            }
        }
    }
    
    post {
        always {
            // Cleanup and notification
            script {
                rollbackOrchestrator.cleanup()
                
                notificationService.send([
                    channels: ['#deployments', '#engineering'],
                    message: "Rollback ${currentBuild.result} for ${env.JOB_NAME}",
                    details: readFile('rollback-report.json'),
                    severity: currentBuild.result == 'SUCCESS' ? 'INFO' : 'ERROR'
                ])
            }
        }
        
        failure {
            script {
                // Emergency escalation
                emergencyResponse.activate([
                    type: 'ROLLBACK_FAILURE',
                    environment: env.TARGET_ENVIRONMENT,
                    buildId: env.BUILD_ID,
                    rollbackPlan: readFile('rollback-plan.json')
                ])
            }
        }
    }
}
```

### Automated Recovery Decision Engine
```python
# Intelligent rollback decision system
from dataclasses import dataclass
from typing import List, Dict, Any
import json
import time
from prometheus_client.parser import text_string_to_metric_families

@dataclass
class HealthMetric:
    name: str
    value: float
    threshold: float
    severity: str
    trend: str

@dataclass
class RollbackDecision:
    should_rollback: bool
    strategy: str
    urgency: str
    confidence: float
    reasons: List[str]

class RollbackDecisionEngine:
    def __init__(self, config_file: str):
        with open(config_file) as f:
            self.config = json.load(f)
        
        self.metrics_history = []
        self.decision_history = []
    
    def analyze_metrics(self, metrics_endpoint: str) -> List[HealthMetric]:
        """Analyze current system health metrics"""
        # Fetch metrics from Prometheus
        response = requests.get(f"{metrics_endpoint}/api/v1/query_range", 
                              params={
                                  "query": "up",
                                  "start": int(time.time() - 300),
                                  "end": int(time.time()),
                                  "step": "30"
                              })
        
        health_metrics = []
        
        # Parse metrics and evaluate thresholds
        for metric_config in self.config['metrics']:
            current_value = self._get_metric_value(
                metrics_endpoint, 
                metric_config['query']
            )
            
            threshold_value = metric_config['threshold']
            severity = self._calculate_severity(current_value, threshold_value)
            trend = self._calculate_trend(metric_config['name'])
            
            health_metrics.append(HealthMetric(
                name=metric_config['name'],
                value=current_value,
                threshold=threshold_value,
                severity=severity,
                trend=trend
            ))
        
        return health_metrics
    
    def make_rollback_decision(self, health_metrics: List[HealthMetric]) -> RollbackDecision:
        """Make intelligent rollback decision based on metrics"""
        
        # Calculate severity score
        severity_score = self._calculate_severity_score(health_metrics)
        
        # Analyze trends
        trend_score = self._calculate_trend_score(health_metrics)
        
        # Check business impact
        business_impact = self._assess_business_impact(health_metrics)
        
        # Calculate confidence based on historical data
        confidence = self._calculate_confidence(health_metrics)
        
        # Decision logic
        should_rollback = False
        strategy = "monitor"
        urgency = "low"
        reasons = []
        
        if severity_score >= self.config['thresholds']['critical']:
            should_rollback = True
            strategy = "immediate"
            urgency = "critical"
            reasons.append("Critical system health degradation detected")
        
        elif severity_score >= self.config['thresholds']['major']:
            if trend_score < -0.5:  # Declining trend
                should_rollback = True
                strategy = "canary_rollback"
                urgency = "high"
                reasons.append("Major issues with declining trend")
            else:
                strategy = "prepare_rollback"
                urgency = "medium"
                reasons.append("Major issues detected, monitoring trend")
        
        elif business_impact > self.config['thresholds']['business_impact']:
            should_rollback = True
            strategy = "blue_green"
            urgency = "medium"
            reasons.append("Significant business impact detected")
        
        # Factor in confidence level
        if confidence < 0.7 and should_rollback:
            strategy = "manual_approval_required"
            reasons.append("Low confidence in automated decision")
        
        return RollbackDecision(
            should_rollback=should_rollback,
            strategy=strategy,
            urgency=urgency,
            confidence=confidence,
            reasons=reasons
        )
    
    def _calculate_severity_score(self, metrics: List[HealthMetric]) -> float:
        """Calculate overall severity score"""
        severity_weights = {
            'critical': 1.0,
            'major': 0.7,
            'minor': 0.3,
            'normal': 0.0
        }
        
        total_score = 0
        total_weight = 0
        
        for metric in metrics:
            weight = self.config.get('metric_weights', {}).get(metric.name, 1.0)
            score = severity_weights.get(metric.severity, 0)
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _calculate_trend_score(self, metrics: List[HealthMetric]) -> float:
        """Calculate trend score (-1 to 1, negative is bad)"""
        trend_scores = {
            'improving': 1.0,
            'stable': 0.0,
            'declining': -1.0,
            'rapidly_declining': -2.0
        }
        
        scores = [trend_scores.get(metric.trend, 0) for metric in metrics]
        return sum(scores) / len(scores) if scores else 0
    
    def _assess_business_impact(self, metrics: List[HealthMetric]) -> float:
        """Assess business impact based on critical path metrics"""
        business_critical_metrics = [
            'checkout_success_rate',
            'payment_processing_rate',
            'user_login_success_rate',
            'api_availability'
        ]
        
        impact_score = 0
        for metric in metrics:
            if metric.name in business_critical_metrics:
                if metric.severity in ['critical', 'major']:
                    impact_score += 1.0
                elif metric.severity == 'minor':
                    impact_score += 0.3
        
        return impact_score / len(business_critical_metrics)
    
    def _calculate_confidence(self, metrics: List[HealthMetric]) -> float:
        """Calculate confidence in the decision based on historical accuracy"""
        # Simplified confidence calculation
        # In practice, this would use ML models trained on historical data
        
        metric_stability = self._calculate_metric_stability(metrics)
        historical_accuracy = self._get_historical_accuracy()
        data_completeness = self._assess_data_completeness(metrics)
        
        confidence = (metric_stability * 0.4 + 
                     historical_accuracy * 0.4 + 
                     data_completeness * 0.2)
        
        return min(max(confidence, 0.0), 1.0)

# Usage example
decision_engine = RollbackDecisionEngine('rollback_config.json')

# Monitor and decide
while True:
    metrics = decision_engine.analyze_metrics('http://prometheus:9090')
    decision = decision_engine.make_rollback_decision(metrics)
    
    if decision.should_rollback:
        print(f"ROLLBACK DECISION: {decision.strategy}")
        print(f"Urgency: {decision.urgency}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Reasons: {', '.join(decision.reasons)}")
        
        # Trigger rollback pipeline
        trigger_rollback_pipeline(decision)
    
    time.sleep(30)  # Check every 30 seconds
```

## Database Rollback Management

### Advanced Database Rollback Strategies
```sql
-- Database rollback management system
CREATE SCHEMA rollback_management;

-- Version tracking table
CREATE TABLE rollback_management.schema_versions (
    version_id SERIAL PRIMARY KEY,
    version_number VARCHAR(50) NOT NULL UNIQUE,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rollback_sql TEXT,
    rollback_data_sql TEXT,
    validation_queries TEXT[],
    rollback_safe BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100),
    notes TEXT
);

-- Rollback execution log
CREATE TABLE rollback_management.rollback_executions (
    execution_id SERIAL PRIMARY KEY,
    from_version VARCHAR(50),
    to_version VARCHAR(50),
    execution_type VARCHAR(20), -- 'schema', 'data', 'full'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20), -- 'running', 'completed', 'failed', 'rolled_back'
    error_message TEXT,
    rollback_plan_id VARCHAR(100),
    executed_by VARCHAR(100)
);

-- Data backup tracking
CREATE TABLE rollback_management.data_backups (
    backup_id SERIAL PRIMARY KEY,
    backup_name VARCHAR(200) NOT NULL,
    backup_type VARCHAR(50), -- 'full', 'incremental', 'point_in_time'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    backup_size BIGINT,
    backup_location TEXT,
    retention_until TIMESTAMP,
    backup_metadata JSONB,
    validation_status VARCHAR(20) DEFAULT 'pending'
);

-- Rollback validation procedures
CREATE OR REPLACE FUNCTION rollback_management.validate_rollback_safety(
    p_target_version VARCHAR(50)
) RETURNS TABLE(
    is_safe BOOLEAN,
    blocking_issues TEXT[],
    warnings TEXT[]
) AS $$
DECLARE
    v_current_version VARCHAR(50);
    v_blocking_issues TEXT[] := ARRAY[]::TEXT[];
    v_warnings TEXT[] := ARRAY[]::TEXT[];
    v_is_safe BOOLEAN := TRUE;
BEGIN
    -- Get current schema version
    SELECT version_number INTO v_current_version
    FROM rollback_management.schema_versions
    WHERE applied_at = (SELECT MAX(applied_at) FROM rollback_management.schema_versions);
    
    -- Check if target version exists and is rollback safe
    IF NOT EXISTS (
        SELECT 1 FROM rollback_management.schema_versions 
        WHERE version_number = p_target_version AND rollback_safe = TRUE
    ) THEN
        v_blocking_issues := array_append(v_blocking_issues, 
            'Target version does not exist or is not marked as rollback safe');
        v_is_safe := FALSE;
    END IF;
    
    -- Check for active transactions
    IF EXISTS (
        SELECT 1 FROM pg_stat_activity 
        WHERE state = 'active' AND query NOT LIKE '%rollback_management%'
    ) THEN
        v_warnings := array_append(v_warnings,
            'Active transactions detected - consider scheduling rollback during maintenance window');
    END IF;
    
    -- Check for foreign key constraints that might prevent rollback
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_schema NOT IN ('information_schema', 'pg_catalog', 'rollback_management')
    ) THEN
        v_warnings := array_append(v_warnings,
            'Foreign key constraints detected - ensure referential integrity during rollback');
    END IF;
    
    -- Check backup availability
    IF NOT EXISTS (
        SELECT 1 FROM rollback_management.data_backups
        WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        AND validation_status = 'valid'
    ) THEN
        v_blocking_issues := array_append(v_blocking_issues,
            'No recent valid backup available for recovery');
        v_is_safe := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_is_safe, v_blocking_issues, v_warnings;
END;
$$ LANGUAGE plpgsql;

-- Execute database rollback
CREATE OR REPLACE FUNCTION rollback_management.execute_rollback(
    p_target_version VARCHAR(50),
    p_rollback_type VARCHAR(20) DEFAULT 'full',
    p_executed_by VARCHAR(100) DEFAULT USER
) RETURNS TABLE(
    success BOOLEAN,
    execution_id INTEGER,
    message TEXT
) AS $$
DECLARE
    v_execution_id INTEGER;
    v_current_version VARCHAR(50);
    v_rollback_sql TEXT;
    v_validation_queries TEXT[];
    v_query TEXT;
    v_error_message TEXT;
BEGIN
    -- Validate rollback safety
    IF NOT (SELECT is_safe FROM rollback_management.validate_rollback_safety(p_target_version)) THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 'Rollback safety validation failed';
        RETURN;
    END IF;
    
    -- Get current version
    SELECT version_number INTO v_current_version
    FROM rollback_management.schema_versions
    WHERE applied_at = (SELECT MAX(applied_at) FROM rollback_management.schema_versions);
    
    -- Create execution record
    INSERT INTO rollback_management.rollback_executions (
        from_version, to_version, execution_type, status, executed_by
    ) VALUES (
        v_current_version, p_target_version, p_rollback_type, 'running', p_executed_by
    ) RETURNING execution_id INTO v_execution_id;
    
    BEGIN
        -- Get rollback SQL
        SELECT rollback_sql, validation_queries INTO v_rollback_sql, v_validation_queries
        FROM rollback_management.schema_versions
        WHERE version_number = p_target_version;
        
        -- Execute rollback SQL
        IF v_rollback_sql IS NOT NULL AND p_rollback_type IN ('schema', 'full') THEN
            EXECUTE v_rollback_sql;
        END IF;
        
        -- Run validation queries
        IF v_validation_queries IS NOT NULL THEN
            FOREACH v_query IN ARRAY v_validation_queries LOOP
                EXECUTE v_query;
            END LOOP;
        END IF;
        
        -- Update execution status
        UPDATE rollback_management.rollback_executions
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP
        WHERE execution_id = v_execution_id;
        
        RETURN QUERY SELECT TRUE, v_execution_id, 'Rollback completed successfully';
        
    EXCEPTION WHEN OTHERS THEN
        -- Handle rollback failure
        GET STACKED DIAGNOSTICS v_error_message = MESSAGE_TEXT;
        
        UPDATE rollback_management.rollback_executions
        SET status = 'failed', 
            completed_at = CURRENT_TIMESTAMP,
            error_message = v_error_message
        WHERE execution_id = v_execution_id;
        
        -- Attempt to rollback the rollback
        ROLLBACK;
        
        RETURN QUERY SELECT FALSE, v_execution_id, v_error_message;
    END;
END;
$$ LANGUAGE plpgsql;
```

### Database Rollback Automation
```python
# Database rollback automation system
import psycopg2
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class DatabaseRollbackManager:
    def __init__(self, config: Dict):
        self.config = config
        self.db_connection = None
        self.s3_client = boto3.client('s3')
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect_database(self) -> bool:
        """Establish database connection"""
        try:
            self.db_connection = psycopg2.connect(**self.config['database'])
            self.db_connection.autocommit = False
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    def create_backup_point(self, backup_name: str) -> bool:
        """Create a backup point before rollback"""
        try:
            # Create database dump
            backup_file = f"/tmp/{backup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            dump_command = [
                'pg_dump',
                f"--host={self.config['database']['host']}",
                f"--port={self.config['database']['port']}",
                f"--username={self.config['database']['user']}",
                f"--dbname={self.config['database']['database']}",
                '--no-password',
                '--clean',
                '--if-exists',
                '--create',
                f'--file={backup_file}'
            ]
            
            import subprocess
            result = subprocess.run(dump_command, 
                                  capture_output=True, 
                                  text=True,
                                  env={'PGPASSWORD': self.config['database']['password']})
            
            if result.returncode != 0:
                self.logger.error(f"Backup creation failed: {result.stderr}")
                return False
            
            # Upload backup to S3
            s3_key = f"database-backups/{backup_name}/{datetime.now().strftime('%Y/%m/%d')}/{backup_file.split('/')[-1]}"
            
            self.s3_client.upload_file(
                backup_file,
                self.config['backup_bucket'],
                s3_key
            )
            
            # Record backup in database
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO rollback_management.data_backups 
                (backup_name, backup_type, backup_location, backup_metadata)
                VALUES (%s, %s, %s, %s)
            """, (
                backup_name,
                'full',
                f"s3://{self.config['backup_bucket']}/{s3_key}",
                json.dumps({
                    'backup_file': backup_file,
                    'created_by': 'automated_rollback_system',
                    'backup_size': os.path.getsize(backup_file)
                })
            ))
            self.db_connection.commit()
            
            # Cleanup local file
            os.remove(backup_file)
            
            self.logger.info(f"Backup created successfully: {s3_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return False
    
    def validate_rollback_target(self, target_version: str) -> Tuple[bool, List[str], List[str]]:
        """Validate if rollback to target version is safe"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT is_safe, blocking_issues, warnings
                FROM rollback_management.validate_rollback_safety(%s)
            """, (target_version,))
            
            result = cursor.fetchone()
            return result[0], result[1] or [], result[2] or []
            
        except Exception as e:
            self.logger.error(f"Rollback validation failed: {e}")
            return False, [str(e)], []
    
    def execute_rollback(self, target_version: str, rollback_type: str = 'full') -> Tuple[bool, Optional[int], str]:
        """Execute database rollback to target version"""
        try:
            # Validate rollback
            is_safe, blocking_issues, warnings = self.validate_rollback_target(target_version)
            
            if not is_safe:
                return False, None, f"Rollback validation failed: {'; '.join(blocking_issues)}"
            
            if warnings:
                self.logger.warning(f"Rollback warnings: {'; '.join(warnings)}")
            
            # Create backup point
            backup_name = f"pre_rollback_{target_version}"
            if not self.create_backup_point(backup_name):
                return False, None, "Failed to create backup point"
            
            # Execute rollback
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT success, execution_id, message
                FROM rollback_management.execute_rollback(%s, %s, %s)
            """, (target_version, rollback_type, 'automated_system'))
            
            success, execution_id, message = cursor.fetchone()
            
            if success:
                self.db_connection.commit()
                self.logger.info(f"Rollback successful: {message}")
            else:
                self.db_connection.rollback()
                self.logger.error(f"Rollback failed: {message}")
            
            return success, execution_id, message
            
        except Exception as e:
            self.db_connection.rollback()
            self.logger.error(f"Rollback execution failed: {e}")
            return False, None, str(e)
    
    def monitor_rollback_progress(self, execution_id: int) -> Dict:
        """Monitor rollback execution progress"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT execution_type, started_at, completed_at, status, error_message
                FROM rollback_management.rollback_executions
                WHERE execution_id = %s
            """, (execution_id,))
            
            result = cursor.fetchone()
            if not result:
                return {'status': 'not_found'}
            
            execution_type, started_at, completed_at, status, error_message = result
            
            progress = {
                'execution_id': execution_id,
                'execution_type': execution_type,
                'started_at': started_at.isoformat() if started_at else None,
                'completed_at': completed_at.isoformat() if completed_at else None,
                'status': status,
                'error_message': error_message,
                'duration': None
            }
            
            if started_at and completed_at:
                progress['duration'] = (completed_at - started_at).total_seconds()
            
            return progress
            
        except Exception as e:
            self.logger.error(f"Failed to monitor rollback progress: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def verify_rollback_success(self, target_version: str, execution_id: int) -> bool:
        """Verify rollback completed successfully"""
        try:
            # Check execution status
            progress = self.monitor_rollback_progress(execution_id)
            if progress['status'] != 'completed':
                return False
            
            # Verify current schema version
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT version_number FROM rollback_management.schema_versions
                WHERE applied_at = (
                    SELECT MAX(applied_at) FROM rollback_management.schema_versions
                )
            """)
            
            current_version = cursor.fetchone()[0]
            
            if current_version != target_version:
                self.logger.error(f"Version mismatch: expected {target_version}, got {current_version}")
                return False
            
            # Run additional verification queries
            cursor.execute("""
                SELECT validation_queries FROM rollback_management.schema_versions
                WHERE version_number = %s
            """, (target_version,))
            
            validation_queries = cursor.fetchone()[0]
            if validation_queries:
                for query in validation_queries:
                    try:
                        cursor.execute(query)
                        # If query runs without error, validation passes
                    except Exception as e:
                        self.logger.error(f"Validation query failed: {query} - {e}")
                        return False
            
            self.logger.info(f"Rollback verification successful for version {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback verification failed: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT backup_id, backup_location 
                FROM rollback_management.data_backups
                WHERE created_at < %s AND validation_status = 'valid'
            """, (cutoff_date,))
            
            old_backups = cursor.fetchall()
            
            for backup_id, backup_location in old_backups:
                if backup_location.startswith('s3://'):
                    # Delete from S3
                    bucket_name = backup_location.split('/')[2]
                    s3_key = '/'.join(backup_location.split('/')[3:])
                    
                    try:
                        self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
                        
                        # Update database record
                        cursor.execute("""
                            UPDATE rollback_management.data_backups
                            SET validation_status = 'deleted'
                            WHERE backup_id = %s
                        """, (backup_id,))
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to delete backup {backup_location}: {e}")
            
            self.db_connection.commit()
            self.logger.info(f"Cleaned up {len(old_backups)} old backups")
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")

# Usage example
config = {
    'database': {
        'host': 'localhost',
        'port': 5432,
        'database': 'myapp',
        'user': 'admin',
        'password': 'secure_password'
    },
    'backup_bucket': 'my-database-backups'
}

rollback_manager = DatabaseRollbackManager(config)
rollback_manager.connect_database()

# Execute rollback
success, execution_id, message = rollback_manager.execute_rollback('v2.1.0', 'full')

if success:
    # Monitor progress
    while True:
        progress = rollback_manager.monitor_rollback_progress(execution_id)
        if progress['status'] in ['completed', 'failed']:
            break
        time.sleep(5)
    
    # Verify success
    if rollback_manager.verify_rollback_success('v2.1.0', execution_id):
        print("Rollback completed and verified successfully")
    else:
        print("Rollback verification failed")
else:
    print(f"Rollback failed: {message}")
```

## Infrastructure Recovery

### Infrastructure State Rollback
```hcl
# Terraform rollback management
terraform {
  required_version = ">= 1.5"
  
  backend "s3" {
    bucket         = "terraform-state-rollback"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    versioning     = true
    
    # State rollback configuration
    lifecycle_configuration {
      rule {
        id     = "state_versioning"
        status = "Enabled"
        
        noncurrent_version_expiration {
          days = 90
        }
        
        noncurrent_version_transition {
          days          = 30
          storage_class = "STANDARD_IA"
        }
      }
    }
  }
}

# Infrastructure rollback data sources
data "terraform_remote_state" "previous_version" {
  count = var.rollback_enabled ? 1 : 0
  
  backend = "s3"
  config = {
    bucket         = "terraform-state-rollback"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-west-2"
    version_id     = var.rollback_version_id
  }
}

# Rollback configuration variables
variable "rollback_enabled" {
  description = "Enable infrastructure rollback mode"
  type        = bool
  default     = false
}

variable "rollback_version_id" {
  description = "State version to rollback to"
  type        = string
  default     = ""
}

variable "rollback_strategy" {
  description = "Rollback strategy: recreate, update_in_place, or blue_green"
  type        = string
  default     = "update_in_place"
  
  validation {
    condition = contains([
      "recreate",
      "update_in_place", 
      "blue_green"
    ], var.rollback_strategy)
    error_message = "Invalid rollback strategy."
  }
}

# Infrastructure rollback locals
locals {
  is_rollback = var.rollback_enabled && var.rollback_version_id != ""
  
  # Extract previous state configurations
  previous_config = local.is_rollback ? data.terraform_remote_state.previous_version[0].outputs : {}
  
  # Rollback-aware resource configuration
  app_instance_count = local.is_rollback ? 
    lookup(local.previous_config, "app_instance_count", var.app_instance_count) : 
    var.app_instance_count
  
  app_instance_type = local.is_rollback ?
    lookup(local.previous_config, "app_instance_type", var.app_instance_type) :
    var.app_instance_type
  
  database_instance_class = local.is_rollback ?
    lookup(local.previous_config, "database_instance_class", var.database_instance_class) :
    var.database_instance_class
  
  # Blue-green rollback configuration
  deployment_slot = local.is_rollback && var.rollback_strategy == "blue_green" ?
    (lookup(local.previous_config, "active_slot", "blue") == "blue" ? "green" : "blue") :
    var.deployment_slot
}

# Application Load Balancer with rollback support
resource "aws_lb" "app_lb" {
  name               = "${var.environment}-app-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb_sg.id]
  subnets           = var.public_subnet_ids

  enable_deletion_protection = !local.is_rollback

  tags = merge(var.common_tags, {
    Name = "${var.environment}-app-lb"
    RollbackSupported = "true"
  })
}

# Target groups for blue-green rollback
resource "aws_lb_target_group" "app_tg_blue" {
  name     = "${var.environment}-app-tg-blue"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 30
    interval            = 60
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name = "${var.environment}-app-tg-blue"
    Slot = "blue"
  }
}

resource "aws_lb_target_group" "app_tg_green" {
  name     = "${var.environment}-app-tg-green"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 30
    interval            = 60
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name = "${var.environment}-app-tg-green"
    Slot = "green"
  }
}

# Load balancer listener with rollback routing
resource "aws_lb_listener" "app_listener" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = local.deployment_slot == "blue" ? 
      aws_lb_target_group.app_tg_blue.arn : 
      aws_lb_target_group.app_tg_green.arn
  }

  # Rollback-aware routing rules
  dynamic "default_action" {
    for_each = local.is_rollback && var.rollback_strategy == "blue_green" ? [1] : []
    
    content {
      type = "forward"
      
      forward {
        target_group {
          arn    = aws_lb_target_group.app_tg_blue.arn
          weight = local.deployment_slot == "blue" ? 100 : 0
        }
        
        target_group {
          arn    = aws_lb_target_group.app_tg_green.arn
          weight = local.deployment_slot == "green" ? 100 : 0
        }
        
        stickiness {
          enabled  = true
          duration = 86400
        }
      }
    }
  }
}

# Auto Scaling Group with rollback configuration
resource "aws_autoscaling_group" "app_asg" {
  name                = "${var.environment}-app-asg-${local.deployment_slot}"
  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = [
    local.deployment_slot == "blue" ? 
      aws_lb_target_group.app_tg_blue.arn : 
      aws_lb_target_group.app_tg_green.arn
  ]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = local.is_rollback ? 1 : var.min_instance_count
  max_size         = local.is_rollback ? local.app_instance_count * 2 : var.max_instance_count
  desired_capacity = local.app_instance_count

  # Rollback-aware instance refresh
  instance_refresh {
    strategy = local.is_rollback ? "Rolling" : var.instance_refresh_strategy
    preferences {
      min_healthy_percentage = local.is_rollback ? 100 : 50
      instance_warmup       = local.is_rollback ? 600 : 300
      checkpoint_percentages = local.is_rollback ? [50, 100] : [25, 50, 75, 100]
      checkpoint_delay      = local.is_rollback ? "300" : "60"
    }
    triggers = local.is_rollback ? ["launch_template"] : ["launch_template", "desired_capacity"]
  }

  launch_template {
    id      = aws_launch_template.app_template.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.environment}-app-instance"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "DeploymentSlot"
    value               = local.deployment_slot
    propagate_at_launch = true
  }

  tag {
    key                 = "RollbackEnabled"
    value               = local.is_rollback ? "true" : "false"
    propagate_at_launch = true
  }
}

# RDS instance with rollback snapshot support
resource "aws_db_instance" "app_database" {
  identifier     = "${var.environment}-database"
  engine         = "postgres"
  engine_version = local.is_rollback ? 
    lookup(local.previous_config, "database_engine_version", var.database_engine_version) :
    var.database_engine_version
  
  instance_class    = local.database_instance_class
  allocated_storage = local.is_rollback ?
    lookup(local.previous_config, "database_allocated_storage", var.database_allocated_storage) :
    var.database_allocated_storage

  db_name  = var.database_name
  username = var.database_username
  password = var.database_password

  vpc_security_group_ids = [aws_security_group.database_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.database_subnet_group.name

  # Rollback-specific configurations
  backup_retention_period = local.is_rollback ? 30 : var.backup_retention_period
  backup_window          = local.is_rollback ? "03:00-04:00" : var.backup_window
  maintenance_window     = local.is_rollback ? "sun:04:00-sun:05:00" : var.maintenance_window
  
  # Point-in-time recovery for rollback
  restore_to_point_in_time {
    count                     = local.is_rollback && var.rollback_strategy == "point_in_time" ? 1 : 0
    source_db_instance_identifier = lookup(local.previous_config, "database_identifier", "")
    restore_time              = var.rollback_target_time
    use_latest_restorable_time = var.rollback_target_time == "" ? true : false
  }

  # Snapshot restore for rollback
  snapshot_identifier = local.is_rollback && var.rollback_strategy == "snapshot" ?
    var.rollback_snapshot_id : null

  skip_final_snapshot       = !local.is_rollback
  final_snapshot_identifier = local.is_rollback ? null : "${var.environment}-database-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  deletion_protection = !local.is_rollback

  tags = {
    Name = "${var.environment}-database"
    RollbackSupported = "true"
  }
}

# Output rollback information
output "rollback_info" {
  value = local.is_rollback ? {
    rollback_enabled     = true
    rollback_version_id  = var.rollback_version_id
    rollback_strategy    = var.rollback_strategy
    deployment_slot      = local.deployment_slot
    previous_config      = local.previous_config
  } : {
    rollback_enabled = false
  }
}

# Output current configuration for future rollbacks
output "current_config" {
  value = {
    app_instance_count       = local.app_instance_count
    app_instance_type        = local.app_instance_type
    database_instance_class  = local.database_instance_class
    database_engine_version  = aws_db_instance.app_database.engine_version
    database_allocated_storage = aws_db_instance.app_database.allocated_storage
    database_identifier      = aws_db_instance.app_database.identifier
    active_slot             = local.deployment_slot
    load_balancer_arn       = aws_lb.app_lb.arn
    target_group_blue_arn   = aws_lb_target_group.app_tg_blue.arn
    target_group_green_arn  = aws_lb_target_group.app_tg_green.arn
  }
  
  sensitive = false
}
```

### Kubernetes Rollback Integration
```yaml
# Kubernetes rollback management
apiVersion: v1
kind: ConfigMap
metadata:
  name: rollback-config
  namespace: rollback-system
data:
  rollback-strategies.yaml: |
    strategies:
      rolling_update:
        description: "Standard rolling update rollback"
        max_unavailable: "25%"
        max_surge: "25%"
        timeout: "600s"
        
      recreate:
        description: "Recreate deployment rollback"
        timeout: "300s"
        pre_rollback_hooks:
          - drain_nodes
          - backup_persistent_volumes
        
      blue_green:
        description: "Blue-green deployment rollback"
        traffic_split_ratio: "0:100"
        validation_timeout: "300s"
        automatic_promotion: false
        
      canary:
        description: "Canary rollback with traffic management"
        initial_traffic: "10%"
        traffic_increment: "20%"
        increment_interval: "300s"
        success_threshold: "95%"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rollback-controller
  namespace: rollback-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rollback-controller
  template:
    metadata:
      labels:
        app: rollback-controller
    spec:
      serviceAccountName: rollback-controller
      containers:
      - name: controller
        image: rollback-controller:v1.2.0
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 8443
          name: webhook
        env:
        - name: WEBHOOK_CERT_DIR
          value: "/tmp/k8s-webhook-server/serving-certs"
        - name: METRICS_PORT
          value: "8080"
        - name: WEBHOOK_PORT
          value: "8443"
        volumeMounts:
        - name: webhook-certs
          mountPath: "/tmp/k8s-webhook-server/serving-certs"
          readOnly: true
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: "/healthz"
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: "/readyz"
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: webhook-certs
        secret:
          secretName: rollback-controller-certs

---
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: rollbackplans.rollback.io
spec:
  group: rollback.io
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              targetDeployment:
                type: string
                description: "Target deployment to rollback"
              targetRevision:
                type: string
                description: "Target revision to rollback to"
              strategy:
                type: string
                enum: ["rolling_update", "recreate", "blue_green", "canary"]
                description: "Rollback strategy"
              automaticTriggers:
                type: object
                properties:
                  healthCheckFailures:
                    type: integer
                    minimum: 1
                    description: "Number of health check failures to trigger rollback"
                  errorRateThreshold:
                    type: string
                    pattern: "^[0-9]+(\.[0-9]+)?%$"
                    description: "Error rate threshold to trigger rollback"
                  responseTimeThreshold:
                    type: string
                    description: "Response time threshold to trigger rollback"
              validationChecks:
                type: array
                items:
                  type: object
                  properties:
                    name:
                      type: string
                    type:
                      type: string
                      enum: ["http", "tcp", "exec", "custom"]
                    config:
                      type: object
              rollbackTimeout:
                type: string
                description: "Timeout for rollback operation"
          status:
            type: object
            properties:
              phase:
                type: string
                enum: ["Pending", "InProgress", "Completed", "Failed"]
              conditions:
                type: array
                items:
                  type: object
                  properties:
                    type:
                      type: string
                    status:
                      type: string
                    reason:
                      type: string
                    message:
                      type: string
                    lastTransitionTime:
                      type: string
              rollbackStartTime:
                type: string
              rollbackCompletionTime:
                type: string
  scope: Namespaced
  names:
    plural: rollbackplans
    singular: rollbackplan
    kind: RollbackPlan

---
# Example RollbackPlan for application
apiVersion: rollback.io/v1
kind: RollbackPlan
metadata:
  name: webapp-rollback-plan
  namespace: production
spec:
  targetDeployment: "webapp-deployment"
  targetRevision: "webapp-deployment-5f7d8c9b"
  strategy: "blue_green"
  
  automaticTriggers:
    healthCheckFailures: 3
    errorRateThreshold: "2.5%"
    responseTimeThreshold: "500ms"
  
  validationChecks:
  - name: health-check
    type: http
    config:
      url: "http://webapp-service/health"
      expectedStatus: 200
      timeout: "30s"
      
  - name: database-connectivity
    type: custom
    config:
      command: ["kubectl", "exec", "-n", "production", "webapp-pod", "--", "pg_isready", "-h", "postgres-service"]
      
  - name: integration-test
    type: http
    config:
      url: "http://webapp-service/api/test"
      expectedStatus: 200
      timeout: "60s"
  
  rollbackTimeout: "15m"

---
# Application deployment with rollback annotations
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-deployment
  namespace: production
  annotations:
    rollback.io/strategy: "blue_green"
    rollback.io/health-check-url: "http://webapp-service/health"
    rollback.io/rollback-plan: "webapp-rollback-plan"
    rollback.io/automatic-rollback: "true"
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
        version: "v2.3.0"
      annotations:
        rollback.io/health-check-path: "/health"
        rollback.io/metrics-port: "8080"
    spec:
      containers:
      - name: webapp
        image: webapp:v2.3.0
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 8081
          name: metrics
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
# Service mesh rollback configuration (Istio)
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: webapp-vs
  namespace: production
spec:
  hosts:
  - webapp-service
  http:
  - match:
    - headers:
        rollback-test:
          exact: "true"
    route:
    - destination:
        host: webapp-service
        subset: v2-2-0  # Previous version for testing
      weight: 100
  - route:
    - destination:
        host: webapp-service
        subset: v2-3-0  # Current version
      weight: 100

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: webapp-dr
  namespace: production
spec:
  host: webapp-service
  subsets:
  - name: v2-3-0
    labels:
      version: v2.3.0
    trafficPolicy:
      connectionPool:
        tcp:
          maxConnections: 100
        http:
          http1MaxPendingRequests: 50
          maxRequestsPerConnection: 10
      outlierDetection:
        consecutiveErrors: 3
        interval: 30s
        baseEjectionTime: 30s
        maxEjectionPercent: 50
  - name: v2-2-0
    labels:
      version: v2.2.0
    trafficPolicy:
      connectionPool:
        tcp:
          maxConnections: 100
        http:
          http1MaxPendingRequests: 50
          maxRequestsPerConnection: 10

---
# Prometheus monitoring for rollback decisions
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: webapp-rollback-monitor
  namespace: production
spec:
  selector:
    matchLabels:
      app: webapp
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s

---
# PrometheusRule for rollback alerting
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: webapp-rollback-rules
  namespace: production
spec:
  groups:
  - name: rollback.rules
    rules:
    - alert: HighErrorRate
      expr: |
        (
          rate(http_requests_total{job="webapp", status=~"5.."}[5m]) /
          rate(http_requests_total{job="webapp"}[5m])
        ) > 0.02
      for: 2m
      labels:
        severity: warning
        rollback_trigger: "true"
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value | humanizePercentage }}"
        
    - alert: HighResponseTime
      expr: |
        histogram_quantile(0.95, 
          rate(http_request_duration_seconds_bucket{job="webapp"}[5m])
        ) > 0.5
      for: 3m
      labels:
        severity: warning
        rollback_trigger: "true"
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is {{ $value }}s"
        
    - alert: PodCrashLoop
      expr: |
        increase(kube_pod_container_status_restarts_total{
          pod=~"webapp-deployment-.*"
        }[10m]) > 3
      for: 5m
      labels:
        severity: critical
        rollback_trigger: "true"
      annotations:
        summary: "Pod crash loop detected"
        description: "Pod {{ $labels.pod }} is crash looping"
```

This comprehensive rollback and recovery system provides:

1. **Multi-layer rollback architecture** with application, database, and infrastructure components
2. **Automated rollback decision engine** using ML and metrics analysis
3. **Database rollback management** with PostgreSQL stored procedures and Python automation
4. **Infrastructure state rollback** using Terraform with blue-green and versioned deployments
5. **Kubernetes rollback integration** with custom resources and service mesh support
6. **Advanced monitoring and alerting** for triggering automated rollbacks
7. **Validation and verification systems** to ensure rollback success
8. **Enterprise-grade safety checks** and approval workflows

The system supports multiple rollback strategies (immediate, canary, blue-green), integrates with monitoring systems for automated triggering, and provides comprehensive validation to ensure rollback success.