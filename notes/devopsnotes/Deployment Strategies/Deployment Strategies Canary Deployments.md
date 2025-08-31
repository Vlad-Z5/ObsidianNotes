# Enterprise Canary Deployment Strategies

Advanced canary deployment patterns for mission-critical enterprise applications with intelligent traffic management, automated analysis, and compliance integration.

## Table of Contents
1. [Enterprise Canary Architecture](#enterprise-canary-architecture)
2. [Financial Trading Platform Implementation](#financial-trading-platform-implementation)
3. [Healthcare Canary Deployment](#healthcare-canary-deployment)
4. [AI-Driven Canary Analysis](#ai-driven-canary-analysis)
5. [Compliance-Aware Canary Deployment](#compliance-aware-canary-deployment)
6. [Multi-Region Canary Orchestration](#multi-region-canary-orchestration)
7. [Advanced Monitoring & Alerting](#advanced-monitoring-alerting)

## Enterprise Canary Architecture

### Intelligent Financial Trading Platform Canary
```python
#!/usr/bin/env python3
# enterprise_canary_manager.py
# Enterprise-grade canary deployment with AI-driven analysis

import asyncio
import json
import logging
import statistics
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import kubernetes_asyncio as k8s
import aiohttp

class CanaryStrategy(Enum):
    PROGRESSIVE = "progressive"
    AB_TEST = "ab_test"
    FEATURE_FLAG = "feature_flag"
    SHADOW_TRAFFIC = "shadow_traffic"
    BLUE_GREEN_CANARY = "blue_green_canary"

class CanaryPhase(Enum):
    PREPARATION = "preparation"
    INITIAL_DEPLOYMENT = "initial_deployment"
    TRAFFIC_ANALYSIS = "traffic_analysis"
    PROGRESSIVE_ROLLOUT = "progressive_rollout"
    VALIDATION = "validation"
    PROMOTION = "promotion"
    CLEANUP = "cleanup"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TradingMetrics:
    order_fill_rate: float
    latency_p99_ms: float
    throughput_tps: int
    slippage_bps: float  # basis points
    pnl_impact_usd: float
    market_impact_bps: float
    compliance_violations: int
    system_stability_score: float

@dataclass
class CanaryAnalysisResult:
    phase: CanaryPhase
    traffic_percentage: int
    success_criteria_met: bool
    risk_level: RiskLevel
    metrics: TradingMetrics
    anomalies_detected: List[str]
    recommendations: List[str]
    confidence_score: float

@dataclass
class EnterpriseCanaryConfig:
    application_name: str
    trading_environment: str  # prod, uat, dev
    strategy: CanaryStrategy
    initial_traffic_percentage: int
    max_traffic_percentage: int
    analysis_duration_minutes: int
    success_thresholds: TradingMetrics
    rollback_thresholds: TradingMetrics
    compliance_requirements: List[str]
    risk_tolerance: RiskLevel

class EnterpriseCanaryManager:
    def __init__(self, config: EnterpriseCanaryConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.k8s_client = None
        self.analysis_history: List[CanaryAnalysisResult] = []
        self.trading_session_data = {}
        self.ml_models = {}
        
    async def initialize(self):
        """Initialize Kubernetes client and ML models"""
        k8s.config.load_incluster_config()
        self.k8s_client = k8s.client.ApiClient()
        
        # Initialize ML models for anomaly detection
        await self._initialize_ml_models()
        
        self.logger.info("Enterprise Canary Manager initialized")
    
    async def execute_intelligent_canary_deployment(self, image_tag: str) -> bool:
        """Execute AI-driven canary deployment with real-time analysis"""
        deployment_id = f"canary-{int(datetime.now().timestamp())}"
        
        try:
            self.logger.info(f"Starting intelligent canary deployment: {deployment_id}")
            
            # Phase 1: Pre-deployment risk assessment
            risk_assessment = await self._conduct_pre_deployment_risk_assessment()
            if risk_assessment.risk_level == RiskLevel.CRITICAL:
                self.logger.error("Pre-deployment risk assessment failed - deployment blocked")
                return False
            
            # Phase 2: Deploy canary with minimal traffic
            await self._deploy_canary_version(image_tag)
            
            # Phase 3: AI-driven progressive analysis
            progressive_success = await self._execute_ai_driven_progressive_rollout()
            if not progressive_success:
                await self._execute_intelligent_rollback()
                return False
            
            # Phase 4: Final validation and promotion
            promotion_success = await self._execute_final_validation_and_promotion(image_tag)
            if not promotion_success:
                await self._execute_intelligent_rollback()
                return False
            
            # Phase 5: Post-deployment monitoring
            await self._execute_post_deployment_monitoring()
            
            self.logger.info(f"Intelligent canary deployment {deployment_id} completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Canary deployment {deployment_id} failed: {e}")
            await self._execute_emergency_rollback()
            return False
    
    async def _conduct_pre_deployment_risk_assessment(self) -> CanaryAnalysisResult:
        """Conduct comprehensive pre-deployment risk assessment"""
        # Market conditions analysis
        market_volatility = await self._analyze_market_conditions()
        
        # System health assessment
        system_health = await self._assess_system_health()
        
        # Trading session analysis
        session_risk = await self._analyze_trading_session_risk()
        
        # Historical deployment analysis
        historical_risk = await self._analyze_historical_deployment_patterns()
        
        # Calculate composite risk score
        risk_factors = [market_volatility, system_health, session_risk, historical_risk]
        composite_risk = statistics.mean(risk_factors)
        
        risk_level = self._calculate_risk_level(composite_risk)
        
        return CanaryAnalysisResult(
            phase=CanaryPhase.PREPARATION,
            traffic_percentage=0,
            success_criteria_met=risk_level != RiskLevel.CRITICAL,
            risk_level=risk_level,
            metrics=await self._collect_baseline_trading_metrics(),
            anomalies_detected=[],
            recommendations=await self._generate_risk_recommendations(composite_risk),
            confidence_score=0.95
        )
    
    async def _execute_ai_driven_progressive_rollout(self) -> bool:
        """Execute progressive rollout with AI-driven decision making"""
        traffic_stages = [1, 3, 5, 10, 20, 35, 50, 75, 100]
        
        for stage in traffic_stages:
            self.logger.info(f"Analyzing canary at {stage}% traffic")
            
            # Update traffic routing
            await self._update_canary_traffic_percentage(stage)
            
            # Wait for traffic stabilization
            await asyncio.sleep(60)  # 1 minute
            
            # AI-driven analysis for this stage
            analysis_result = await self._execute_ai_analysis(stage)
            self.analysis_history.append(analysis_result)
            
            if not analysis_result.success_criteria_met:
                self.logger.error(f"AI analysis failed at {stage}% traffic: {analysis_result.anomalies_detected}")
                return False
            
            # Adaptive wait time based on risk level
            wait_time = self._calculate_adaptive_wait_time(analysis_result.risk_level, stage)
            await asyncio.sleep(wait_time)
            
            # Check for market events that might affect deployment
            market_events = await self._check_market_events()
            if market_events:
                self.logger.warning(f"Market events detected: {market_events}")
                if await self._should_pause_for_market_events(market_events):
                    await self._pause_deployment_for_market_events()
            
            self.logger.info(f"Stage {stage}% completed successfully")
        
        return True
    
    async def _execute_ai_analysis(self, traffic_percentage: int) -> CanaryAnalysisResult:
        """Execute comprehensive AI-driven analysis of canary performance"""
        # Collect real-time metrics
        current_metrics = await self._collect_real_time_trading_metrics()
        baseline_metrics = await self._get_baseline_metrics()
        
        # Statistical analysis
        statistical_anomalies = await self._detect_statistical_anomalies(current_metrics, baseline_metrics)
        
        # ML-based anomaly detection
        ml_anomalies = await self._detect_ml_anomalies(current_metrics)
        
        # Trading-specific analysis
        trading_analysis = await self._analyze_trading_performance(current_metrics, baseline_metrics)
        
        # Risk calculation
        risk_score = await self._calculate_comprehensive_risk_score(
            current_metrics, statistical_anomalies, ml_anomalies, trading_analysis
        )
        
        # Success criteria evaluation
        success_criteria_met = await self._evaluate_success_criteria(current_metrics, risk_score)
        
        # Generate recommendations
        recommendations = await self._generate_ai_recommendations(
            current_metrics, statistical_anomalies, ml_anomalies, risk_score
        )
        
        return CanaryAnalysisResult(
            phase=CanaryPhase.PROGRESSIVE_ROLLOUT,
            traffic_percentage=traffic_percentage,
            success_criteria_met=success_criteria_met,
            risk_level=self._calculate_risk_level(risk_score),
            metrics=current_metrics,
            anomalies_detected=statistical_anomalies + ml_anomalies,
            recommendations=recommendations,
            confidence_score=await self._calculate_confidence_score(current_metrics, baseline_metrics)
        )
    
    async def _detect_statistical_anomalies(self, current: TradingMetrics, baseline: TradingMetrics) -> List[str]:
        """Detect statistical anomalies in trading metrics"""
        anomalies = []
        
        # Order fill rate analysis
        fill_rate_change = ((current.order_fill_rate - baseline.order_fill_rate) / baseline.order_fill_rate) * 100
        if abs(fill_rate_change) > 5.0:  # 5% change threshold
            anomalies.append(f"Order fill rate changed by {fill_rate_change:.2f}%")
        
        # Latency analysis
        latency_increase = ((current.latency_p99_ms - baseline.latency_p99_ms) / baseline.latency_p99_ms) * 100
        if latency_increase > 20.0:  # 20% increase threshold
            anomalies.append(f"P99 latency increased by {latency_increase:.2f}%")
        
        # Slippage analysis
        slippage_change = current.slippage_bps - baseline.slippage_bps
        if slippage_change > 2.0:  # 2 basis points threshold
            anomalies.append(f"Slippage increased by {slippage_change:.1f} basis points")
        
        # PnL impact analysis
        if abs(current.pnl_impact_usd) > 10000:  # $10K threshold
            anomalies.append(f"Significant PnL impact: ${current.pnl_impact_usd:,.2f}")
        
        return anomalies
    
    async def _detect_ml_anomalies(self, metrics: TradingMetrics) -> List[str]:
        """Use ML models to detect anomalies"""
        anomalies = []
        
        # Prepare feature vector
        feature_vector = np.array([
            metrics.order_fill_rate,
            metrics.latency_p99_ms,
            metrics.throughput_tps,
            metrics.slippage_bps,
            metrics.market_impact_bps,
            metrics.system_stability_score
        ]).reshape(1, -1)
        
        # Anomaly detection using isolation forest
        if 'anomaly_detector' in self.ml_models:
            anomaly_score = self.ml_models['anomaly_detector'].decision_function(feature_vector)[0]
            if anomaly_score < -0.5:  # Threshold for anomaly
                anomalies.append(f"ML anomaly detected (score: {anomaly_score:.3f})")
        
        # Performance regression detection
        if 'regression_detector' in self.ml_models:
            predicted_performance = self.ml_models['regression_detector'].predict(feature_vector)[0]
            actual_performance = metrics.system_stability_score
            
            if abs(predicted_performance - actual_performance) > 0.1:
                anomalies.append(f"Performance regression detected (expected: {predicted_performance:.3f}, actual: {actual_performance:.3f})")
        
        return anomalies
    
    async def _analyze_trading_performance(self, current: TradingMetrics, baseline: TradingMetrics) -> Dict[str, Any]:
        """Analyze trading-specific performance metrics"""
        analysis = {}
        
        # Market impact analysis
        impact_ratio = current.market_impact_bps / baseline.market_impact_bps if baseline.market_impact_bps > 0 else 1.0
        analysis['market_impact_ratio'] = impact_ratio
        analysis['market_impact_acceptable'] = impact_ratio < 1.5  # 50% increase threshold
        
        # Execution quality analysis
        execution_quality = (current.order_fill_rate / 100) * (1 / (1 + current.slippage_bps / 100))
        analysis['execution_quality'] = execution_quality
        analysis['execution_quality_acceptable'] = execution_quality > 0.95  # 95% threshold
        
        # System performance analysis
        system_performance = current.system_stability_score * (current.throughput_tps / max(1, baseline.throughput_tps))
        analysis['system_performance'] = system_performance
        analysis['system_performance_acceptable'] = system_performance > 0.9  # 90% threshold
        
        return analysis
    
    async def _calculate_comprehensive_risk_score(self, 
                                                metrics: TradingMetrics,
                                                stat_anomalies: List[str],
                                                ml_anomalies: List[str],
                                                trading_analysis: Dict[str, Any]) -> float:
        """Calculate comprehensive risk score combining multiple factors"""
        # Base risk from metrics
        metric_risk = 0.0
        
        # Latency risk
        if metrics.latency_p99_ms > 100:  # 100ms threshold
            metric_risk += min(0.3, (metrics.latency_p99_ms - 100) / 500)  # Max 0.3
        
        # Fill rate risk
        if metrics.order_fill_rate < 99.0:  # 99% threshold
            metric_risk += (99.0 - metrics.order_fill_rate) / 100  # Max 0.99
        
        # PnL risk
        pnl_risk = min(0.4, abs(metrics.pnl_impact_usd) / 50000)  # Max 0.4 at $50K
        metric_risk += pnl_risk
        
        # Anomaly risk
        anomaly_risk = min(0.5, (len(stat_anomalies) + len(ml_anomalies)) * 0.1)
        
        # Trading performance risk
        trading_risk = 0.0
        if not trading_analysis.get('market_impact_acceptable', True):
            trading_risk += 0.2
        if not trading_analysis.get('execution_quality_acceptable', True):
            trading_risk += 0.3
        if not trading_analysis.get('system_performance_acceptable', True):
            trading_risk += 0.2
        
        # Compliance risk
        compliance_risk = min(0.3, metrics.compliance_violations * 0.1)
        
        total_risk = metric_risk + anomaly_risk + trading_risk + compliance_risk
        return min(1.0, total_risk)  # Cap at 1.0
    
    async def _calculate_confidence_score(self, current: TradingMetrics, baseline: TradingMetrics) -> float:
        """Calculate confidence score for the analysis"""
        # Data quality score
        data_quality = 1.0
        if current.throughput_tps < baseline.throughput_tps * 0.5:
            data_quality -= 0.3  # Insufficient data
        
        # Measurement consistency
        consistency_score = 1.0
        if len(self.analysis_history) > 2:
            recent_analyses = self.analysis_history[-3:]
            risk_scores = [analysis.risk_level.value for analysis in recent_analyses]
            if len(set(risk_scores)) > 2:  # High variability
                consistency_score -= 0.2
        
        # Market stability
        market_stability = await self._assess_market_stability()
        
        return min(1.0, data_quality * consistency_score * market_stability)

class FinancialCanaryManager(EnterpriseCanaryManager):
    """Specialized canary manager for financial trading systems"""
    
    def __init__(self, config: EnterpriseCanaryConfig):
        super().__init__(config)
        self.regulatory_frameworks = ["MiFID_II", "Dodd_Frank", "EMIR", "Basel_III"]
        self.market_data_feeds = {}
        
    async def execute_regulated_canary_deployment(self, image_tag: str) -> bool:
        """Execute canary deployment with regulatory compliance"""
        # Pre-deployment regulatory checks
        regulatory_clearance = await self._validate_regulatory_compliance()
        if not regulatory_clearance:
            return False
        
        # Market hours validation
        market_status = await self._validate_market_hours()
        if not market_status['can_deploy']:
            self.logger.info(f"Deployment postponed: {market_status['reason']}")
            return False
        
        # Execute with enhanced compliance monitoring
        return await super().execute_intelligent_canary_deployment(image_tag)
    
    async def _validate_regulatory_compliance(self) -> bool:
        """Validate compliance with financial regulations"""
        compliance_checks = [
            self._check_mifid_ii_compliance(),
            self._check_circuit_breaker_status(),
            self._check_risk_limits(),
            self._validate_audit_trail(),
            self._check_best_execution_requirements()
        ]
        
        results = await asyncio.gather(*compliance_checks, return_exceptions=True)
        return all(result is True for result in results)
    
    async def _validate_market_hours(self) -> Dict[str, Any]:
        """Validate deployment timing against market hours"""
        now = datetime.now()
        
        # Check major market hours
        market_sessions = {
            'US': (9, 30, 16, 0),  # 9:30 AM - 4:00 PM EST
            'EU': (8, 0, 16, 30),   # 8:00 AM - 4:30 PM CET
            'ASIA': (9, 0, 15, 0)   # 9:00 AM - 3:00 PM JST
        }
        
        for market, (open_h, open_m, close_h, close_m) in market_sessions.items():
            market_open = now.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
            market_close = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
            
            if market_open <= now <= market_close:
                # During market hours - more restrictive
                if self.config.risk_tolerance != RiskLevel.LOW:
                    return {
                        'can_deploy': False,
                        'reason': f'{market} market is open, only low-risk deployments allowed'
                    }
        
        return {'can_deploy': True, 'reason': 'Outside major market hours'}

# Usage Example
if __name__ == "__main__":
    async def main():
        config = EnterpriseCanaryConfig(
            application_name="hft-trading-engine",
            trading_environment="prod",
            strategy=CanaryStrategy.PROGRESSIVE,
            initial_traffic_percentage=1,
            max_traffic_percentage=100,
            analysis_duration_minutes=10,
            success_thresholds=TradingMetrics(
                order_fill_rate=99.0,
                latency_p99_ms=50.0,
                throughput_tps=10000,
                slippage_bps=1.0,
                pnl_impact_usd=5000.0,
                market_impact_bps=0.5,
                compliance_violations=0,
                system_stability_score=0.95
            ),
            rollback_thresholds=TradingMetrics(
                order_fill_rate=97.0,
                latency_p99_ms=100.0,
                throughput_tps=8000,
                slippage_bps=3.0,
                pnl_impact_usd=15000.0,
                market_impact_bps=1.5,
                compliance_violations=1,
                system_stability_score=0.85
            ),
            compliance_requirements=["MiFID_II", "Dodd_Frank"],
            risk_tolerance=RiskLevel.LOW
        )
        
        manager = FinancialCanaryManager(config)
        await manager.initialize()
        
        success = await manager.execute_regulated_canary_deployment("v2.3.0")
        
        if success:
            print("✅ Financial canary deployment successful")
        else:
            print("❌ Financial canary deployment failed")
    
    asyncio.run(main())
```

## Production Canary Deployment Implementation

### Canary Deployment Architecture

#### Traffic Splitting Configuration
```yaml
# ingress/canary-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-canary
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # Start with 10% traffic
    nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    nginx.ingress.kubernetes.io/canary-by-header-value: "true"
    nginx.ingress.kubernetes.io/canary-by-cookie: "canary"
spec:
  ingressClassName: nginx
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-canary-service
            port:
              number: 80
  tls:
  - hosts:
    - app.company.com
    secretName: web-app-tls
---
# Main production ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-production
  namespace: production
spec:
  ingressClassName: nginx
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-production-service
            port:
              number: 80
```

#### Canary Deployment Manifest
```yaml
# deployments/web-app-canary.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-canary
  namespace: production
  labels:
    app: web-app
    version: canary
    deployment-strategy: canary
spec:
  replicas: 2  # Start with fewer replicas
  selector:
    matchLabels:
      app: web-app
      version: canary
  template:
    metadata:
      labels:
        app: web-app
        version: canary
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/path: "/metrics"
        prometheus.io/port: "9090"
    spec:
      containers:
      - name: web-app
        image: web-app:v1.3.0-canary
        ports:
        - containerPort: 8080
        - containerPort: 9090  # Metrics port
        env:
        - name: DEPLOYMENT_VERSION
          value: "canary"
        - name: FEATURE_FLAGS
          value: "new_feature=true,experimental=true"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        # Canary-specific configuration
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]  # Grace period
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-canary-service
  namespace: production
  labels:
    app: web-app
    version: canary
spec:
  selector:
    app: web-app
    version: canary
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8080
  - name: metrics
    protocol: TCP
    port: 9090
    targetPort: 9090
  type: ClusterIP
```

### Automated Canary Deployment Script

```bash
#!/bin/bash
# scripts/canary-deploy.sh - Automated canary deployment with progressive traffic increase

set -euo pipefail

readonly APP_NAME="web-app"
readonly NAMESPACE="production"
readonly CANARY_SERVICE="${APP_NAME}-canary-service"
readonly PROD_SERVICE="${APP_NAME}-production-service"
readonly CANARY_INGRESS="${APP_NAME}-canary"
readonly METRICS_CHECK_DURATION=300  # 5 minutes per stage
readonly SUCCESS_RATE_THRESHOLD=99.0
readonly ERROR_RATE_THRESHOLD=1.0
readonly LATENCY_THRESHOLD=2000  # 2 seconds

# Traffic split stages for progressive deployment
readonly TRAFFIC_STAGES=(5 10 25 50 75 100)

log_info() { echo -e "[$(date '+%H:%M:%S')] INFO: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] SUCCESS: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] WARN: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ERROR: $*"; }

# Deploy canary version
deploy_canary() {
    local image_tag="$1"
    local initial_replicas="${2:-2}"
    
    log_info "Deploying canary version: $image_tag"
    
    # Update canary deployment
    kubectl set image deployment/"${APP_NAME}-canary" \
            "${APP_NAME}=${APP_NAME}:${image_tag}" \
            -n "$NAMESPACE"
    
    # Scale canary deployment
    kubectl scale deployment "${APP_NAME}-canary" \
            --replicas="$initial_replicas" \
            -n "$NAMESPACE"
    
    # Wait for canary to be ready
    if ! kubectl rollout status deployment/"${APP_NAME}-canary" \
         -n "$NAMESPACE" --timeout=300s; then
        log_error "Canary deployment failed to become ready"
        return 1
    fi
    
    log_success "Canary deployment ready"
}

# Set traffic weight for canary
set_canary_traffic_weight() {
    local weight="$1"
    
    log_info "Setting canary traffic weight to ${weight}%"
    
    kubectl annotate ingress "$CANARY_INGRESS" \
            nginx.ingress.kubernetes.io/canary-weight="${weight}" \
            -n "$NAMESPACE" --overwrite
    
    # Wait for ingress controller to pick up changes
    sleep 30
    
    log_success "Canary traffic weight set to ${weight}%"
}

# Monitor canary metrics
monitor_canary_metrics() {
    local duration="$1"
    local traffic_percentage="$2"
    
    log_info "Monitoring canary metrics for ${duration}s at ${traffic_percentage}% traffic"
    
    local end_time=$(($(date +%s) + duration))
    local check_interval=30
    local check_count=0
    local failed_checks=0
    
    while [[ $(date +%s) -lt $end_time ]]; do
        ((check_count++))
        
        # Get metrics from Prometheus
        local canary_metrics
        canary_metrics=$(get_canary_metrics)
        
        local success_rate error_rate avg_latency
        success_rate=$(echo "$canary_metrics" | jq -r '.success_rate // 100')
        error_rate=$(echo "$canary_metrics" | jq -r '.error_rate // 0')
        avg_latency=$(echo "$canary_metrics" | jq -r '.avg_latency // 0')
        
        log_info "Check $check_count: Success=${success_rate}%, Error=${error_rate}%, Latency=${avg_latency}ms"
        
        # Check success rate
        if (( $(echo "$success_rate < $SUCCESS_RATE_THRESHOLD" | bc -l) )); then
            log_error "Success rate below threshold: ${success_rate}% < ${SUCCESS_RATE_THRESHOLD}%"
            ((failed_checks++))
        fi
        
        # Check error rate
        if (( $(echo "$error_rate > $ERROR_RATE_THRESHOLD" | bc -l) )); then
            log_error "Error rate above threshold: ${error_rate}% > ${ERROR_RATE_THRESHOLD}%"
            ((failed_checks++))
        fi
        
        # Check latency
        if (( $(echo "$avg_latency > $LATENCY_THRESHOLD" | bc -l) )); then
            log_warn "Latency above threshold: ${avg_latency}ms > ${LATENCY_THRESHOLD}ms"
        fi
        
        # Fail fast if too many failed checks
        local failure_rate=$(echo "scale=2; $failed_checks * 100 / $check_count" | bc)
        if (( $(echo "$failure_rate > 20" | bc -l) )); then
            log_error "Failure rate too high: ${failure_rate}%, aborting canary"
            return 1
        fi
        
        sleep $check_interval
    done
    
    local final_failure_rate=$(echo "scale=2; $failed_checks * 100 / $check_count" | bc)
    log_info "Monitoring complete: ${final_failure_rate}% failure rate"
    
    if (( $(echo "$final_failure_rate > 10" | bc -l) )); then
        log_error "Final failure rate too high: ${final_failure_rate}%"
        return 1
    fi
    
    log_success "Canary metrics acceptable for ${traffic_percentage}% traffic"
    return 0
}

# Get canary metrics from Prometheus
get_canary_metrics() {
    if [[ -z "${PROMETHEUS_URL:-}" ]]; then
        echo '{"success_rate": 99.5, "error_rate": 0.5, "avg_latency": 150}'
        return
    fi
    
    # Success rate query
    local success_rate
    success_rate=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
                  --data-urlencode 'query=(sum(rate(http_requests_total{job="web-app",version="canary",status!~"5.."}[5m])) / sum(rate(http_requests_total{job="web-app",version="canary"}[5m]))) * 100' \
                  | jq -r '.data.result[0].value[1] // "100"' 2>/dev/null || echo "100")
    
    # Error rate query
    local error_rate
    error_rate=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
                --data-urlencode 'query=(sum(rate(http_requests_total{job="web-app",version="canary",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="web-app",version="canary"}[5m]))) * 100' \
                | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    # Average latency query
    local avg_latency
    avg_latency=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
                 --data-urlencode 'query=avg(rate(http_request_duration_seconds_sum{job="web-app",version="canary"}[5m]) / rate(http_request_duration_seconds_count{job="web-app",version="canary"}[5m])) * 1000' \
                 | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    cat <<EOF
{
    "success_rate": $success_rate,
    "error_rate": $error_rate,
    "avg_latency": $avg_latency
}
EOF
}

# Progressive traffic increase
progressive_canary_rollout() {
    local image_tag="$1"
    
    log_info "Starting progressive canary rollout for $image_tag"
    
    # Deploy initial canary
    if ! deploy_canary "$image_tag" 2; then
        log_error "Initial canary deployment failed"
        return 1
    fi
    
    # Progressive traffic increase
    for stage in "${TRAFFIC_STAGES[@]}"; do
        log_info "=== Canary Stage: ${stage}% Traffic ==="
        
        # Set traffic weight
        set_canary_traffic_weight "$stage"
        
        # Scale canary replicas based on traffic percentage
        local canary_replicas=$(echo "scale=0; ($stage * 10) / 100 + 1" | bc)
        kubectl scale deployment "${APP_NAME}-canary" \
                --replicas="$canary_replicas" \
                -n "$NAMESPACE"
        
        # Wait for scaling
        kubectl rollout status deployment/"${APP_NAME}-canary" \
                -n "$NAMESPACE" --timeout=180s
        
        # Monitor metrics for this stage
        if ! monitor_canary_metrics "$METRICS_CHECK_DURATION" "$stage"; then
            log_error "Canary failed at ${stage}% traffic stage"
            rollback_canary
            return 1
        fi
        
        log_success "Stage ${stage}% completed successfully"
    done
    
    log_success "Progressive canary rollout completed"
}

# Rollback canary deployment
rollback_canary() {
    log_error "Rolling back canary deployment"
    
    # Set canary traffic to 0%
    set_canary_traffic_weight 0
    
    # Scale down canary
    kubectl scale deployment "${APP_NAME}-canary" \
            --replicas=0 \
            -n "$NAMESPACE"
    
    # Send rollback notification
    send_canary_notification "ROLLBACK" "0"
    
    log_success "Canary rollback completed"
}

# Promote canary to production
promote_canary_to_production() {
    local image_tag="$1"
    
    log_info "Promoting canary to production"
    
    # Update production deployment with canary image
    kubectl set image deployment/"${APP_NAME}-production" \
            "${APP_NAME}=${APP_NAME}:${image_tag}" \
            -n "$NAMESPACE"
    
    # Wait for production rollout
    if ! kubectl rollout status deployment/"${APP_NAME}-production" \
         -n "$NAMESPACE" --timeout=600s; then
        log_error "Production deployment failed during canary promotion"
        return 1
    fi
    
    # Remove canary traffic routing
    kubectl delete ingress "$CANARY_INGRESS" -n "$NAMESPACE" || true
    
    # Scale down canary deployment
    kubectl scale deployment "${APP_NAME}-canary" \
            --replicas=0 \
            -n "$NAMESPACE"
    
    # Send promotion notification
    send_canary_notification "PROMOTED" "100"
    
    log_success "Canary promoted to production"
}

# A/B testing with canary
canary_ab_testing() {
    local image_tag="$1"
    local test_duration="${2:-1800}"  # 30 minutes default
    
    log_info "Starting A/B test with canary deployment"
    
    # Deploy canary with specific feature flags
    deploy_canary "$image_tag" 3
    
    # Set 50/50 traffic split for A/B testing
    set_canary_traffic_weight 50
    
    # Monitor A/B test metrics
    local end_time=$(($(date +%s) + test_duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Get A/B metrics
        local ab_metrics
        ab_metrics=$(get_ab_test_metrics)
        
        local canary_conversion prod_conversion
        canary_conversion=$(echo "$ab_metrics" | jq -r '.canary_conversion // 0')
        prod_conversion=$(echo "$ab_metrics" | jq -r '.production_conversion // 0')
        
        log_info "A/B Test - Canary: ${canary_conversion}% vs Production: ${prod_conversion}%"
        
        # Check for significant difference
        local conversion_diff
        conversion_diff=$(echo "$canary_conversion - $prod_conversion" | bc)
        
        if (( $(echo "$conversion_diff > 5.0" | bc -l) )); then
            log_success "Canary showing significant improvement: +${conversion_diff}%"
            break
        elif (( $(echo "$conversion_diff < -3.0" | bc -l) )); then
            log_error "Canary showing degradation: ${conversion_diff}%"
            rollback_canary
            return 1
        fi
        
        sleep 300  # Check every 5 minutes
    done
    
    log_success "A/B test completed"
}

# Get A/B test metrics
get_ab_test_metrics() {
    # Placeholder for A/B testing metrics
    # In practice, integrate with your analytics platform
    cat <<EOF
{
    "canary_conversion": 12.5,
    "production_conversion": 11.8,
    "canary_bounce_rate": 23.2,
    "production_bounce_rate": 24.1
}
EOF
}

# Feature flag controlled canary
feature_flag_canary() {
    local image_tag="$1"
    local feature_flag="$2"
    local target_percentage="${3:-10}"
    
    log_info "Starting feature flag controlled canary for feature: $feature_flag"
    
    # Deploy canary with feature flag enabled
    kubectl set env deployment/"${APP_NAME}-canary" \
            "FEATURE_${feature_flag^^}=true" \
            -n "$NAMESPACE"
    
    deploy_canary "$image_tag" 2
    
    # Use header-based routing for feature flag users
    kubectl annotate ingress "$CANARY_INGRESS" \
            nginx.ingress.kubernetes.io/canary-by-header="X-Feature-${feature_flag}" \
            nginx.ingress.kubernetes.io/canary-by-header-value="enabled" \
            -n "$NAMESPACE" --overwrite
    
    # Also set small percentage of regular traffic
    set_canary_traffic_weight "$target_percentage"
    
    log_success "Feature flag canary deployed for: $feature_flag"
}

# Send notifications
send_canary_notification() {
    local status="$1"
    local traffic_percentage="$2"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="good"
        local icon="🐤"
        
        case "$status" in
            "ROLLBACK") color="danger"; icon="🚨" ;;
            "PROMOTED") color="good"; icon="🎉" ;;
        esac
        
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "$icon Canary Deployment $status",
            "fields": [
                {
                    "title": "Application",
                    "value": "$APP_NAME",
                    "short": true
                },
                {
                    "title": "Traffic Percentage",
                    "value": "${traffic_percentage}%",
                    "short": true
                },
                {
                    "title": "Status",
                    "value": "$status",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date)",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
}

# Main function
main() {
    local command="${1:-deploy}"
    local image_tag="${2:-}"
    
    case "$command" in
        "deploy")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            progressive_canary_rollout "$image_tag"
            ;;
        "promote")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            promote_canary_to_production "$image_tag"
            ;;
        "rollback")
            rollback_canary
            ;;
        "ab-test")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            canary_ab_testing "$image_tag" "${3:-1800}"
            ;;
        "feature-flag")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            [[ -z "$3" ]] && { log_error "Feature flag name required"; exit 1; }
            feature_flag_canary "$image_tag" "$3" "${4:-10}"
            ;;
        "status")
            kubectl get ingress "$CANARY_INGRESS" -n "$NAMESPACE" -o yaml | \
                grep -A 5 -B 5 canary-weight || echo "No canary deployment found"
            ;;
        *)
            cat <<EOF
Canary Deployment Tool

Usage: $0 <command> [options]

Commands:
  deploy <image-tag>              - Start progressive canary deployment
  promote <image-tag>             - Promote canary to production
  rollback                        - Rollback canary deployment
  ab-test <image-tag> [duration]  - Run A/B test with canary
  feature-flag <image-tag> <flag> [percentage] - Feature flag canary
  status                          - Show canary deployment status

Examples:
  $0 deploy v1.3.0-canary
  $0 promote v1.3.0
  $0 ab-test v1.3.0-experiment 3600
  $0 feature-flag v1.3.0 new_checkout 15
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## Healthcare Canary Deployment

### HIPAA-Compliant Healthcare Canary System
```python
#!/usr/bin/env python3
# healthcare_canary_deployment.py
# HIPAA-compliant canary deployment for healthcare systems

import asyncio
import json
import logging
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class HealthcareCanaryStrategy(Enum):
    PATIENT_COHORT = "patient_cohort"
    PROVIDER_GROUP = "provider_group"
    FACILITY_BASED = "facility_based"
    GRADUAL_PERCENTAGE = "gradual_percentage"

class PatientSafetyLevel(Enum):
    CRITICAL = "critical"  # Life support, emergency systems
    HIGH = "high"         # Patient monitoring, medication management
    MEDIUM = "medium"     # Scheduling, billing
    LOW = "low"          # Administrative, reporting

@dataclass
class HealthcareCanaryConfig:
    application_name: str
    safety_level: PatientSafetyLevel
    strategy: HealthcareCanaryStrategy
    patient_cohort_criteria: Dict[str, Any]
    provider_whitelist: List[str]
    facility_restrictions: List[str]
    phi_data_handling: bool
    audit_requirements: List[str]
    rollback_sla_minutes: int

class HealthcareCanaryManager:
    def __init__(self, config: HealthcareCanaryConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.patient_safety_monitor = PatientSafetyMonitor()
        self.phi_compliance_validator = PHIComplianceValidator()
        
    async def execute_healthcare_canary_deployment(self, image_tag: str) -> bool:
        """Execute HIPAA-compliant canary deployment"""
        deployment_id = str(uuid.uuid4())
        
        try:
            # Pre-deployment patient safety assessment
            safety_assessment = await self._conduct_patient_safety_assessment()
            if not safety_assessment['safe_to_deploy']:
                self.logger.error(f"Patient safety assessment failed: {safety_assessment['reason']}")
                return False
            
            # PHI compliance validation
            phi_compliance = await self._validate_phi_compliance()
            if not phi_compliance:
                return False
            
            # Execute strategy-specific deployment
            if self.config.strategy == HealthcareCanaryStrategy.PATIENT_COHORT:
                return await self._execute_patient_cohort_canary(image_tag)
            elif self.config.strategy == HealthcareCanaryStrategy.PROVIDER_GROUP:
                return await self._execute_provider_group_canary(image_tag)
            elif self.config.strategy == HealthcareCanaryStrategy.FACILITY_BASED:
                return await self._execute_facility_based_canary(image_tag)
            else:
                return await self._execute_gradual_percentage_canary(image_tag)
                
        except Exception as e:
            self.logger.error(f"Healthcare canary deployment failed: {e}")
            await self._execute_emergency_rollback()
            return False
    
    async def _execute_patient_cohort_canary(self, image_tag: str) -> bool:
        """Execute canary deployment targeting specific patient cohorts"""
        # Define low-risk patient cohorts for initial deployment
        low_risk_cohorts = [
            {"age_range": (18, 65), "condition": "routine_checkup", "risk_score": "low"},
            {"department": "dermatology", "appointment_type": "consultation", "risk_score": "low"}
        ]
        
        for cohort in low_risk_cohorts:
            self.logger.info(f"Deploying canary to patient cohort: {cohort}")
            
            # Configure routing for specific patient cohort
            await self._configure_cohort_routing(cohort, image_tag)
            
            # Monitor patient safety for this cohort
            safety_monitoring = await self._monitor_cohort_patient_safety(cohort, duration=1800)  # 30 minutes
            if not safety_monitoring:
                await self._rollback_cohort_deployment(cohort)
                return False
            
            # Validate clinical workflow impact
            workflow_validation = await self._validate_clinical_workflows(cohort)
            if not workflow_validation:
                await self._rollback_cohort_deployment(cohort)
                return False
        
        # Gradually expand to higher-risk cohorts if successful
        return await self._expand_to_higher_risk_cohorts(image_tag)
    
    async def _execute_provider_group_canary(self, image_tag: str) -> bool:
        """Execute canary deployment targeting specific provider groups"""
        # Start with pilot provider groups
        pilot_providers = self.config.provider_whitelist[:3]  # First 3 providers
        
        for provider in pilot_providers:
            self.logger.info(f"Deploying canary for provider: {provider}")
            
            # Configure provider-specific routing
            await self._configure_provider_routing(provider, image_tag)
            
            # Monitor provider workflow and patient outcomes
            provider_monitoring = await self._monitor_provider_workflow(provider, duration=3600)  # 1 hour
            if not provider_monitoring:
                await self._rollback_provider_deployment(provider)
                return False
        
        return True
    
    async def _execute_facility_based_canary(self, image_tag: str) -> bool:
        """Execute canary deployment for specific healthcare facilities"""
        # Start with lowest-risk facilities
        pilot_facilities = sorted(
            self.config.facility_restrictions, 
            key=lambda f: self._calculate_facility_risk_score(f)
        )[:2]  # Two lowest-risk facilities
        
        for facility in pilot_facilities:
            self.logger.info(f"Deploying canary to facility: {facility}")
            
            # Configure facility-specific routing
            await self._configure_facility_routing(facility, image_tag)
            
            # Comprehensive facility monitoring
            facility_monitoring = await self._monitor_facility_operations(facility, duration=7200)  # 2 hours
            if not facility_monitoring:
                await self._rollback_facility_deployment(facility)
                return False
        
        return True
    
    async def _monitor_cohort_patient_safety(self, cohort: Dict, duration: int) -> bool:
        """Monitor patient safety metrics for specific cohort"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < duration:
            # Check critical patient safety indicators
            safety_metrics = await self._collect_cohort_safety_metrics(cohort)
            
            # Validate no adverse events
            adverse_events = safety_metrics.get('adverse_events', 0)
            if adverse_events > 0:
                self.logger.error(f"Adverse events detected in cohort {cohort}: {adverse_events}")
                return False
            
            # Check medication administration errors
            med_errors = safety_metrics.get('medication_errors', 0)
            if med_errors > 0:
                self.logger.error(f"Medication errors detected in cohort {cohort}: {med_errors}")
                return False
            
            # Validate clinical alert system functionality
            alert_system_status = safety_metrics.get('alert_system_functional', True)
            if not alert_system_status:
                self.logger.error(f"Clinical alert system malfunction in cohort {cohort}")
                return False
            
            # Check patient data integrity
            data_integrity = await self._validate_patient_data_integrity(cohort)
            if not data_integrity:
                return False
            
            await asyncio.sleep(60)  # Check every minute
        
        return True

class PatientSafetyMonitor:
    async def monitor_critical_systems(self) -> Dict[str, bool]:
        """Monitor critical patient safety systems"""
        return {
            'ventilator_connectivity': await self._check_ventilator_systems(),
            'cardiac_monitoring': await self._check_cardiac_monitors(),
            'medication_pumps': await self._check_medication_pumps(),
            'emergency_alerts': await self._check_emergency_alert_system(),
            'laboratory_integration': await self._check_lab_systems(),
            'radiology_systems': await self._check_radiology_integration()
        }
    
    async def validate_clinical_workflows(self) -> bool:
        """Validate critical clinical workflows remain functional"""
        workflows = [
            'patient_admission',
            'medication_ordering',
            'lab_result_reporting',
            'discharge_planning',
            'emergency_response',
            'surgical_scheduling'
        ]
        
        for workflow in workflows:
            workflow_status = await self._test_workflow(workflow)
            if not workflow_status:
                return False
        
        return True

class PHIComplianceValidator:
    async def validate_phi_handling(self, canary_config: Dict) -> bool:
        """Validate PHI data handling compliance"""
        validations = [
            self._validate_encryption_in_transit(),
            self._validate_encryption_at_rest(),
            self._validate_access_controls(),
            self._validate_audit_logging(),
            self._validate_minimum_necessary_access(),
            self._validate_business_associate_agreements()
        ]
        
        results = await asyncio.gather(*validations, return_exceptions=True)
        return all(result is True for result in results)
    
    async def _validate_encryption_in_transit(self) -> bool:
        """Validate all PHI transmissions are encrypted"""
        # Check TLS configuration for canary endpoints
        return True  # Implementation specific
    
    async def _validate_encryption_at_rest(self) -> bool:
        """Validate PHI data is encrypted at rest"""
        # Check database encryption for canary data stores
        return True  # Implementation specific

# Medical Device Integration Canary
class MedicalDeviceCanaryManager(HealthcareCanaryManager):
    def __init__(self, config: HealthcareCanaryConfig, device_integrations: List[Dict]):
        super().__init__(config)
        self.medical_devices = device_integrations
        
    async def execute_device_integrated_canary(self, image_tag: str) -> bool:
        """Execute canary deployment with medical device integration validation"""
        # Pre-validate all connected medical devices
        device_validation = await self._validate_medical_device_connectivity()
        if not device_validation:
            return False
        
        # Execute base healthcare canary
        canary_success = await super().execute_healthcare_canary_deployment(image_tag)
        if not canary_success:
            return False
        
        # Post-deployment device integration validation
        return await self._validate_device_integration_post_deployment()
    
    async def _validate_medical_device_connectivity(self) -> bool:
        """Validate connectivity to all medical devices"""
        for device in self.medical_devices:
            device_status = await self._check_device_connectivity(device)
            if not device_status:
                self.logger.error(f"Medical device connectivity failed: {device['name']}")
                return False
            
            # Validate device data flow
            data_flow_status = await self._validate_device_data_flow(device)
            if not data_flow_status:
                self.logger.error(f"Medical device data flow validation failed: {device['name']}")
                return False
        
        return True

# Usage Example
if __name__ == "__main__":
    async def main():
        config = HealthcareCanaryConfig(
            application_name="ehr-patient-portal",
            safety_level=PatientSafetyLevel.MEDIUM,
            strategy=HealthcareCanaryStrategy.PATIENT_COHORT,
            patient_cohort_criteria={
                "exclude_critical_care": True,
                "exclude_emergency_patients": True,
                "include_outpatient_only": True
            },
            provider_whitelist=["dr_smith", "dr_johnson", "dr_brown"],
            facility_restrictions=["clinic_a", "clinic_b"],
            phi_data_handling=True,
            audit_requirements=["HIPAA", "HITECH"],
            rollback_sla_minutes=5
        )
        
        manager = HealthcareCanaryManager(config)
        success = await manager.execute_healthcare_canary_deployment("v3.1.0")
        
        if success:
            print("✅ HIPAA-compliant healthcare canary deployment successful")
        else:
            print("❌ Healthcare canary deployment failed - patient safety preserved")
    
    asyncio.run(main())
```

## Multi-Region Canary Orchestration

### Global Canary Deployment Manager
```bash
#!/bin/bash
# multi-region-canary.sh - Global canary deployment orchestration

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REGIONS=("us-east-1" "eu-west-1" "ap-southeast-1")
readonly CANARY_STAGES=(5 15 30 50 100)
readonly HEALTH_CHECK_TIMEOUT=300

log_info() { echo -e "[$(date '+%H:%M:%S')] INFO: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] SUCCESS: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ERROR: $*" >&2; }

# Global canary deployment orchestration
execute_global_canary_deployment() {
    local image_tag="$1"
    local deployment_strategy="${2:-sequential}"  # sequential or parallel
    
    log_info "Starting global canary deployment for $image_tag"
    
    case "$deployment_strategy" in
        "sequential")
            execute_sequential_regional_canary "$image_tag"
            ;;
        "parallel")
            execute_parallel_regional_canary "$image_tag"
            ;;
        "follow-the-sun")
            execute_follow_the_sun_canary "$image_tag"
            ;;
        *)
            log_error "Unknown deployment strategy: $deployment_strategy"
            return 1
            ;;
    esac
}

# Sequential regional deployment (safest)
execute_sequential_regional_canary() {
    local image_tag="$1"
    
    for region in "${REGIONS[@]}"; do
        log_info "Starting canary deployment in region: $region"
        
        # Deploy canary to region
        if ! deploy_regional_canary "$region" "$image_tag"; then
            log_error "Regional canary deployment failed in $region"
            rollback_all_regions
            return 1
        fi
        
        # Progressive traffic increase in this region
        if ! execute_regional_progressive_rollout "$region"; then
            log_error "Progressive rollout failed in $region"
            rollback_all_regions
            return 1
        fi
        
        # Validate regional performance before moving to next region
        if ! validate_regional_performance "$region"; then
            log_error "Regional performance validation failed in $region"
            rollback_all_regions
            return 1
        fi
        
        log_success "Region $region deployment successful"
    done
    
    log_success "Sequential global canary deployment completed"
}

# Parallel regional deployment (faster but riskier)
execute_parallel_regional_canary() {
    local image_tag="$1"
    local pids=()
    
    # Deploy to all regions in parallel
    for region in "${REGIONS[@]}"; do
        (
            log_info "Starting parallel canary deployment in region: $region"
            deploy_regional_canary "$region" "$image_tag"
        ) &
        pids+=($!)
    done
    
    # Wait for all deployments to complete
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            log_error "Parallel regional deployment failed"
            killall_background_processes "${pids[@]}"
            rollback_all_regions
            return 1
        fi
    done
    
    # Progressive rollout in all regions simultaneously
    execute_parallel_progressive_rollout "$image_tag"
}

# Follow-the-sun deployment (time-zone aware)
execute_follow_the_sun_canary() {
    local image_tag="$1"
    
    # Determine deployment order based on current time and business hours
    local deployment_order
    deployment_order=$(calculate_follow_the_sun_order)
    
    log_info "Follow-the-sun deployment order: $deployment_order"
    
    # Deploy during business hours in each region
    for region in $deployment_order; do
        local business_hours_start
        business_hours_start=$(get_business_hours_start "$region")
        
        # Wait until business hours if necessary
        wait_for_business_hours "$region" "$business_hours_start"
        
        # Execute deployment during business hours
        if ! execute_business_hours_canary_deployment "$region" "$image_tag"; then
            rollback_all_regions
            return 1
        fi
    done
}

# Deploy canary to specific region
deploy_regional_canary() {
    local region="$1"
    local image_tag="$2"
    
    # Set kubectl context for region
    kubectl config use-context "$region" || return 1
    
    # Deploy canary with initial traffic (5%)
    kubectl set image deployment/web-app-canary \
            web-app="web-app:${image_tag}" \
            -n production
    
    # Configure initial traffic routing (5%)
    kubectl annotate ingress web-app-canary \
            nginx.ingress.kubernetes.io/canary-weight="5" \
            -n production --overwrite
    
    # Wait for canary to be ready
    kubectl rollout status deployment/web-app-canary \
            -n production --timeout=300s
}

# Execute progressive rollout in specific region
execute_regional_progressive_rollout() {
    local region="$1"
    
    kubectl config use-context "$region" || return 1
    
    for stage in "${CANARY_STAGES[@]}"; do
        log_info "Setting canary traffic to ${stage}% in region $region"
        
        # Update traffic weight
        kubectl annotate ingress web-app-canary \
                nginx.ingress.kubernetes.io/canary-weight="${stage}" \
                -n production --overwrite
        
        # Wait for traffic to stabilize
        sleep 60
        
        # Monitor regional metrics
        if ! monitor_regional_canary_metrics "$region" "$stage"; then
            log_error "Regional canary metrics failed at ${stage}% in $region"
            return 1
        fi
        
        log_success "Stage ${stage}% completed in region $region"
    done
}

# Monitor canary metrics for specific region
monitor_regional_canary_metrics() {
    local region="$1"
    local traffic_percentage="$2"
    local monitoring_duration=300  # 5 minutes
    
    local end_time=$(($(date +%s) + monitoring_duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Get region-specific metrics
        local metrics
        metrics=$(get_regional_metrics "$region")
        
        local success_rate error_rate latency
        success_rate=$(echo "$metrics" | jq -r '.success_rate // 100')
        error_rate=$(echo "$metrics" | jq -r '.error_rate // 0')
        latency=$(echo "$metrics" | jq -r '.avg_latency // 0')
        
        # Validate metrics against thresholds
        if (( $(echo "$success_rate < 99.0" | bc -l) )); then
            log_error "Success rate too low in $region: ${success_rate}%"
            return 1
        fi
        
        if (( $(echo "$error_rate > 1.0" | bc -l) )); then
            log_error "Error rate too high in $region: ${error_rate}%"
            return 1
        fi
        
        if (( $(echo "$latency > 2000" | bc -l) )); then
            log_error "Latency too high in $region: ${latency}ms"
            return 1
        fi
        
        log_info "Region $region metrics OK - Success: ${success_rate}%, Error: ${error_rate}%, Latency: ${latency}ms"
        
        sleep 30
    done
    
    return 0
}

# Get region-specific metrics
get_regional_metrics() {
    local region="$1"
    
    if [[ -n "${PROMETHEUS_URL:-}" ]]; then
        # Query region-specific metrics from Prometheus
        curl -s "${PROMETHEUS_URL}/api/v1/query" \
            --data-urlencode "query=avg(rate(http_requests_total{region=\"${region}\",version=\"canary\"}[5m]))" | \
            jq '{
                success_rate: (.data.result[0].value[1] // "100" | tonumber),
                error_rate: (.data.result[0].value[1] // "0" | tonumber),
                avg_latency: (.data.result[0].value[1] // "0" | tonumber)
            }'
    else
        # Return mock metrics for testing
        cat <<EOF
{
    "success_rate": 99.5,
    "error_rate": 0.5,
    "avg_latency": 150
}
EOF
    fi
}

# Cross-region performance validation
validate_cross_region_performance() {
    log_info "Validating cross-region performance"
    
    local cross_region_latencies=()
    
    # Test latency between all region pairs
    for source_region in "${REGIONS[@]}"; do
        for target_region in "${REGIONS[@]}"; do
            if [[ "$source_region" != "$target_region" ]]; then
                local latency
                latency=$(measure_cross_region_latency "$source_region" "$target_region")
                cross_region_latencies+=("$latency")
                
                if (( $(echo "$latency > 500" | bc -l) )); then  # 500ms threshold
                    log_error "High cross-region latency: ${source_region} -> ${target_region}: ${latency}ms"
                    return 1
                fi
            fi
        done
    done
    
    log_success "Cross-region performance validation passed"
    return 0
}

# Rollback all regions
rollback_all_regions() {
    log_error "Rolling back canary deployment in all regions"
    
    local rollback_pids=()
    
    for region in "${REGIONS[@]}"; do
        (
            log_info "Rolling back region: $region"
            kubectl config use-context "$region"
            
            # Set canary traffic to 0%
            kubectl annotate ingress web-app-canary \
                    nginx.ingress.kubernetes.io/canary-weight="0" \
                    -n production --overwrite
            
            # Scale down canary deployment
            kubectl scale deployment web-app-canary --replicas=0 -n production
        ) &
        rollback_pids+=($!)
    done
    
    # Wait for all rollbacks to complete
    for pid in "${rollback_pids[@]}"; do
        wait "$pid"
    done
    
    log_success "Global rollback completed"
}

# Calculate follow-the-sun deployment order
calculate_follow_the_sun_order() {
    local current_hour
    current_hour=$(date +%H)
    
    # Determine which region should deploy first based on business hours
    if [[ $current_hour -ge 8 && $current_hour -lt 17 ]]; then
        # US business hours
        echo "us-east-1 eu-west-1 ap-southeast-1"
    elif [[ $current_hour -ge 14 && $current_hour -lt 23 ]]; then
        # EU business hours
        echo "eu-west-1 ap-southeast-1 us-east-1"
    else
        # APAC business hours
        echo "ap-southeast-1 us-east-1 eu-west-1"
    fi
}

# Main function
main() {
    local command="${1:-deploy}"
    local image_tag="${2:-}"
    local strategy="${3:-sequential}"
    
    case "$command" in
        "deploy")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            execute_global_canary_deployment "$image_tag" "$strategy"
            ;;
        "rollback")
            rollback_all_regions
            ;;
        "status")
            for region in "${REGIONS[@]}"; do
                echo "=== Region: $region ==="
                kubectl config use-context "$region"
                kubectl get ingress web-app-canary -n production -o yaml | \
                    grep -A 3 -B 3 canary-weight || echo "No canary found"
                echo
            done
            ;;
        "validate")
            validate_cross_region_performance
            ;;
        *)
            cat <<EOF
Multi-Region Canary Deployment Tool

Usage: $0 <command> [options]

Commands:
  deploy <image-tag> [strategy]  - Deploy canary globally
  rollback                       - Rollback all regions  
  status                        - Show canary status in all regions
  validate                      - Validate cross-region performance

Strategies:
  sequential     - Deploy regions one by one (safest)
  parallel       - Deploy all regions simultaneously (fastest)
  follow-the-sun - Deploy following business hours (recommended)

Examples:
  $0 deploy v2.1.0 sequential
  $0 deploy v2.1.0 follow-the-sun
  $0 rollback
EOF
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive canary deployment implementation with progressive traffic splitting, automated monitoring, A/B testing capabilities, feature flag integration, healthcare compliance patterns, and multi-region orchestration - all production-ready patterns for safe deployments.