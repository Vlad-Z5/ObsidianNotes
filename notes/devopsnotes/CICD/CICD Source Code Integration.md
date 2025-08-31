# CICD Source Code Integration

Advanced source code management integration patterns, branching strategies, and automated quality controls for enterprise CICD pipelines.

## Table of Contents
1. [Git Integration Fundamentals](#git-integration-fundamentals)
2. [Branching Strategies](#branching-strategies)
3. [Webhook & Event Management](#webhook--event-management)
4. [Code Quality Gates](#code-quality-gates)
5. [Merge & Pull Request Automation](#merge--pull-request-automation)
6. [Multi-Repository Management](#multi-repository-management)
7. [Security & Compliance](#security--compliance)
8. [Advanced Integration Patterns](#advanced-integration-patterns)

## Git Integration Fundamentals

### Repository Configuration
```yaml
# Enterprise Git configuration
git_integration:
  repository_setup:
    default_branch: "main"
    protected_branches:
      - name: "main"
        protection_rules:
          required_status_checks:
            strict: true
            contexts:
              - "continuous-integration"
              - "security-scan"
              - "code-quality"
          required_pull_request_reviews:
            required_approving_review_count: 2
            dismiss_stale_reviews: true
            require_code_owner_reviews: true
          enforce_admins: false
          restrictions:
            users: []
            teams: ["senior-developers"]
      
      - name: "develop"
        protection_rules:
          required_status_checks:
            strict: true
            contexts:
              - "continuous-integration"
              - "security-scan"
          required_pull_request_reviews:
            required_approving_review_count: 1

  hooks_configuration:
    pre_commit:
      - lint_check
      - security_scan
      - test_execution
    
    pre_push:
      - integration_tests
      - dependency_check
    
    post_receive:
      - trigger_pipeline
      - notification_system
      - metrics_collection
```

### Git Flow Integration
```bash
#!/bin/bash
# git-flow-cicd-integration.sh

set -euo pipefail

# Configuration
MAIN_BRANCH="main"
DEVELOP_BRANCH="develop"
FEATURE_PREFIX="feature/"
RELEASE_PREFIX="release/"
HOTFIX_PREFIX="hotfix/"

# Determine pipeline strategy based on branch
determine_pipeline_strategy() {
    local branch_name=$1
    local pipeline_strategy=""
    
    case "$branch_name" in
        "$MAIN_BRANCH")
            pipeline_strategy="production-deployment"
            ;;
        "$DEVELOP_BRANCH")
            pipeline_strategy="integration-testing"
            ;;
        "$FEATURE_PREFIX"*)
            pipeline_strategy="feature-validation"
            ;;
        "$RELEASE_PREFIX"*)
            pipeline_strategy="release-validation"
            ;;
        "$HOTFIX_PREFIX"*)
            pipeline_strategy="hotfix-validation"
            ;;
        *)
            pipeline_strategy="basic-validation"
            ;;
    esac
    
    echo "$pipeline_strategy"
}

# Extract feature/service context
extract_context() {
    local branch_name=$1
    local changed_files=$2
    
    # Determine affected services
    affected_services=$(echo "$changed_files" | grep -E '^services/' | cut -d'/' -f2 | sort -u)
    
    # Determine if infrastructure changes exist
    infra_changes=$(echo "$changed_files" | grep -E '^(terraform|k8s|helm)/' | wc -l)
    
    # Determine if documentation changes exist
    docs_changes=$(echo "$changed_files" | grep -E '\.(md|rst|txt)$' | wc -l)
    
    # Create context object
    cat <<EOF
{
    "branch": "$branch_name",
    "pipeline_strategy": "$(determine_pipeline_strategy "$branch_name")",
    "affected_services": [$(echo "$affected_services" | tr '\n' ',' | sed 's/,$//' | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$/"/')],
    "infrastructure_changes": $infra_changes,
    "documentation_changes": $docs_changes,
    "requires_integration_tests": $([ ${#affected_services} -gt 1 ] && echo "true" || echo "false")
}
EOF
}

# Validate branch naming convention
validate_branch_name() {
    local branch_name=$1
    local valid_patterns=(
        "^main$"
        "^develop$"
        "^feature/[a-z0-9-]+(/[a-z0-9-]+)*$"
        "^release/[0-9]+\.[0-9]+\.[0-9]+$"
        "^hotfix/[a-z0-9-]+-[0-9]+\.[0-9]+\.[0-9]+$"
    )
    
    for pattern in "${valid_patterns[@]}"; do
        if [[ $branch_name =~ $pattern ]]; then
            return 0
        fi
    done
    
    echo "Error: Branch name '$branch_name' doesn't follow naming conventions"
    echo "Valid patterns:"
    echo "  - feature/feature-name"
    echo "  - release/1.0.0"
    echo "  - hotfix/fix-name-1.0.1"
    return 1
}

# Main execution
main() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    local changed_files=$(git diff --name-only HEAD~1 HEAD)
    
    # Validate branch naming
    validate_branch_name "$current_branch"
    
    # Extract context
    local context=$(extract_context "$current_branch" "$changed_files")
    
    # Output context for pipeline consumption
    echo "$context" > .pipeline-context.json
    
    echo "Pipeline context generated successfully"
    echo "$context" | jq '.'
}

main "$@"
```

## Branching Strategies

### Advanced GitFlow Implementation
```yaml
# GitFlow CICD integration
gitflow_strategy:
  branch_workflows:
    feature_branches:
      creation_triggers:
        - jira_ticket_created
        - github_issue_assigned
      
      pipeline_stages:
        - code_quality_check:
            tools: [eslint, sonarqube, codacy]
            failure_action: "block_merge"
        - unit_tests:
            coverage_threshold: 80
            failure_action: "require_explanation"
        - security_scan:
            tools: [snyk, semgrep, bandit]
            failure_action: "block_merge"
        - build_verification:
            environments: [local_build]
            failure_action: "block_merge"
      
      merge_requirements:
        - all_checks_pass: true
        - peer_review_count: 2
        - no_merge_conflicts: true
        - up_to_date_with_target: true
    
    develop_branch:
      merge_triggers:
        - feature_branch_approved
        - hotfix_branch_approved
      
      pipeline_stages:
        - full_test_suite:
            types: [unit, integration, contract]
        - deploy_integration_environment:
            environment: "integration"
            auto_promotion: true
        - integration_tests:
            test_suites: [api_tests, ui_tests, performance_tests]
        - deploy_staging_environment:
            environment: "staging"
            approval_required: false
      
      quality_gates:
        - test_coverage: ">= 85%"
        - code_duplication: "<= 5%"
        - security_vulnerabilities: "0 high, <= 5 medium"
        - performance_regression: "< 10%"
    
    release_branches:
      creation_triggers:
        - sprint_completion
        - manual_trigger
      
      pipeline_stages:
        - version_validation:
            semantic_versioning: true
            changelog_required: true
        - comprehensive_testing:
            test_suites: [all_automated_tests]
            manual_testing_required: true
        - security_validation:
            penetration_testing: true
            compliance_check: true
        - performance_validation:
            load_testing: true
            stress_testing: true
        - pre_production_deployment:
            environment: "pre_prod"
            approval_required: true
      
      approval_workflow:
        required_approvers:
          - product_owner
          - technical_lead
          - security_team
        approval_timeout: "48h"
        emergency_override: true
    
    main_branch:
      merge_sources: ["release/*", "hotfix/*"]
      
      pipeline_stages:
        - final_validation:
            smoke_tests: true
            health_checks: true
        - production_deployment:
            strategy: "blue_green"
            rollback_enabled: true
            monitoring_validation: true
        - post_deployment_validation:
            smoke_tests: true
            performance_monitoring: true
            user_acceptance_testing: optional
      
      post_merge_actions:
        - tag_creation:
            format: "v{major}.{minor}.{patch}"
            signed: true
        - merge_back_to_develop: true
        - notification:
            channels: ["slack", "email", "jira"]
        - metrics_collection: true
```

## Webhook & Event Management

### Advanced Webhook Processing
```python
#!/usr/bin/env python3
# webhook_processor.py

import json
import hashlib
import hmac
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    RELEASE = "release"
    ISSUE = "issues"
    DEPLOYMENT = "deployment"

@dataclass
class WebhookEvent:
    event_type: EventType
    repository: str
    branch: str
    commit_sha: str
    author: str
    timestamp: str
    changed_files: List[str]
    metadata: Dict

class WebhookProcessor:
    def __init__(self, secret_token: str):
        self.secret_token = secret_token
        self.logger = logging.getLogger(__name__)
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security"""
        if not signature.startswith('sha256='):
            return False
        
        expected = hmac.new(
            self.secret_token.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f'sha256={expected}', signature)
    
    def process_push_event(self, payload: Dict) -> Optional[WebhookEvent]:
        """Process git push events"""
        try:
            repository = payload['repository']['full_name']
            branch = payload['ref'].replace('refs/heads/', '')
            commit_sha = payload['after']
            author = payload['pusher']['name']
            timestamp = payload['head_commit']['timestamp']
            
            # Extract changed files
            changed_files = []
            for commit in payload['commits']:
                changed_files.extend(commit.get('added', []))
                changed_files.extend(commit.get('modified', []))
            
            # Remove duplicates
            changed_files = list(set(changed_files))
            
            # Determine pipeline context
            metadata = self._analyze_changes(changed_files, branch)
            
            return WebhookEvent(
                event_type=EventType.PUSH,
                repository=repository,
                branch=branch,
                commit_sha=commit_sha,
                author=author,
                timestamp=timestamp,
                changed_files=changed_files,
                metadata=metadata
            )
        except KeyError as e:
            self.logger.error(f"Missing required field in push payload: {e}")
            return None
    
    def process_pull_request_event(self, payload: Dict) -> Optional[WebhookEvent]:
        """Process pull request events"""
        try:
            action = payload['action']
            if action not in ['opened', 'synchronize', 'closed']:
                return None
            
            pr = payload['pull_request']
            repository = payload['repository']['full_name']
            branch = pr['head']['ref']
            commit_sha = pr['head']['sha']
            author = pr['user']['login']
            timestamp = pr['updated_at']
            
            # Get changed files (would require additional API call)
            changed_files = []  # Simplified for example
            
            metadata = {
                'action': action,
                'pr_number': pr['number'],
                'target_branch': pr['base']['ref'],
                'mergeable': pr.get('mergeable', False),
                'draft': pr.get('draft', False)
            }
            
            return WebhookEvent(
                event_type=EventType.PULL_REQUEST,
                repository=repository,
                branch=branch,
                commit_sha=commit_sha,
                author=author,
                timestamp=timestamp,
                changed_files=changed_files,
                metadata=metadata
            )
        except KeyError as e:
            self.logger.error(f"Missing required field in PR payload: {e}")
            return None
    
    def _analyze_changes(self, changed_files: List[str], branch: str) -> Dict:
        """Analyze changed files to determine pipeline requirements"""
        analysis = {
            'affected_services': [],
            'infrastructure_changes': False,
            'database_changes': False,
            'config_changes': False,
            'documentation_only': False,
            'requires_integration_tests': False,
            'requires_security_scan': False,
            'deployment_required': False
        }
        
        # Service detection
        services = set()
        for file_path in changed_files:
            if file_path.startswith('services/'):
                service = file_path.split('/')[1]
                services.add(service)
        
        analysis['affected_services'] = list(services)
        analysis['requires_integration_tests'] = len(services) > 1
        
        # Infrastructure changes
        infra_patterns = ['terraform/', 'k8s/', 'helm/', 'docker/', 'Dockerfile']
        analysis['infrastructure_changes'] = any(
            any(pattern in file_path for pattern in infra_patterns)
            for file_path in changed_files
        )
        
        # Database changes
        db_patterns = ['migrations/', '.sql', 'schema.']
        analysis['database_changes'] = any(
            any(pattern in file_path for pattern in db_patterns)
            for file_path in changed_files
        )
        
        # Configuration changes
        config_patterns = ['.env', 'config/', '.yaml', '.yml', '.json']
        analysis['config_changes'] = any(
            any(pattern in file_path for pattern in config_patterns)
            for file_path in changed_files
        )
        
        # Documentation only
        doc_patterns = ['.md', '.rst', '.txt', 'docs/']
        analysis['documentation_only'] = all(
            any(pattern in file_path for pattern in doc_patterns)
            for file_path in changed_files
        )
        
        # Security scan requirements
        security_patterns = ['package.json', 'requirements.txt', 'Gemfile', 'pom.xml']
        analysis['requires_security_scan'] = any(
            any(pattern in file_path for pattern in security_patterns)
            for file_path in changed_files
        )
        
        # Deployment requirements
        deployment_branches = ['main', 'master', 'develop', 'staging']
        analysis['deployment_required'] = branch in deployment_branches
        
        return analysis
    
    def generate_pipeline_config(self, event: WebhookEvent) -> Dict:
        """Generate dynamic pipeline configuration based on event"""
        config = {
            'pipeline_id': f"{event.repository}-{event.commit_sha[:8]}",
            'trigger_event': event.event_type.value,
            'repository': event.repository,
            'branch': event.branch,
            'commit_sha': event.commit_sha,
            'stages': []
        }
        
        # Always include basic stages
        config['stages'].extend([
            {
                'name': 'checkout',
                'type': 'source_code',
                'enabled': True
            },
            {
                'name': 'build',
                'type': 'compilation',
                'enabled': not event.metadata.get('documentation_only', False)
            }
        ])
        
        # Conditional stages based on analysis
        if event.metadata.get('requires_security_scan', False):
            config['stages'].append({
                'name': 'security_scan',
                'type': 'security',
                'enabled': True,
                'tools': ['semgrep', 'snyk', 'bandit']
            })
        
        if event.metadata.get('affected_services'):
            config['stages'].append({
                'name': 'service_tests',
                'type': 'testing',
                'enabled': True,
                'parallel': True,
                'services': event.metadata['affected_services']
            })
        
        if event.metadata.get('requires_integration_tests', False):
            config['stages'].append({
                'name': 'integration_tests',
                'type': 'testing',
                'enabled': True,
                'depends_on': ['service_tests']
            })
        
        if event.metadata.get('deployment_required', False):
            strategy = 'blue_green' if event.branch == 'main' else 'rolling'
            config['stages'].append({
                'name': 'deployment',
                'type': 'deployment',
                'enabled': True,
                'strategy': strategy,
                'environment': 'production' if event.branch == 'main' else 'staging'
            })
        
        return config

# Usage example
def main():
    processor = WebhookProcessor(secret_token='your-webhook-secret')
    
    # Example payload processing
    payload = {
        'ref': 'refs/heads/feature/new-auth',
        'after': 'abc123def456',
        'repository': {'full_name': 'company/app'},
        'pusher': {'name': 'developer'},
        'head_commit': {'timestamp': '2023-01-01T12:00:00Z'},
        'commits': [
            {
                'added': ['services/auth/auth.py'],
                'modified': ['services/user/user.py', 'requirements.txt']
            }
        ]
    }
    
    event = processor.process_push_event(payload)
    if event:
        pipeline_config = processor.generate_pipeline_config(event)
        print(json.dumps(pipeline_config, indent=2))

if __name__ == '__main__':
    main()
```

## Real-World Use Cases

### Use Case 1: Microservices Monorepo Management
```yaml
# Large-scale microservices repository integration
microservices_integration:
  repository_structure:
    services:
      user_service:
        path: "services/user/"
        technology: "Node.js"
        dependencies: ["shared/auth", "shared/database"]
        test_requirements: ["unit", "integration", "contract"]
      
      payment_service:
        path: "services/payment/"
        technology: "Java"
        dependencies: ["shared/encryption", "shared/messaging"]
        compliance: ["PCI-DSS", "SOX"]
        test_requirements: ["unit", "integration", "security"]
      
      notification_service:
        path: "services/notification/"
        technology: "Python"
        dependencies: ["shared/templates", "shared/messaging"]
        test_requirements: ["unit", "integration"]
  
  change_detection:
    algorithms:
      path_based: true
      dependency_graph: true
      impact_analysis: true
    
    triggers:
      single_service_change:
        pipeline: "service_specific"
        stages: ["build", "test", "deploy_service"]
      
      cross_service_change:
        pipeline: "integration_focused"
        stages: ["build_all", "unit_tests", "integration_tests", "contract_tests"]
      
      shared_dependency_change:
        pipeline: "full_regression"
        stages: ["build_all", "full_test_suite", "staged_deployment"]
```

### Use Case 2: Enterprise GitOps Integration
```python
#!/usr/bin/env python3
# gitops_integration.py

import git
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class GitOpsConfig:
    application: str
    environment: str
    image_tag: str
    replicas: int
    resources: Dict[str, str]
    config_hash: str

class GitOpsIntegrator:
    def __init__(self, config_repo_url: str, deploy_key_path: str):
        self.config_repo_url = config_repo_url
        self.deploy_key_path = deploy_key_path
        self.logger = logging.getLogger(__name__)
    
    def update_deployment_config(self, app_name: str, environment: str, 
                               image_tag: str, config_changes: Dict) -> bool:
        """Update GitOps repository with new deployment configuration"""
        try:
            # Clone or update config repository
            repo_path = self._prepare_config_repo()
            
            # Load current configuration
            current_config = self._load_current_config(repo_path, app_name, environment)
            
            # Update configuration
            updated_config = self._merge_config_changes(current_config, {
                'image_tag': image_tag,
                **config_changes
            })
            
            # Validate configuration
            if not self._validate_config(updated_config):
                raise ValueError("Configuration validation failed")
            
            # Write updated configuration
            config_path = repo_path / f"apps/{app_name}/{environment}/values.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(asdict(updated_config), f, default_flow_style=False)
            
            # Commit and push changes
            self._commit_and_push_changes(repo_path, f"Update {app_name} to {image_tag}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update GitOps config: {e}")
            return False
    
    def _prepare_config_repo(self) -> Path:
        """Clone or update the GitOps configuration repository"""
        repo_path = Path("/tmp/gitops-config")
        
        if repo_path.exists():
            # Update existing repository
            repo = git.Repo(repo_path)
            repo.remotes.origin.pull()
        else:
            # Clone repository with deploy key
            git.Repo.clone_from(
                self.config_repo_url,
                repo_path,
                env={'GIT_SSH_COMMAND': f'ssh -i {self.deploy_key_path} -o StrictHostKeyChecking=no'}
            )
        
        return repo_path
    
    def _load_current_config(self, repo_path: Path, app_name: str, environment: str) -> GitOpsConfig:
        """Load current deployment configuration"""
        config_file = repo_path / f"apps/{app_name}/{environment}/values.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            return GitOpsConfig(
                application=app_name,
                environment=environment,
                image_tag=config_data.get('image_tag', 'latest'),
                replicas=config_data.get('replicas', 1),
                resources=config_data.get('resources', {}),
                config_hash=config_data.get('config_hash', '')
            )
        else:
            # Create default configuration
            return GitOpsConfig(
                application=app_name,
                environment=environment,
                image_tag='latest',
                replicas=1,
                resources={'cpu': '100m', 'memory': '128Mi'},
                config_hash=''
            )
    
    def _merge_config_changes(self, current: GitOpsConfig, changes: Dict) -> GitOpsConfig:
        """Merge configuration changes with current config"""
        updated = asdict(current)
        updated.update(changes)
        return GitOpsConfig(**updated)
    
    def _validate_config(self, config: GitOpsConfig) -> bool:
        """Validate deployment configuration"""
        validations = [
            config.replicas > 0,
            config.image_tag != '',
            'cpu' in config.resources,
            'memory' in config.resources
        ]
        
        return all(validations)
    
    def _commit_and_push_changes(self, repo_path: Path, commit_message: str):
        """Commit and push configuration changes"""
        repo = git.Repo(repo_path)
        
        # Stage all changes
        repo.git.add('.')
        
        # Commit changes
        if repo.is_dirty():
            repo.index.commit(commit_message)
            
            # Push to remote
            repo.remotes.origin.push()
            
            self.logger.info(f"Successfully pushed changes: {commit_message}")
        else:
            self.logger.info("No changes to commit")
```

### Use Case 3: Multi-Environment Branch Strategy
```yaml
# Complex enterprise branch strategy
enterprise_branching:
  environments:
    development:
      branches: ["feature/*", "bugfix/*"]
      auto_deploy: true
      testing_requirements:
        - unit_tests: "required"
        - integration_tests: "optional"
        - security_scan: "required"
      
      quality_gates:
        - code_coverage: ">= 70%"
        - lint_errors: "0"
        - security_vulnerabilities: "0 critical"
    
    staging:
      branches: ["develop", "release/*"]
      auto_deploy: true
      testing_requirements:
        - unit_tests: "required"
        - integration_tests: "required"
        - e2e_tests: "required"
        - performance_tests: "required"
        - security_scan: "required"
      
      quality_gates:
        - code_coverage: ">= 85%"
        - performance_regression: "< 5%"
        - security_vulnerabilities: "0 high+"
        - accessibility_compliance: "AA"
    
    production:
      branches: ["main"]
      auto_deploy: false
      approval_required: true
      testing_requirements:
        - all_staging_tests: "passed"
        - smoke_tests: "required"
        - canary_deployment: "required"
      
      quality_gates:
        - all_tests_passing: true
        - security_compliance: "full"
        - performance_benchmarks: "met"
        - business_sign_off: true
  
  branch_protection:
    main:
      dismiss_stale_reviews: true
      required_reviews: 3
      require_code_owner_review: true
      required_status_checks:
        - "ci/build"
        - "ci/test"
        - "security/scan"
        - "quality/sonarqube"
      
      restrictions:
        push_allowance: ["admin", "release-team"]
        bypass_allowance: ["emergency-response-team"]
    
    develop:
      dismiss_stale_reviews: true
      required_reviews: 2
      require_code_owner_review: true
      required_status_checks:
        - "ci/build"
        - "ci/test"
        - "security/scan"
```

### Use Case 4: Compliance-Heavy Integration
```bash
#!/bin/bash
# compliance_integration.sh

set -euo pipefail

# Compliance framework configuration
COMPLIANCE_FRAMEWORKS=("SOX" "HIPAA" "PCI-DSS" "GDPR")
AUDIT_LOG_RETENTION="2555"  # 7 years in days
REQUIRED_APPROVERS=3

# Audit logging function
audit_log() {
    local action="$1"
    local resource="$2"
    local user="${GITHUB_ACTOR:-unknown}"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local commit_sha="${GITHUB_SHA:-unknown}"
    
    # Create audit entry
    local audit_entry=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "action": "$action",
  "resource": "$resource",
  "user": "$user",
  "commit_sha": "$commit_sha",
  "branch": "${GITHUB_REF_NAME:-unknown}",
  "workflow": "${GITHUB_WORKFLOW:-unknown}",
  "run_id": "${GITHUB_RUN_ID:-unknown}",
  "compliance_frameworks": [$(printf '"%s",' "${COMPLIANCE_FRAMEWORKS[@]}" | sed 's/,$//')]]
}
EOF
    )
    
    # Send to audit system
    curl -X POST "${AUDIT_ENDPOINT}" \
        -H "Authorization: Bearer ${AUDIT_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$audit_entry" || true
    
    # Also log locally for backup
    echo "$audit_entry" >> "/tmp/audit.log"
}

# Compliance validation function
validate_compliance() {
    local changes="$1"
    local violations=()
    
    echo "🔍 Running compliance validation..."
    
    # SOX compliance checks
    if echo "$changes" | grep -E '(financial|accounting|revenue)' >/dev/null; then
        echo "📊 SOX compliance checks required"
        
        # Check for required approvals
        local approvers=$(gh pr view --json reviews --jq '.reviews | length')
        if [[ $approvers -lt $REQUIRED_APPROVERS ]]; then
            violations+=("SOX: Insufficient approvers ($approvers/$REQUIRED_APPROVERS)")
        fi
        
        # Check for audit trail
        if ! git log --oneline -10 | grep -E '(audit|review|approve)'; then
            violations+=("SOX: Missing audit trail in commit history")
        fi
    fi
    
    # HIPAA compliance checks
    if echo "$changes" | grep -E '(patient|health|medical|phi)' >/dev/null; then
        echo "🏥 HIPAA compliance checks required"
        
        # Check for PHI handling
        if echo "$changes" | grep -E '(ssn|dob|patient_id)' >/dev/null; then
            violations+=("HIPAA: Potential PHI exposure detected")
        fi
        
        # Verify encryption patterns
        if ! echo "$changes" | grep -E '(encrypt|hash|secure)' >/dev/null; then
            violations+=("HIPAA: No encryption patterns found for sensitive data")
        fi
    fi
    
    # PCI-DSS compliance checks
    if echo "$changes" | grep -E '(payment|card|credit|debit)' >/dev/null; then
        echo "💳 PCI-DSS compliance checks required"
        
        # Check for secure coding patterns
        if echo "$changes" | grep -E '(card_number|cvv|pin)' >/dev/null; then
            violations+=("PCI-DSS: Potential card data exposure")
        fi
        
        # Verify tokenization patterns
        if ! echo "$changes" | grep -E '(tokenize|vault|secure_store)' >/dev/null; then
            violations+=("PCI-DSS: No tokenization patterns found")
        fi
    fi
    
    # GDPR compliance checks
    if echo "$changes" | grep -E '(personal|gdpr|privacy|consent)' >/dev/null; then
        echo "🇪🇺 GDPR compliance checks required"
        
        # Check for data processing documentation
        if ! find . -name "*privacy*" -o -name "*gdpr*" -o -name "*consent*" | head -1 >/dev/null; then
            violations+=("GDPR: Missing privacy documentation")
        fi
        
        # Check for data retention policies
        if ! echo "$changes" | grep -E '(retention|delete|purge)' >/dev/null; then
            violations+=("GDPR: No data retention patterns found")
        fi
    fi
    
    # Report violations
    if [[ ${#violations[@]} -gt 0 ]]; then
        echo "❌ Compliance violations detected:"
        printf '  - %s\n' "${violations[@]}"
        
        # Log violations for audit
        for violation in "${violations[@]}"; do
            audit_log "compliance_violation" "$violation"
        done
        
        return 1
    else
        echo "✅ All compliance checks passed"
        audit_log "compliance_check" "passed"
        return 0
    fi
}

# Secure merge validation
validate_secure_merge() {
    local pr_number="$1"
    
    echo "🔒 Validating secure merge requirements..."
    
    # Check GPG signatures
    local unsigned_commits=$(git log --pretty="format:%H %G?" origin/main..HEAD | grep -v " G" | wc -l)
    if [[ $unsigned_commits -gt 0 ]]; then
        echo "❌ Found $unsigned_commits unsigned commits"
        audit_log "security_violation" "unsigned_commits: $unsigned_commits"
        return 1
    fi
    
    # Check for security scanning results
    local scan_results=$(find . -name "*security*" -o -name "*vulnerability*" | head -1)
    if [[ -z "$scan_results" ]]; then
        echo "❌ No security scan results found"
        audit_log "security_violation" "missing_security_scan"
        return 1
    fi
    
    # Verify all status checks passed
    local failed_checks=$(gh pr view "$pr_number" --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS") | .name')
    if [[ -n "$failed_checks" ]]; then
        echo "❌ Failed status checks: $failed_checks"
        audit_log "pipeline_failure" "failed_checks: $failed_checks"
        return 1
    fi
    
    echo "✅ Secure merge validation passed"
    audit_log "secure_merge" "validation_passed"
    return 0
}

# Main compliance integration
main() {
    local changed_files=$(git diff --name-only HEAD~1 HEAD)
    local pr_number="${PR_NUMBER:-}"
    
    audit_log "compliance_check_start" "$(echo "$changed_files" | wc -l) files changed"
    
    # Run compliance validation
    if ! validate_compliance "$changed_files"; then
        echo "❌ Compliance validation failed"
        exit 1
    fi
    
    # Run secure merge validation if PR context
    if [[ -n "$pr_number" ]]; then
        if ! validate_secure_merge "$pr_number"; then
            echo "❌ Secure merge validation failed"
            exit 1
        fi
    fi
    
    echo "✅ All compliance and security validations passed"
    audit_log "compliance_check_complete" "all_validations_passed"
}

# Execute if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## Advanced Integration Patterns

### Polyglot Repository Management
```python
#!/usr/bin/env python3
# polyglot_repo_manager.py

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class Language(Enum):
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    PYTHON = "python"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CSHARP = "csharp"

@dataclass
class ProjectConfig:
    name: str
    path: str
    language: Language
    framework: Optional[str]
    build_tool: str
    test_command: str
    dependencies: List[str]
    docker_enabled: bool

class PolyglotRepoManager:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.projects = self._discover_projects()
    
    def _discover_projects(self) -> Dict[str, ProjectConfig]:
        """Automatically discover projects in the repository"""
        projects = {}
        
        for root, dirs, files in os.walk(self.repo_root):
            root_path = Path(root)
            relative_path = root_path.relative_to(self.repo_root)
            
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target']]
            
            project_config = self._identify_project_type(root_path, files)
            if project_config:
                projects[str(relative_path)] = project_config
        
        return projects
    
    def _identify_project_type(self, path: Path, files: List[str]) -> Optional[ProjectConfig]:
        """Identify project type based on files present"""
        project_name = path.name
        relative_path = str(path.relative_to(self.repo_root))
        
        # JavaScript/TypeScript projects
        if 'package.json' in files:
            has_typescript = any(f.endswith('.ts') or f.endswith('.tsx') for f in files)
            language = Language.TYPESCRIPT if has_typescript else Language.JAVASCRIPT
            
            # Detect framework
            framework = self._detect_js_framework(path)
            
            return ProjectConfig(
                name=project_name,
                path=relative_path,
                language=language,
                framework=framework,
                build_tool='npm',
                test_command='npm test',
                dependencies=self._get_js_dependencies(path),
                docker_enabled='Dockerfile' in files
            )
        
        # Python projects
        elif any(f in files for f in ['requirements.txt', 'pyproject.toml', 'setup.py']):
            framework = self._detect_python_framework(path)
            
            return ProjectConfig(
                name=project_name,
                path=relative_path,
                language=Language.PYTHON,
                framework=framework,
                build_tool='pip',
                test_command='pytest' if framework != 'django' else 'python manage.py test',
                dependencies=self._get_python_dependencies(path),
                docker_enabled='Dockerfile' in files
            )
        
        # Java projects
        elif any(f in files for f in ['pom.xml', 'build.gradle', 'build.gradle.kts']):
            build_tool = 'maven' if 'pom.xml' in files else 'gradle'
            framework = self._detect_java_framework(path)
            
            return ProjectConfig(
                name=project_name,
                path=relative_path,
                language=Language.JAVA,
                framework=framework,
                build_tool=build_tool,
                test_command=f'{build_tool} test',
                dependencies=self._get_java_dependencies(path, build_tool),
                docker_enabled='Dockerfile' in files
            )
        
        # Go projects
        elif 'go.mod' in files:
            return ProjectConfig(
                name=project_name,
                path=relative_path,
                language=Language.GO,
                framework=None,
                build_tool='go',
                test_command='go test ./...',
                dependencies=self._get_go_dependencies(path),
                docker_enabled='Dockerfile' in files
            )
        
        return None
    
    def _detect_js_framework(self, path: Path) -> Optional[str]:
        """Detect JavaScript/TypeScript framework"""
        package_json_path = path / 'package.json'
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
            
            if 'react' in dependencies:
                return 'react'
            elif 'vue' in dependencies:
                return 'vue'
            elif '@angular/core' in dependencies:
                return 'angular'
            elif 'express' in dependencies:
                return 'express'
            elif 'next' in dependencies:
                return 'nextjs'
        
        return None
    
    def _detect_python_framework(self, path: Path) -> Optional[str]:
        """Detect Python framework"""
        # Check for Django
        if (path / 'manage.py').exists():
            return 'django'
        
        # Check for Flask
        files_content = self._get_python_file_contents(path)
        if any('from flask import' in content or 'import flask' in content for content in files_content):
            return 'flask'
        
        # Check for FastAPI
        if any('from fastapi import' in content or 'import fastapi' in content for content in files_content):
            return 'fastapi'
        
        return None
    
    def _detect_java_framework(self, path: Path) -> Optional[str]:
        """Detect Java framework"""
        # Check for Spring Boot
        if (path / 'pom.xml').exists():
            with open(path / 'pom.xml', 'r') as f:
                content = f.read()
                if 'spring-boot' in content:
                    return 'spring-boot'
        
        if (path / 'build.gradle').exists():
            with open(path / 'build.gradle', 'r') as f:
                content = f.read()
                if 'spring-boot' in content:
                    return 'spring-boot'
        
        return None
    
    def generate_pipeline_config(self, changed_files: Set[str]) -> Dict:
        """Generate pipeline configuration based on changed files"""
        affected_projects = self._get_affected_projects(changed_files)
        
        pipeline_config = {
            'projects': [],
            'global_stages': ['security_scan', 'license_check'],
            'integration_tests_required': len(affected_projects) > 1
        }
        
        for project_path, project in affected_projects.items():
            project_config = {
                'name': project.name,
                'path': project.path,
                'language': project.language.value,
                'framework': project.framework,
                'stages': self._generate_project_stages(project)
            }
            
            pipeline_config['projects'].append(project_config)
        
        return pipeline_config
    
    def _get_affected_projects(self, changed_files: Set[str]) -> Dict[str, ProjectConfig]:
        """Determine which projects are affected by changed files"""
        affected = {}
        
        for file_path in changed_files:
            for project_path, project in self.projects.items():
                if file_path.startswith(project_path):
                    affected[project_path] = project
                    break
        
        return affected
    
    def _generate_project_stages(self, project: ProjectConfig) -> List[Dict]:
        """Generate pipeline stages for a specific project"""
        stages = [
            {
                'name': 'build',
                'command': self._get_build_command(project),
                'working_directory': project.path
            },
            {
                'name': 'test',
                'command': project.test_command,
                'working_directory': project.path,
                'artifacts': self._get_test_artifacts(project)
            }
        ]
        
        # Add language-specific stages
        if project.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            stages.append({
                'name': 'lint',
                'command': 'npm run lint',
                'working_directory': project.path
            })
        
        elif project.language == Language.PYTHON:
            stages.extend([
                {
                    'name': 'lint',
                    'command': 'flake8 .',
                    'working_directory': project.path
                },
                {
                    'name': 'type_check',
                    'command': 'mypy .',
                    'working_directory': project.path
                }
            ])
        
        # Add Docker build if enabled
        if project.docker_enabled:
            stages.append({
                'name': 'docker_build',
                'command': f'docker build -t {project.name}:latest .',
                'working_directory': project.path
            })
        
        return stages
    
    def _get_build_command(self, project: ProjectConfig) -> str:
        """Get appropriate build command for project"""
        build_commands = {
            Language.JAVASCRIPT: 'npm run build',
            Language.TYPESCRIPT: 'npm run build',
            Language.PYTHON: 'pip install -r requirements.txt',
            Language.JAVA: f'{project.build_tool} compile',
            Language.GO: 'go build ./...',
        }
        
        return build_commands.get(project.language, 'echo "No build command defined"')
    
    def _get_test_artifacts(self, project: ProjectConfig) -> List[str]:
        """Get test artifacts for project"""
        artifact_patterns = {
            Language.JAVASCRIPT: ['coverage/**/*', 'test-results.xml'],
            Language.TYPESCRIPT: ['coverage/**/*', 'test-results.xml'],
            Language.PYTHON: ['htmlcov/**/*', 'coverage.xml', 'pytest.xml'],
            Language.JAVA: ['target/site/jacoco/**/*', 'target/surefire-reports/**/*'],
            Language.GO: ['coverage.out', 'test-results.xml'],
        }
        
        return artifact_patterns.get(project.language, [])

# Example usage
if __name__ == '__main__':
    repo_manager = PolyglotRepoManager(Path('.'))
    
    # Simulate changed files
    changed_files = {
        'services/user-service/src/main.js',
        'services/payment-service/pom.xml',
        'shared/auth/auth.py'
    }
    
    config = repo_manager.generate_pipeline_config(changed_files)
    print(json.dumps(config, indent=2))
```

This comprehensive CICD Source Code Integration guide provides enterprise-ready patterns for integrating version control systems with automated pipelines, ensuring code quality, and managing complex branching strategies across diverse technology stacks and compliance requirements.