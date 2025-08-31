# CICD Container Workflows

Advanced containerization pipeline patterns, multi-stage container builds, security scanning, and orchestrated container deployment workflows.

## Table of Contents
1. [Container Pipeline Architecture](#container-pipeline-architecture)
2. [Multi-Stage Container Builds](#multi-stage-container-builds)
3. [Container Security Integration](#container-security-integration)
4. [Container Registry Management](#container-registry-management)
5. [Container Orchestration Pipelines](#container-orchestration-pipelines)
6. [Container Testing Strategies](#container-testing-strategies)
7. [Container Deployment Patterns](#container-deployment-patterns)
8. [Advanced Container Workflows](#advanced-container-workflows)

## Container Pipeline Architecture

### Enterprise Container Pipeline Framework
```yaml
container_pipeline_architecture:
  build_strategies:
    multi_stage_builds:
      base_images:
        - distroless: ["gcr.io/distroless/java", "gcr.io/distroless/nodejs"]
        - alpine: ["alpine:3.18", "node:18-alpine", "openjdk:11-alpine"]
        - ubuntu: ["ubuntu:22.04", "ubuntu:20.04"]
        - custom: ["company/base-java:v1.0", "company/base-nodejs:v2.1"]
      
      optimization_techniques:
        - layer_caching
        - multi_architecture_builds
        - build_cache_mounts
        - dependency_caching
        - parallel_stage_execution
      
      security_practices:
        - non_root_user_execution
        - minimal_attack_surface
        - secrets_management
        - vulnerability_scanning
        - runtime_security
    
    build_matrix:
      architectures: ["amd64", "arm64", "arm/v7"]
      platforms: ["linux", "windows"]
      variants:
        - production: "optimized, minimal"
        - development: "debug_symbols, dev_tools"
        - testing: "test_frameworks, coverage_tools"
    
    optimization_patterns:
      layer_optimization:
        - dependency_installation_first
        - source_code_last
        - static_content_caching
        - build_artifact_separation
      
      size_optimization:
        - multi_stage_builds
        - unused_package_removal
        - temporary_file_cleanup
        - compression_optimization
      
      security_hardening:
        - minimal_base_images
        - vulnerability_free_dependencies
        - secure_defaults
        - runtime_protection

  registry_integration:
    multi_registry_strategy:
      primary_registry:
        type: "harbor"
        url: "registry.company.com"
        features: ["vulnerability_scanning", "image_signing", "policy_enforcement"]
        retention_policies:
          development: "30d"
          staging: "90d"
          production: "1y"
      
      secondary_registries:
        - type: "aws_ecr"
          region: "us-west-2"
          cross_region_replication: true
          lifecycle_policies: true
        
        - type: "gcr"
          project: "production-project"
          vulnerability_scanning: true
          binary_authorization: true
        
        - type: "azure_acr"
          location: "westus2"
          geo_replication: ["eastus", "westeurope"]
          content_trust: true
    
    image_promotion:
      environments:
        development:
          registry: "registry.company.com/dev"
          tags: ["branch-name", "commit-sha", "latest"]
          scan_required: false
          signing_required: false
        
        staging:
          registry: "registry.company.com/staging"
          tags: ["version", "commit-sha"]
          scan_required: true
          signing_required: false
          promotion_criteria:
            - security_scan_passed
            - unit_tests_passed
            - integration_tests_passed
        
        production:
          registry: "registry.company.com/prod"
          tags: ["version", "latest", "stable"]
          scan_required: true
          signing_required: true
          promotion_criteria:
            - all_tests_passed
            - security_approved
            - signed_by_release_team
            - compliance_validated

  container_testing:
    test_layers:
      unit_tests:
        - dockerfile_linting
        - security_policy_validation
        - build_optimization_analysis
        - layer_analysis
      
      integration_tests:
        - container_startup_tests
        - health_check_validation
        - service_communication_tests
        - resource_consumption_tests
      
      security_tests:
        - vulnerability_scanning
        - malware_detection
        - secrets_scanning
        - compliance_validation
      
      performance_tests:
        - startup_time_benchmarks
        - memory_usage_profiling
        - cpu_utilization_testing
        - network_performance_testing

  deployment_orchestration:
    kubernetes_integration:
      deployment_strategies:
        - rolling_updates
        - blue_green_deployments
        - canary_releases
        - a_b_testing
      
      resource_management:
        - resource_quotas
        - limit_ranges
        - horizontal_pod_autoscaling
        - vertical_pod_autoscaling
      
      security_contexts:
        - pod_security_policies
        - security_contexts
        - network_policies
        - admission_controllers
    
    service_mesh_integration:
      istio:
        - traffic_management
        - security_policies
        - observability_configuration
        - chaos_engineering
      
      linkerd:
        - automatic_tls
        - load_balancing
        - circuit_breakers
        - retry_policies
```

### Advanced Docker Multi-Stage Pipeline
```dockerfile
# Advanced multi-stage Dockerfile with optimization
# Stage 1: Base dependency cache
FROM node:18-alpine AS dependency-cache
WORKDIR /app

# Copy package files for dependency caching
COPY package*.json yarn.lock* ./
COPY packages/*/package.json ./packages/

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=cache,target=/root/.yarn \
    if [ -f yarn.lock ]; then \
        yarn install --frozen-lockfile --network-timeout 600000; \
    else \
        npm ci --only=production --no-audit --no-fund; \
    fi

# Stage 2: Development environment
FROM dependency-cache AS development
ENV NODE_ENV=development

# Install development dependencies
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=cache,target=/root/.yarn \
    if [ -f yarn.lock ]; then \
        yarn install --frozen-lockfile --network-timeout 600000; \
    else \
        npm install --no-audit --no-fund; \
    fi

# Copy source code
COPY . .

# Development server
EXPOSE 3000 9229
CMD ["npm", "run", "dev"]

# Stage 3: Build stage
FROM dependency-cache AS builder
ENV NODE_ENV=production

# Install build dependencies
COPY . .

# Build application with cache mount
RUN --mount=type=cache,target=/tmp \
    npm run build && \
    npm run test:unit && \
    npm audit --production --audit-level=high

# Stage 4: Security scanning stage
FROM builder AS security-scan

# Install security scanning tools
RUN apk add --no-cache \
    curl \
    jq

# Run security scans
RUN npm audit --audit-level=moderate || true
COPY scripts/security-check.sh /security-check.sh
RUN chmod +x /security-check.sh && /security-check.sh

# Stage 5: Production runtime
FROM gcr.io/distroless/nodejs18-debian11 AS production

# Metadata labels
LABEL maintainer="platform-team@company.com" \
      version="1.0.0" \
      description="Production Node.js application" \
      security.scan.date="$(date -Iseconds)" \
      org.opencontainers.image.source="https://github.com/company/app" \
      org.opencontainers.image.documentation="https://docs.company.com/app" \
      org.opencontainers.image.vendor="Company Inc." \
      org.opencontainers.image.licenses="MIT"

# Create non-root user
WORKDIR /app

# Copy production dependencies and built application
COPY --from=dependency-cache --chown=nonroot:nonroot /app/node_modules ./node_modules
COPY --from=builder --chown=nonroot:nonroot /app/dist ./dist
COPY --from=builder --chown=nonroot:nonroot /app/package.json ./

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["/nodejs/bin/node", "dist/healthcheck.js"]

# Runtime configuration
EXPOSE 8080
USER nonroot

# Production startup
CMD ["/nodejs/bin/node", "dist/server.js"]

# Stage 6: Testing runtime
FROM node:18-alpine AS testing
WORKDIR /app

# Copy built application and test dependencies
COPY --from=builder /app .
COPY --from=dependency-cache /app/node_modules ./node_modules

# Install testing tools
RUN npm install --only=dev --no-audit --no-fund

# Test environment setup
ENV NODE_ENV=test
EXPOSE 3001

CMD ["npm", "run", "test:integration"]
```

### Container Build Automation
```groovy
@Library(['container-shared-library']) _

pipeline {
    agent none
    
    parameters {
        choice(
            name: 'BUILD_TYPE',
            choices: ['development', 'staging', 'production', 'all'],
            description: 'Type of container build'
        )
        booleanParam(
            name: 'MULTI_ARCH_BUILD',
            defaultValue: true,
            description: 'Build for multiple architectures'
        )
        booleanParam(
            name: 'PUSH_TO_REGISTRY',
            defaultValue: true,
            description: 'Push images to registry'
        )
        string(
            name: 'CUSTOM_TAG',
            defaultValue: '',
            description: 'Custom tag for the build'
        )
        booleanParam(
            name: 'SECURITY_SCAN',
            defaultValue: true,
            description: 'Run security scans on images'
        )
    }
    
    environment {
        DOCKER_BUILDKIT = '1'
        BUILDX_NO_DEFAULT_ATTESTATIONS = '1'
        
        // Registry configuration
        PRIMARY_REGISTRY = 'registry.company.com'
        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"
        GCR_REGISTRY = 'gcr.io/production-project'
        
        // Build configuration
        IMAGE_NAME = "${env.JOB_NAME.split('/')[1]}"
        BUILD_VERSION = getBuildVersion()
        GIT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
        
        // Multi-architecture configuration
        PLATFORMS = params.MULTI_ARCH_BUILD ? 'linux/amd64,linux/arm64' : 'linux/amd64'
        
        // Security scanning
        TRIVY_DB_REPOSITORY = 'public.ecr.aws/aquasecurity/trivy-db'
        SNYK_TOKEN = credentials('snyk-token')
        
        // Signing configuration
        COSIGN_PRIVATE_KEY = credentials('cosign-private-key')
        COSIGN_PUBLIC_KEY = credentials('cosign-public-key')
    }
    
    stages {
        stage('Container Pipeline Initialization') {
            agent { label 'docker-builder' }
            steps {
                script {
                    // Setup Docker Buildx
                    sh '''
                        # Create and use buildx builder
                        docker buildx create --name container-builder --use --bootstrap
                        docker buildx inspect container-builder
                        
                        # Setup QEMU for multi-arch builds
                        if [ "${MULTI_ARCH_BUILD}" = "true" ]; then
                            docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
                        fi
                        
                        # Verify registry connectivity
                        docker login ${PRIMARY_REGISTRY} -u ${REGISTRY_USER} -p ${REGISTRY_PASSWORD}
                    '''
                    
                    // Initialize build context
                    containerBuilder.initialize([
                        buildType: params.BUILD_TYPE,
                        platforms: env.PLATFORMS,
                        imageName: env.IMAGE_NAME,
                        version: env.BUILD_VERSION
                    ])
                }
            }
        }
        
        stage('Dockerfile Analysis') {
            parallel {
                stage('Dockerfile Linting') {
                    agent { label 'dockerfile-linter' }
                    steps {
                        script {
                            // Dockerfile linting with hadolint
                            sh '''
                                hadolint Dockerfile --format json > hadolint-results.json || true
                                hadolint Dockerfile --format sarif > hadolint-results.sarif || true
                            '''
                            
                            dockerfileLinter.processResults([
                                jsonResults: readJSON(file: 'hadolint-results.json'),
                                sarifResults: 'hadolint-results.sarif'
                            ])
                            
                            archiveArtifacts artifacts: 'hadolint-results.*'
                        }
                    }
                }
                
                stage('Build Optimization Analysis') {
                    agent { label 'build-analyzer' }
                    steps {
                        script {
                            // Analyze Dockerfile for optimization opportunities
                            buildOptimizer.analyze([
                                dockerfile: 'Dockerfile',
                                buildContext: '.',
                                optimizationLevel: getBuildOptimizationLevel()
                            ])
                        }
                    }
                }
                
                stage('Security Policy Validation') {
                    agent { label 'policy-validator' }
                    steps {
                        script {
                            // Validate against security policies
                            securityPolicyValidator.validateDockerfile([
                                dockerfile: 'Dockerfile',
                                policies: getSecurityPolicies(),
                                enforcementLevel: 'warn'
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Multi-Stage Container Build') {
            agent { label 'docker-builder-large' }
            steps {
                script {
                    def buildStages = []
                    
                    if (params.BUILD_TYPE in ['development', 'all']) {
                        buildStages << [
                            name: 'development',
                            target: 'development',
                            tags: ["${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:dev-${env.BUILD_VERSION}"]
                        ]
                    }
                    
                    if (params.BUILD_TYPE in ['staging', 'all']) {
                        buildStages << [
                            name: 'staging',
                            target: 'production',
                            tags: [
                                "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:staging-${env.BUILD_VERSION}",
                                "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:staging-latest"
                            ]
                        ]
                    }
                    
                    if (params.BUILD_TYPE in ['production', 'all']) {
                        buildStages << [
                            name: 'production',
                            target: 'production',
                            tags: [
                                "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:${env.BUILD_VERSION}",
                                "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:latest"
                            ]
                        ]
                    }
                    
                    // Add testing stage
                    buildStages << [
                        name: 'testing',
                        target: 'testing',
                        tags: ["${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:test-${env.BUILD_VERSION}"]
                    ]
                    
                    // Build all stages in parallel
                    def parallelBuilds = [:]
                    buildStages.each { stage ->
                        parallelBuilds[stage.name] = {
                            buildContainerStage(stage)
                        }
                    }
                    
                    parallel parallelBuilds
                }
            }
        }
        
        stage('Container Security Scanning') {
            when { params.SECURITY_SCAN }
            parallel {
                stage('Vulnerability Scanning') {
                    agent { label 'security-scanner' }
                    steps {
                        script {
                            def imagesToScan = getBuiltImages()
                            
                            imagesToScan.each { image ->
                                // Trivy vulnerability scanning
                                sh """
                                    trivy image --format json --output trivy-${image.safeName}.json ${image.fullName}
                                    trivy image --format sarif --output trivy-${image.safeName}.sarif ${image.fullName}
                                """
                                
                                // Snyk container scanning
                                sh """
                                    snyk container test ${image.fullName} \
                                        --json-file-output=snyk-${image.safeName}.json \
                                        --severity-threshold=high || true
                                """
                                
                                // Process scan results
                                vulnerabilityScanner.processResults([
                                    image: image.fullName,
                                    trivyResults: readJSON(file: "trivy-${image.safeName}.json"),
                                    snykResults: readJSON(file: "snyk-${image.safeName}.json"),
                                    failOnHigh: shouldFailOnHighVulnerabilities()
                                ])
                            }
                            
                            archiveArtifacts artifacts: 'trivy-*.*, snyk-*.*'
                        }
                    }
                }
                
                stage('Malware Scanning') {
                    agent { label 'malware-scanner' }
                    steps {
                        script {
                            def imagesToScan = getBuiltImages()
                            
                            imagesToScan.each { image ->
                                malwareScanner.scanImage([
                                    image: image.fullName,
                                    scanner: 'clamav',
                                    quarantine: true
                                ])
                            }
                        }
                    }
                }
                
                stage('Secrets Scanning') {
                    agent { label 'secrets-scanner' }
                    steps {
                        script {
                            // Scan container layers for secrets
                            secretsScanner.scanContainerLayers([
                                images: getBuiltImages(),
                                patterns: getSecretsPatterns(),
                                excludePaths: ['/tmp', '/var/log']
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Container Testing') {
            parallel {
                stage('Container Startup Tests') {
                    agent { label 'container-tester' }
                    steps {
                        script {
                            def testImages = getBuiltImages().findAll { it.target != 'development' }
                            
                            testImages.each { image ->
                                containerTester.testStartup([
                                    image: image.fullName,
                                    healthcheck: true,
                                    timeout: '60s',
                                    expectedPorts: getExpectedPorts(image.target)
                                ])
                            }
                        }
                    }
                }
                
                stage('Integration Tests') {
                    agent { label 'integration-tester' }
                    steps {
                        script {
                            // Test application functionality in containers
                            def testImage = "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:test-${env.BUILD_VERSION}"
                            
                            containerTester.runIntegrationTests([
                                testImage: testImage,
                                testSuite: 'container_integration',
                                environment: 'testing',
                                timeout: '10m'
                            ])
                        }
                    }
                }
                
                stage('Performance Tests') {
                    agent { label 'performance-tester' }
                    steps {
                        script {
                            def prodImage = "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:${env.BUILD_VERSION}"
                            
                            performanceTester.benchmarkContainer([
                                image: prodImage,
                                metrics: ['startup_time', 'memory_usage', 'cpu_usage'],
                                duration: '5m',
                                baseline: getPerformanceBaseline()
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Image Signing & Registry Push') {
            when { params.PUSH_TO_REGISTRY }
            agent { label 'registry-pusher' }
            steps {
                script {
                    def imagesToPush = getBuiltImages().findAll { 
                        shouldPushImage(it.target, params.BUILD_TYPE) 
                    }
                    
                    imagesToPush.each { image ->
                        // Push to primary registry
                        containerRegistry.pushImage([
                            image: image.fullName,
                            registry: env.PRIMARY_REGISTRY,
                            retries: 3
                        ])
                        
                        // Sign production images
                        if (image.target == 'production') {
                            imageSigner.signImage([
                                image: image.fullName,
                                privateKey: env.COSIGN_PRIVATE_KEY,
                                annotations: [
                                    'build.number': env.BUILD_NUMBER,
                                    'git.commit': env.GIT_COMMIT,
                                    'build.date': new Date().format('yyyy-MM-dd\'T\'HH:mm:ssZ')
                                ]
                            ])
                        }
                        
                        // Cross-registry replication
                        if (shouldReplicateImage(image.target)) {
                            containerRegistry.replicateImage([
                                sourceImage: image.fullName,
                                targetRegistries: [env.ECR_REGISTRY, env.GCR_REGISTRY]
                            ])
                        }
                        
                        // Update image metadata
                        imageMetadata.update([
                            image: image.fullName,
                            metadata: [
                                'build.pipeline': env.JOB_NAME,
                                'build.number': env.BUILD_NUMBER,
                                'git.branch': env.BRANCH_NAME,
                                'git.commit': env.GIT_COMMIT,
                                'security.scanned': params.SECURITY_SCAN,
                                'signed': image.target == 'production'
                            ]
                        ])
                    }
                }
            }
        }
        
        stage('Container Promotion') {
            when {
                anyOf {
                    params.BUILD_TYPE == 'production'
                    params.BUILD_TYPE == 'all'
                }
            }
            agent { label 'promotion-manager' }
            steps {
                script {
                    def promotionCriteria = [
                        security_scan_passed: true,
                        vulnerability_threshold: 'medium',
                        performance_baseline_met: true,
                        integration_tests_passed: true
                    ]
                    
                    containerPromotion.promote([
                        sourceImage: "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:${env.BUILD_VERSION}",
                        targetEnvironment: 'production',
                        criteria: promotionCriteria,
                        approvers: ['release-team', 'security-team']
                    ])
                }
            }
        }
        
        stage('Deployment Trigger') {
            when {
                allOf {
                    params.PUSH_TO_REGISTRY
                    anyOf {
                        params.BUILD_TYPE == 'staging'
                        params.BUILD_TYPE == 'production'
                        params.BUILD_TYPE == 'all'
                    }
                }
            }
            agent { label 'deployment-trigger' }
            steps {
                script {
                    // Trigger deployment pipelines
                    if (params.BUILD_TYPE in ['staging', 'all']) {
                        deploymentTrigger.trigger([
                            pipeline: 'staging-deployment',
                            image: "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:staging-${env.BUILD_VERSION}",
                            environment: 'staging'
                        ])
                    }
                    
                    if (params.BUILD_TYPE in ['production', 'all']) {
                        deploymentTrigger.trigger([
                            pipeline: 'production-deployment',
                            image: "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:${env.BUILD_VERSION}",
                            environment: 'production',
                            approval_required: true
                        ])
                    }
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Cleanup build context
                sh '''
                    docker buildx rm container-builder || true
                    docker system prune -f || true
                '''
                
                // Collect artifacts
                containerArtifactCollector.collect([
                    buildType: params.BUILD_TYPE,
                    images: getBuiltImages(),
                    scanResults: glob(pattern: '*.json, *.sarif')
                ])
                
                // Update metrics
                metricsCollector.updateContainerMetrics([
                    pipeline: env.JOB_NAME,
                    buildResult: currentBuild.result,
                    buildType: params.BUILD_TYPE,
                    duration: currentBuild.durationString,
                    imagesBuilt: getBuiltImages().size()
                ])
                
                cleanWs()
            }
        }
        
        success {
            script {
                containerNotification.sendSuccess([
                    images: getBuiltImages(),
                    buildType: params.BUILD_TYPE,
                    securityScanResults: getSecurityScanSummary(),
                    channels: getNotificationChannels()
                ])
            }
        }
        
        failure {
            script {
                containerNotification.sendFailure([
                    buildType: params.BUILD_TYPE,
                    failureStage: env.STAGE_NAME,
                    error: currentBuild.description,
                    channels: ['#container-builds', '#engineering']
                ])
            }
        }
    }
}

// Helper functions
def buildContainerStage(stageConfig) {
    def buildArgs = getBuildArgs(stageConfig.target)
    def cacheFrom = getCacheFrom(stageConfig.target)
    
    sh """
        docker buildx build \\
            --target ${stageConfig.target} \\
            --platform ${env.PLATFORMS} \\
            ${buildArgs.collect { "--build-arg ${it}" }.join(' ')} \\
            ${cacheFrom.collect { "--cache-from ${it}" }.join(' ')} \\
            --cache-to type=registry,ref=${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:cache-${stageConfig.target} \\
            ${stageConfig.tags.collect { "--tag ${it}" }.join(' ')} \\
            ${params.PUSH_TO_REGISTRY ? '--push' : '--load'} \\
            .
    """
}

def getBuiltImages() {
    // Return list of built images based on build type
    def images = []
    
    if (params.BUILD_TYPE in ['development', 'all']) {
        images << [
            fullName: "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:dev-${env.BUILD_VERSION}",
            safeName: "dev",
            target: 'development'
        ]
    }
    
    if (params.BUILD_TYPE in ['staging', 'all']) {
        images << [
            fullName: "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:staging-${env.BUILD_VERSION}",
            safeName: "staging",
            target: 'production'
        ]
    }
    
    if (params.BUILD_TYPE in ['production', 'all']) {
        images << [
            fullName: "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:${env.BUILD_VERSION}",
            safeName: "production",
            target: 'production'
        ]
    }
    
    // Always include testing image
    images << [
        fullName: "${env.PRIMARY_REGISTRY}/${env.IMAGE_NAME}:test-${env.BUILD_VERSION}",
        safeName: "testing",
        target: 'testing'
    ]
    
    return images
}

def getBuildVersion() {
    if (params.CUSTOM_TAG) {
        return params.CUSTOM_TAG
    }
    
    if (env.BRANCH_NAME == 'main') {
        return "v${env.BUILD_NUMBER}"
    } else {
        return "${env.BRANCH_NAME}-${env.BUILD_NUMBER}".replaceAll('/', '-')
    }
}
```

## Container Security Integration

### Advanced Container Security Pipeline
```python
# Container security integration system
import docker
import json
import subprocess
import requests
from typing import Dict, List, Any
import logging
from dataclasses import dataclass
from enum import Enum

class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class SecurityFinding:
    type: str
    severity: SeverityLevel
    description: str
    location: str
    remediation: str
    cve_id: str = None
    cvss_score: float = None

@dataclass
class SecurityScanResult:
    image: str
    scan_type: str
    findings: List[SecurityFinding]
    scan_date: str
    scanner_version: str
    passed: bool
    summary: Dict[str, int]

class ContainerSecurityScanner:
    def __init__(self, config: Dict):
        self.config = config
        self.docker_client = docker.from_env()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def comprehensive_security_scan(self, image: str) -> Dict[str, SecurityScanResult]:
        """Run comprehensive security scanning on container image"""
        
        self.logger.info(f"Starting comprehensive security scan for {image}")
        
        scan_results = {}
        
        # Vulnerability scanning with multiple tools
        scan_results['trivy'] = self._run_trivy_scan(image)
        scan_results['grype'] = self._run_grype_scan(image)
        scan_results['clair'] = self._run_clair_scan(image)
        
        # Secrets scanning
        scan_results['secrets'] = self._run_secrets_scan(image)
        
        # Configuration analysis
        scan_results['config'] = self._analyze_configuration(image)
        
        # Runtime security analysis
        scan_results['runtime'] = self._analyze_runtime_security(image)
        
        # Malware scanning
        scan_results['malware'] = self._run_malware_scan(image)
        
        # Generate consolidated report
        consolidated_result = self._consolidate_results(scan_results)
        
        return {
            'individual_scans': scan_results,
            'consolidated': consolidated_result
        }
    
    def _run_trivy_scan(self, image: str) -> SecurityScanResult:
        """Run Trivy vulnerability scanner"""
        
        try:
            # Run Trivy scan
            cmd = [
                'trivy', 'image',
                '--format', 'json',
                '--quiet',
                image
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            trivy_data = json.loads(result.stdout)
            
            # Process Trivy results
            findings = []
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            
            for target in trivy_data.get('Results', []):
                for vulnerability in target.get('Vulnerabilities', []):
                    severity = SeverityLevel(vulnerability.get('Severity', 'low').lower())
                    severity_counts[severity.value] += 1
                    
                    finding = SecurityFinding(
                        type='vulnerability',
                        severity=severity,
                        description=vulnerability.get('Description', ''),
                        location=f"{vulnerability.get('PkgName')}:{vulnerability.get('InstalledVersion')}",
                        remediation=vulnerability.get('FixedVersion', 'No fix available'),
                        cve_id=vulnerability.get('VulnerabilityID'),
                        cvss_score=float(vulnerability.get('CVSS', {}).get('nvd', {}).get('V3Score', 0))
                    )
                    findings.append(finding)
            
            # Determine if scan passed
            passed = (severity_counts['critical'] == 0 and 
                     severity_counts['high'] <= self.config.get('max_high_vulnerabilities', 0))
            
            return SecurityScanResult(
                image=image,
                scan_type='trivy',
                findings=findings,
                scan_date=trivy_data.get('CreatedAt', ''),
                scanner_version=trivy_data.get('Metadata', {}).get('Version', ''),
                passed=passed,
                summary=severity_counts
            )
            
        except Exception as e:
            self.logger.error(f"Trivy scan failed: {e}")
            return self._create_failed_result(image, 'trivy', str(e))
    
    def _run_grype_scan(self, image: str) -> SecurityScanResult:
        """Run Grype vulnerability scanner"""
        
        try:
            cmd = [
                'grype', image,
                '--output', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            grype_data = json.loads(result.stdout)
            
            findings = []
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            
            for match in grype_data.get('matches', []):
                vulnerability = match.get('vulnerability', {})
                severity = SeverityLevel(vulnerability.get('severity', 'low').lower())
                severity_counts[severity.value] += 1
                
                finding = SecurityFinding(
                    type='vulnerability',
                    severity=severity,
                    description=vulnerability.get('description', ''),
                    location=f"{match.get('artifact', {}).get('name')}:{match.get('artifact', {}).get('version')}",
                    remediation=vulnerability.get('fix', {}).get('versions', ['No fix available'])[0],
                    cve_id=vulnerability.get('id'),
                    cvss_score=self._extract_cvss_score(vulnerability.get('cvss', []))
                )
                findings.append(finding)
            
            passed = (severity_counts['critical'] == 0 and 
                     severity_counts['high'] <= self.config.get('max_high_vulnerabilities', 0))
            
            return SecurityScanResult(
                image=image,
                scan_type='grype',
                findings=findings,
                scan_date=grype_data.get('timestamp', ''),
                scanner_version='grype',
                passed=passed,
                summary=severity_counts
            )
            
        except Exception as e:
            self.logger.error(f"Grype scan failed: {e}")
            return self._create_failed_result(image, 'grype', str(e))
    
    def _run_secrets_scan(self, image: str) -> SecurityScanResult:
        """Scan container image for secrets"""
        
        try:
            # Export image filesystem
            container = self.docker_client.containers.create(image, command='sleep infinity')
            
            # Run TruffleHog on container filesystem
            cmd = [
                'docker', 'exec', container.id,
                'trufflehog', 'filesystem', '/',
                '--json',
                '--no-verification'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            container.remove(force=True)
            
            findings = []
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        secret_data = json.loads(line)
                        severity = SeverityLevel('high')  # Secrets are always high severity
                        severity_counts['high'] += 1
                        
                        finding = SecurityFinding(
                            type='secret',
                            severity=severity,
                            description=f"Potential secret detected: {secret_data.get('detector', 'unknown')}",
                            location=secret_data.get('source', 'unknown'),
                            remediation="Remove or encrypt sensitive data",
                            cve_id=None,
                            cvss_score=None
                        )
                        findings.append(finding)
            
            passed = severity_counts['high'] == 0
            
            return SecurityScanResult(
                image=image,
                scan_type='secrets',
                findings=findings,
                scan_date='',
                scanner_version='trufflehog',
                passed=passed,
                summary=severity_counts
            )
            
        except Exception as e:
            self.logger.error(f"Secrets scan failed: {e}")
            return self._create_failed_result(image, 'secrets', str(e))
    
    def _analyze_configuration(self, image: str) -> SecurityScanResult:
        """Analyze container configuration for security issues"""
        
        try:
            # Inspect image configuration
            image_info = self.docker_client.api.inspect_image(image)
            config = image_info.get('Config', {})
            
            findings = []
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            
            # Check if running as root
            user = config.get('User', '')
            if not user or user == 'root' or user == '0':
                severity = SeverityLevel('medium')
                severity_counts['medium'] += 1
                
                findings.append(SecurityFinding(
                    type='configuration',
                    severity=severity,
                    description="Container runs as root user",
                    location="User configuration",
                    remediation="Set non-root user in Dockerfile"
                ))
            
            # Check for exposed privileged ports
            exposed_ports = config.get('ExposedPorts', {})
            for port in exposed_ports:
                port_num = int(port.split('/')[0])
                if port_num < 1024:
                    severity = SeverityLevel('low')
                    severity_counts['low'] += 1
                    
                    findings.append(SecurityFinding(
                        type='configuration',
                        severity=severity,
                        description=f"Privileged port {port} exposed",
                        location=f"Port {port}",
                        remediation="Use non-privileged ports (> 1024)"
                    ))
            
            # Check environment variables for secrets
            env_vars = config.get('Env', [])
            secret_patterns = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'API_KEY']
            
            for env_var in env_vars:
                if '=' in env_var:
                    key, value = env_var.split('=', 1)
                    if any(pattern in key.upper() for pattern in secret_patterns):
                        severity = SeverityLevel('medium')
                        severity_counts['medium'] += 1
                        
                        findings.append(SecurityFinding(
                            type='configuration',
                            severity=severity,
                            description=f"Potential secret in environment variable: {key}",
                            location=f"Environment variable: {key}",
                            remediation="Use secrets management instead of environment variables"
                        ))
            
            passed = severity_counts['critical'] == 0 and severity_counts['high'] == 0
            
            return SecurityScanResult(
                image=image,
                scan_type='configuration',
                findings=findings,
                scan_date='',
                scanner_version='docker_inspect',
                passed=passed,
                summary=severity_counts
            )
            
        except Exception as e:
            self.logger.error(f"Configuration analysis failed: {e}")
            return self._create_failed_result(image, 'configuration', str(e))
    
    def _consolidate_results(self, scan_results: Dict[str, SecurityScanResult]) -> SecurityScanResult:
        """Consolidate multiple scan results into single result"""
        
        all_findings = []
        total_severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for scan_type, result in scan_results.items():
            all_findings.extend(result.findings)
            for severity, count in result.summary.items():
                total_severity_counts[severity] += count
        
        # Remove duplicates based on CVE ID
        unique_findings = []
        seen_cves = set()
        
        for finding in all_findings:
            if finding.cve_id and finding.cve_id in seen_cves:
                continue
            unique_findings.append(finding)
            if finding.cve_id:
                seen_cves.add(finding.cve_id)
        
        # Recalculate severity counts
        final_severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for finding in unique_findings:
            final_severity_counts[finding.severity.value] += 1
        
        # Determine overall pass/fail
        passed = (final_severity_counts['critical'] == 0 and 
                 final_severity_counts['high'] <= self.config.get('max_high_vulnerabilities', 0))
        
        return SecurityScanResult(
            image=list(scan_results.values())[0].image,
            scan_type='consolidated',
            findings=unique_findings,
            scan_date='',
            scanner_version='multiple',
            passed=passed,
            summary=final_severity_counts
        )
    
    def generate_security_report(self, scan_results: Dict[str, Any]) -> str:
        """Generate comprehensive security report"""
        
        consolidated = scan_results['consolidated']
        
        report = f"""
# Container Security Scan Report

**Image:** {consolidated.image}
**Scan Date:** {consolidated.scan_date}
**Overall Result:** {'✅ PASSED' if consolidated.passed else '❌ FAILED'}

## Summary
- **Critical:** {consolidated.summary['critical']}
- **High:** {consolidated.summary['high']}
- **Medium:** {consolidated.summary['medium']}
- **Low:** {consolidated.summary['low']}

## Findings by Severity

"""
        
        # Group findings by severity
        severity_groups = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for finding in consolidated.findings:
            severity_groups[finding.severity.value].append(finding)
        
        for severity in ['critical', 'high', 'medium', 'low']:
            findings = severity_groups[severity]
            if findings:
                report += f"### {severity.upper()} ({len(findings)} findings)\n\n"
                for finding in findings:
                    report += f"- **{finding.type.title()}:** {finding.description}\n"
                    report += f"  - **Location:** {finding.location}\n"
                    report += f"  - **Remediation:** {finding.remediation}\n"
                    if finding.cve_id:
                        report += f"  - **CVE ID:** {finding.cve_id}\n"
                    if finding.cvss_score:
                        report += f"  - **CVSS Score:** {finding.cvss_score}\n"
                    report += "\n"
        
        return report
    
    def _create_failed_result(self, image: str, scan_type: str, error: str) -> SecurityScanResult:
        """Create a failed scan result"""
        
        return SecurityScanResult(
            image=image,
            scan_type=scan_type,
            findings=[SecurityFinding(
                type='error',
                severity=SeverityLevel('critical'),
                description=f"Scanner failed: {error}",
                location='scanner',
                remediation='Fix scanner configuration or connectivity'
            )],
            scan_date='',
            scanner_version='unknown',
            passed=False,
            summary={'critical': 1, 'high': 0, 'medium': 0, 'low': 0}
        )

# Usage example
if __name__ == "__main__":
    config = {
        'max_high_vulnerabilities': 5,
        'scanners': {
            'trivy': {'enabled': True},
            'grype': {'enabled': True},
            'secrets': {'enabled': True}
        }
    }
    
    scanner = ContainerSecurityScanner(config)
    results = scanner.comprehensive_security_scan('nginx:latest')
    
    report = scanner.generate_security_report(results)
    print(report)
```

This comprehensive container workflow system provides enterprise-grade capabilities for container building, security scanning, multi-stage optimization, registry management, and automated deployment integration.