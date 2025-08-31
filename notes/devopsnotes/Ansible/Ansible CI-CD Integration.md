### Pipeline Integration Patterns
```yaml
# CI/CD Integration Strategies
cicd_patterns:
  push_model:
    description: "CI/CD system triggers Ansible directly"
    tools: ["Jenkins", "GitLab CI", "GitHub Actions", "Azure DevOps"]
    use_cases: ["Application deployment", "Infrastructure provisioning"]
    
  pull_model:
    description: "Ansible pulls configuration from SCM"
    tools: ["AWX/Tower", "Ansible Pull", "GitOps workflows"]
    use_cases: ["Configuration drift correction", "Scheduled updates"]
    
  hybrid_model:
    description: "Combination of push and pull patterns"
    tools: ["GitOps + CI/CD", "Event-driven automation"]
    use_cases: ["Complex multi-stage deployments", "Environment-specific workflows"]
```

## Jenkins Integration

### Jenkins Pipeline with Ansible
```groovy
// Jenkinsfile - Complete Ansible CI/CD Pipeline
pipeline {
    agent {
        kubernetes {
            yaml '''
                apiVersion: v1
                kind: Pod
                spec:
                  containers:
                  - name: ansible
                    image: quay.io/ansible/ansible-runner:2.12.0
                    command:
                    - cat
                    tty: true
                    volumeMounts:
                    - name: ansible-vault
                      mountPath: /etc/ansible-vault
                      readOnly: true
                  - name: terraform
                    image: hashicorp/terraform:1.3
                    command:
                    - cat
                    tty: true
                  volumes:
                  - name: ansible-vault
                    secret:
                      secretName: ansible-vault-secret
            '''
        }
    }
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['development', 'staging', 'production'],
            description: 'Target environment'
        )
        choice(
            name: 'DEPLOYMENT_STRATEGY',
            choices: ['rolling', 'blue-green', 'canary'],
            description: 'Deployment strategy'
        )
        string(
            name: 'APP_VERSION',
            defaultValue: 'latest',
            description: 'Application version to deploy'
        )
        booleanParam(
            name: 'RUN_SMOKE_TESTS',
            defaultValue: true,
            description: 'Run smoke tests after deployment'
        )
        booleanParam(
            name: 'ROLLBACK_ON_FAILURE',
            defaultValue: true,
            description: 'Automatic rollback on deployment failure'
        )
    }
    
    environment {
        ANSIBLE_HOST_KEY_CHECKING = 'False'
        ANSIBLE_FORCE_COLOR = 'True'
        VAULT_PASSWORD_FILE = '/etc/ansible-vault/password'
        AWS_DEFAULT_REGION = 'us-east-1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.BUILD_TIMESTAMP = sh(
                        script: 'date +%Y%m%d-%H%M%S',
                        returnStdout: true
                    ).trim()
                }
            }
        }
        
        stage('Validate') {
            parallel {
                stage('Syntax Check') {
                    steps {
                        container('ansible') {
                            sh '''
                                ansible-playbook \
                                    --syntax-check \
                                    --inventory=inventory/${ENVIRONMENT} \
                                    playbooks/site.yml
                            '''
                        }
                    }
                }
                
                stage('Lint Check') {
                    steps {
                        container('ansible') {
                            sh '''
                                ansible-lint \
                                    --exclude=.git \
                                    --exclude=.github \
                                    --format=pep8 \
                                    playbooks/
                            '''
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        container('ansible') {
                            sh '''
                                # Check for secrets in playbooks
                                grep -r -i "password\\|secret\\|key" playbooks/ || true
                                
                                # Validate vault files
                                find . -name "*vault*" -exec ansible-vault view {} \\; \
                                    --vault-password-file=${VAULT_PASSWORD_FILE}
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Plan') {
            steps {
                container('ansible') {
                    script {
                        // Generate deployment plan
                        sh '''
                            mkdir -p reports
                            
                            # Dry run to generate plan
                            ansible-playbook \
                                --check \
                                --diff \
                                --inventory=inventory/${ENVIRONMENT} \
                                --vault-password-file=${VAULT_PASSWORD_FILE} \
                                --extra-vars="app_version=${APP_VERSION}" \
                                --extra-vars="deployment_strategy=${DEPLOYMENT_STRATEGY}" \
                                --extra-vars="build_number=${BUILD_NUMBER}" \
                                --extra-vars="git_commit=${GIT_COMMIT_SHORT}" \
                                playbooks/site.yml \
                                > reports/deployment-plan.txt 2>&1 || true
                        '''
                        
                        // Archive the plan
                        archiveArtifacts artifacts: 'reports/deployment-plan.txt'
                        
                        // Display plan summary
                        def planContent = readFile('reports/deployment-plan.txt')
                        echo "Deployment Plan Summary:\\n${planContent.take(2000)}"
                    }
                }
            }
        }
        
        stage('Approval') {
            when {
                expression { params.ENVIRONMENT == 'production' }
            }
            steps {
                script {
                    def deploymentInfo = """
                    Deployment Details:
                    - Environment: ${params.ENVIRONMENT}
                    - Version: ${params.APP_VERSION}
                    - Strategy: ${params.DEPLOYMENT_STRATEGY}
                    - Build: ${BUILD_NUMBER}
                    - Commit: ${env.GIT_COMMIT_SHORT}
                    """
                    
                    def approval = input(
                        message: 'Approve production deployment?',
                        parameters: [
                            text(name: 'APPROVAL_NOTES', defaultValue: '', description: 'Approval notes'),
                            choice(name: 'APPROVED', choices: ['No', 'Yes'], description: 'Approve deployment?')
                        ],
                        submitterParameter: 'APPROVER'
                    )
                    
                    if (approval.APPROVED != 'Yes') {
                        error("Deployment not approved")
                    }
                    
                    env.APPROVER = approval.APPROVER
                    env.APPROVAL_NOTES = approval.APPROVAL_NOTES
                }
            }
        }
        
        stage('Pre-deployment') {
            steps {
                container('ansible') {
                    sh '''
                        # Pre-deployment health checks
                        ansible-playbook \
                            --inventory=inventory/${ENVIRONMENT} \
                            --vault-password-file=${VAULT_PASSWORD_FILE} \
                            --extra-vars="check_type=pre_deployment" \
                            playbooks/health-check.yml
                        
                        # Backup current state
                        ansible-playbook \
                            --inventory=inventory/${ENVIRONMENT} \
                            --vault-password-file=${VAULT_PASSWORD_FILE} \
                            --extra-vars="backup_type=pre_deployment" \
                            --extra-vars="backup_id=${BUILD_NUMBER}" \
                            playbooks/backup.yml
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                container('ansible') {
                    script {
                        try {
                            sh '''
                                # Main deployment
                                ansible-playbook \
                                    --inventory=inventory/${ENVIRONMENT} \
                                    --vault-password-file=${VAULT_PASSWORD_FILE} \
                                    --extra-vars="app_version=${APP_VERSION}" \
                                    --extra-vars="deployment_strategy=${DEPLOYMENT_STRATEGY}" \
                                    --extra-vars="build_number=${BUILD_NUMBER}" \
                                    --extra-vars="git_commit=${GIT_COMMIT_SHORT}" \
                                    --extra-vars="jenkins_build_url=${BUILD_URL}" \
                                    --extra-vars="approver=${APPROVER}" \
                                    playbooks/deploy.yml
                            '''
                            
                            currentBuild.result = 'SUCCESS'
                            
                        } catch (Exception e) {
                            currentBuild.result = 'FAILURE'
                            
                            if (params.ROLLBACK_ON_FAILURE) {
                                echo "Deployment failed, initiating rollback..."
                                sh '''
                                    ansible-playbook \
                                        --inventory=inventory/${ENVIRONMENT} \
                                        --vault-password-file=${VAULT_PASSWORD_FILE} \
                                        --extra-vars="backup_id=${BUILD_NUMBER}" \
                                        playbooks/rollback.yml
                                '''
                            }
                            
                            throw e
                        }
                    }
                }
            }
        }
        
        stage('Post-deployment') {
            parallel {
                stage('Health Check') {
                    steps {
                        container('ansible') {
                            sh '''
                                # Post-deployment health checks
                                ansible-playbook \
                                    --inventory=inventory/${ENVIRONMENT} \
                                    --vault-password-file=${VAULT_PASSWORD_FILE} \
                                    --extra-vars="check_type=post_deployment" \
                                    --extra-vars="app_version=${APP_VERSION}" \
                                    playbooks/health-check.yml
                            '''
                        }
                    }
                }
                
                stage('Smoke Tests') {
                    when {
                        expression { params.RUN_SMOKE_TESTS }
                    }
                    steps {
                        container('ansible') {
                            sh '''
                                # Run smoke tests
                                ansible-playbook \
                                    --inventory=inventory/${ENVIRONMENT} \
                                    --vault-password-file=${VAULT_PASSWORD_FILE} \
                                    --extra-vars="test_suite=smoke" \
                                    --extra-vars="app_version=${APP_VERSION}" \
                                    playbooks/test.yml
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Monitoring Setup') {
            steps {
                container('ansible') {
                    sh '''
                        # Configure monitoring for new deployment
                        ansible-playbook \
                            --inventory=inventory/${ENVIRONMENT} \
                            --vault-password-file=${VAULT_PASSWORD_FILE} \
                            --extra-vars="deployment_id=${BUILD_NUMBER}" \
                            --extra-vars="app_version=${APP_VERSION}" \
                            playbooks/monitoring.yml
                    '''
                }
            }
        }
    }
    
    post {
        always {
            // Archive deployment artifacts
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
            
            // Collect Ansible logs
            container('ansible') {
                sh '''
                    if [ -f /tmp/ansible.log ]; then
                        cp /tmp/ansible.log reports/ansible-execution.log
                    fi
                '''
            }
        }
        
        success {
            script {
                // Send success notification
                def message = """
                ✅ Deployment Successful
                Environment: ${params.ENVIRONMENT}
                Version: ${params.APP_VERSION}
                Strategy: ${params.DEPLOYMENT_STRATEGY}
                Build: ${BUILD_NUMBER}
                Duration: ${currentBuild.durationString}
                """.stripIndent()
                
                // Send to Slack/Teams/Email
                slackSend(
                    channel: '#deployments',
                    color: 'good',
                    message: message
                )
            }
        }
        
        failure {
            script {
                def message = """
                ❌ Deployment Failed
                Environment: ${params.ENVIRONMENT}
                Version: ${params.APP_VERSION}
                Build: ${BUILD_NUMBER}
                Logs: ${BUILD_URL}console
                """.stripIndent()
                
                slackSend(
                    channel: '#deployments',
                    color: 'danger',
                    message: message
                )
            }
        }
    }
}
```

### Jenkins Shared Library
```groovy
// vars/ansibleDeploy.groovy - Shared library for Ansible deployments
def call(Map config) {
    pipeline {
        agent any
        
        parameters {
            choice(
                name: 'ENVIRONMENT',
                choices: config.environments ?: ['dev', 'staging', 'prod'],
                description: 'Target environment'
            )
            string(
                name: 'VERSION',
                defaultValue: config.defaultVersion ?: 'latest',
                description: 'Application version'
            )
        }
        
        stages {
            stage('Validate Configuration') {
                steps {
                    script {
                        // Validate required configuration
                        def requiredKeys = ['playbook', 'inventory']
                        requiredKeys.each { key ->
                            if (!config.containsKey(key)) {
                                error("Required configuration key '${key}' is missing")
                            }
                        }
                    }
                }
            }
            
            stage('Run Ansible') {
                steps {
                    ansiblePlaybook(
                        playbook: config.playbook,
                        inventory: config.inventory + "/${params.ENVIRONMENT}",
                        credentialsId: config.credentialsId ?: 'ansible-ssh-key',
                        vaultCredentialsId: config.vaultCredentialsId ?: 'ansible-vault-password',
                        extraVars: [
                            app_version: params.VERSION,
                            environment: params.ENVIRONMENT,
                            build_number: BUILD_NUMBER,
                            jenkins_url: BUILD_URL
                        ] + (config.extraVars ?: [:]),
                        colorized: true,
                        disableHostKeyChecking: true
                    )
                }
            }
            
            stage('Post Deployment') {
                when {
                    expression { config.postDeployment }
                }
                steps {
                    script {
                        config.postDeployment.each { step ->
                            ansiblePlaybook(
                                playbook: step.playbook,
                                inventory: config.inventory + "/${params.ENVIRONMENT}",
                                credentialsId: config.credentialsId ?: 'ansible-ssh-key',
                                vaultCredentialsId: config.vaultCredentialsId ?: 'ansible-vault-password',
                                extraVars: step.extraVars ?: [:],
                                colorized: true,
                                disableHostKeyChecking: true
                            )
                        }
                    }
                }
            }
        }
        
        post {
            always {
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'reports',
                    reportFiles: '*.html',
                    reportName: 'Ansible Report'
                ])
            }
        }
    }
}

// Usage example in Jenkinsfile:
// ansibleDeploy([
//     playbook: 'playbooks/deploy.yml',
//     inventory: 'inventory',
//     environments: ['dev', 'staging', 'prod'],
//     postDeployment: [
//         [playbook: 'playbooks/health-check.yml'],
//         [playbook: 'playbooks/smoke-tests.yml']
//     ]
// ])
```

## GitLab CI Integration

### GitLab CI Pipeline
```yaml
# .gitlab-ci.yml - Complete GitLab CI/CD with Ansible
variables:
  ANSIBLE_HOST_KEY_CHECKING: "False"
  ANSIBLE_FORCE_COLOR: "True"
  DOCKER_DRIVER: overlay2
  VAULT_PASSWORD_FILE: "/tmp/vault_password"

stages:
  - validate
  - plan
  - deploy-dev
  - test-dev
  - deploy-staging
  - test-staging
  - approve-prod
  - deploy-prod
  - test-prod
  - notify

# Base job template
.ansible_base: &ansible_base
  image: quay.io/ansible/ansible-runner:2.12.0
  before_script:
    - echo "$VAULT_PASSWORD" > $VAULT_PASSWORD_FILE
    - chmod 600 $VAULT_PASSWORD_FILE
    - mkdir -p ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh-keyscan -H $DEPLOYMENT_HOSTS >> ~/.ssh/known_hosts 2>/dev/null || true
  after_script:
    - rm -f $VAULT_PASSWORD_FILE ~/.ssh/id_rsa

# Validation stage
ansible-lint:
  <<: *ansible_base
  stage: validate
  script:
    - ansible-lint --exclude=.git --format=pep8 playbooks/
  artifacts:
    reports:
      junit: reports/ansible-lint.xml
    paths:
      - reports/
    expire_in: 1 week

syntax-check:
  <<: *ansible_base
  stage: validate
  script:
    - |
      for env in dev staging prod; do
        echo "Checking syntax for $env environment"
        ansible-playbook \
          --syntax-check \
          --inventory=inventory/$env \
          playbooks/site.yml
      done

security-scan:
  <<: *ansible_base
  stage: validate
  script:
    - |
      # Check for hardcoded secrets
      echo "Scanning for hardcoded secrets..."
      grep -r -E "(password|secret|key)\s*[:=]\s*['\"][^'\"]*['\"]" playbooks/ && exit 1 || true
      
      # Validate all vault files can be decrypted
      echo "Validating vault files..."
      find . -name "*vault*" -type f | while read vault_file; do
        echo "Checking $vault_file"
        ansible-vault view "$vault_file" --vault-password-file=$VAULT_PASSWORD_FILE > /dev/null
      done

# Planning stage
generate-plan:
  <<: *ansible_base
  stage: plan
  script:
    - |
      mkdir -p reports
      for env in dev staging prod; do
        echo "Generating plan for $env environment"
        ansible-playbook \
          --check \
          --diff \
          --inventory=inventory/$env \
          --vault-password-file=$VAULT_PASSWORD_FILE \
          --extra-vars="app_version=$CI_COMMIT_TAG" \
          --extra-vars="build_number=$CI_PIPELINE_ID" \
          --extra-vars="git_commit=$CI_COMMIT_SHORT_SHA" \
          playbooks/site.yml > reports/plan-$env.txt 2>&1 || true
      done
  artifacts:
    paths:
      - reports/
    expire_in: 1 week

# Development deployment
deploy-dev:
  <<: *ansible_base
  stage: deploy-dev
  environment:
    name: development
    url: https://dev.app.company.com
  script:
    - |
      ansible-playbook \
        --inventory=inventory/dev \
        --vault-password-file=$VAULT_PASSWORD_FILE \
        --extra-vars="app_version=${CI_COMMIT_TAG:-latest}" \
        --extra-vars="environment=development" \
        --extra-vars="build_number=$CI_PIPELINE_ID" \
        --extra-vars="git_commit=$CI_COMMIT_SHORT_SHA" \
        --extra-vars="gitlab_pipeline_url=$CI_PIPELINE_URL" \
        playbooks/deploy.yml
  only:
    - develop
    - merge_requests
  artifacts:
    reports:
      junit: reports/deploy-dev.xml
    paths:
      - reports/
    expire_in: 1 week

test-dev:
  <<: *ansible_base
  stage: test-dev
  environment:
    name: development
  script:
    - |
      ansible-playbook \
        --inventory=inventory/dev \
        --vault-password-file=$VAULT_PASSWORD_FILE \
        --extra-vars="test_suite=integration" \
        --extra-vars="app_version=${CI_COMMIT_TAG:-latest}" \
        playbooks/test.yml
  dependencies:
    - deploy-dev
  only:
    - develop
    - merge_requests

# Staging deployment
deploy-staging:
  <<: *ansible_base
  stage: deploy-staging
  environment:
    name: staging
    url: https://staging.app.company.com
  script:
    - |
      ansible-playbook \
        --inventory=inventory/staging \
        --vault-password-file=$VAULT_PASSWORD_FILE \
        --extra-vars="app_version=$CI_COMMIT_TAG" \
        --extra-vars="environment=staging" \
        --extra-vars="build_number=$CI_PIPELINE_ID" \
        --extra-vars="git_commit=$CI_COMMIT_SHORT_SHA" \
        --extra-vars="deployment_strategy=blue-green" \
        playbooks/deploy.yml
  only:
    - tags
  when: manual

test-staging:
  <<: *ansible_base
  stage: test-staging
  environment:
    name: staging
  script:
    - |
      # Run comprehensive test suite
      ansible-playbook \
        --inventory=inventory/staging \
        --vault-password-file=$VAULT_PASSWORD_FILE \
        --extra-vars="test_suite=full" \
        --extra-vars="app_version=$CI_COMMIT_TAG" \
        playbooks/test.yml
  dependencies:
    - deploy-staging
  only:
    - tags

# Production approval
approve-production:
  stage: approve-prod
  image: alpine:latest
  script:
    - echo "Production deployment approved for version $CI_COMMIT_TAG"
  when: manual
  allow_failure: false
  only:
    - tags
  environment:
    name: production-approval

# Production deployment
deploy-prod:
  <<: *ansible_base
  stage: deploy-prod
  environment:
    name: production
    url: https://app.company.com
  script:
    - |
      # Pre-deployment backup
      ansible-playbook \
        --inventory=inventory/prod \
        --vault-password-file=$VAULT_PASSWORD_FILE \
        --extra-vars="backup_type=pre_deployment" \
        --extra-vars="backup_id=$CI_PIPELINE_ID" \
        playbooks/backup.yml
      
      # Main deployment with canary strategy
      ansible-playbook \
        --inventory=inventory/prod \
        --vault-password-file=$VAULT_PASSWORD_FILE \
        --extra-vars="app_version=$CI_COMMIT_TAG" \
        --extra-vars="environment=production" \
        --extra-vars="build_number=$CI_PIPELINE_ID" \
        --extra-vars="git_commit=$CI_COMMIT_SHORT_SHA" \
        --extra-vars="deployment_strategy=canary" \
        --extra-vars="canary_percentage=20" \
        playbooks/deploy.yml
  dependencies:
    - approve-production
  only:
    - tags
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure

test-prod:
  <<: *ansible_base
  stage: test-prod
  environment:
    name: production
  script:
    - |
      # Production smoke tests
      ansible-playbook \
        --inventory=inventory/prod \
        --vault-password-file=$VAULT_PASSWORD_FILE \
        --extra-vars="test_suite=smoke" \
        --extra-vars="app_version=$CI_COMMIT_TAG" \
        playbooks/test.yml
  dependencies:
    - deploy-prod
  only:
    - tags

# Notification stage
notify-success:
  stage: notify
  image: appropriate/curl:latest
  script:
    - |
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Deployment successful for $CI_PROJECT_NAME version $CI_COMMIT_TAG\"}" \
        $SLACK_WEBHOOK_URL
  when: on_success
  only:
    - tags

notify-failure:
  stage: notify
  image: appropriate/curl:latest
  script:
    - |
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"❌ Deployment failed for $CI_PROJECT_NAME version $CI_COMMIT_TAG. Pipeline: $CI_PIPELINE_URL\"}" \
        $SLACK_WEBHOOK_URL
  when: on_failure
  only:
    - tags
```

## GitHub Actions Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Ansible Deployment Pipeline

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - development
          - staging
          - production
      version:
        description: 'Version to deploy'
        required: true
        default: 'latest'
        type: string

env:
  ANSIBLE_HOST_KEY_CHECKING: False
  ANSIBLE_FORCE_COLOR: True
  PYTHON_VERSION: '3.10'

jobs:
  validate:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        ansible-galaxy install -r requirements.yml
    
    - name: Lint Ansible playbooks
      run: |
        ansible-lint --exclude=.github --format=pep8 playbooks/
    
    - name: Syntax check
      run: |
        for env in development staging production; do
          echo "Checking syntax for $env environment"
          ansible-playbook \
            --syntax-check \
            --inventory=inventory/$env \
            playbooks/site.yml
        done
    
    - name: Security scan
      run: |
        # Check for potential secrets
        grep -r -E "(password|secret|key)\s*[:=]\s*['\"][^'\"]*['\"]" playbooks/ && exit 1 || true
        echo "Security scan passed"
    
    - name: Set deployment matrix
      id: set-matrix
      run: |
        if [[ "${{ github.ref }}" == "refs/tags/v"* ]]; then
          echo "matrix={\"environment\":[\"development\",\"staging\",\"production\"]}" >> $GITHUB_OUTPUT
        elif [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
          echo "matrix={\"environment\":[\"development\",\"staging\"]}" >> $GITHUB_OUTPUT
        else
          echo "matrix={\"environment\":[\"development\"]}" >> $GITHUB_OUTPUT
        fi

  plan:
    runs-on: ubuntu-latest
    needs: validate
    strategy:
      matrix: ${{ fromJson(needs.validate.outputs.matrix) }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        ansible-galaxy install -r requirements.yml
    
    - name: Configure SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H ${{ secrets.DEPLOYMENT_HOSTS }} >> ~/.ssh/known_hosts 2>/dev/null || true
    
    - name: Generate deployment plan
      env:
        VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}
      run: |
        echo "$VAULT_PASSWORD" > /tmp/vault_password
        chmod 600 /tmp/vault_password
        
        mkdir -p reports
        ansible-playbook \
          --check \
          --diff \
          --inventory=inventory/${{ matrix.environment }} \
          --vault-password-file=/tmp/vault_password \
          --extra-vars="app_version=${{ github.ref_name }}" \
          --extra-vars="build_number=${{ github.run_number }}" \
          --extra-vars="git_commit=${{ github.sha }}" \
          playbooks/site.yml > reports/plan-${{ matrix.environment }}.txt 2>&1 || true
        
        rm -f /tmp/vault_password
    
    - name: Upload plan artifacts
      uses: actions/upload-artifact@v3
      with:
        name: deployment-plans
        path: reports/
        retention-days: 30

  deploy:
    runs-on: ubuntu-latest
    needs: [validate, plan]
    strategy:
      matrix: ${{ fromJson(needs.validate.outputs.matrix) }}
    environment: ${{ matrix.environment }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        ansible-galaxy install -r requirements.yml
    
    - name: Configure SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H ${{ secrets.DEPLOYMENT_HOSTS }} >> ~/.ssh/known_hosts 2>/dev/null || true
    
    - name: Deploy application
      env:
        VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}
      run: |
        echo "$VAULT_PASSWORD" > /tmp/vault_password
        chmod 600 /tmp/vault_password
        
        # Determine deployment strategy
        if [[ "${{ matrix.environment }}" == "production" ]]; then
          STRATEGY="canary"
        elif [[ "${{ matrix.environment }}" == "staging" ]]; then
          STRATEGY="blue-green"
        else
          STRATEGY="rolling"
        fi
        
        # Run deployment
        ansible-playbook \
          --inventory=inventory/${{ matrix.environment }} \
          --vault-password-file=/tmp/vault_password \
          --extra-vars="app_version=${{ github.ref_name }}" \
          --extra-vars="environment=${{ matrix.environment }}" \
          --extra-vars="build_number=${{ github.run_number }}" \
          --extra-vars="git_commit=${{ github.sha }}" \
          --extra-vars="deployment_strategy=$STRATEGY" \
          --extra-vars="github_run_url=${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}" \
          playbooks/deploy.yml
        
        rm -f /tmp/vault_password
    
    - name: Run post-deployment tests
      env:
        VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}
      run: |
        echo "$VAULT_PASSWORD" > /tmp/vault_password
        chmod 600 /tmp/vault_password
        
        ansible-playbook \
          --inventory=inventory/${{ matrix.environment }} \
          --vault-password-file=/tmp/vault_password \
          --extra-vars="test_suite=smoke" \
          --extra-vars="app_version=${{ github.ref_name }}" \
          playbooks/test.yml
        
        rm -f /tmp/vault_password
    
    - name: Generate deployment report
      if: always()
      run: |
        mkdir -p reports
        echo "# Deployment Report" > reports/deployment-${{ matrix.environment }}.md
        echo "- Environment: ${{ matrix.environment }}" >> reports/deployment-${{ matrix.environment }}.md
        echo "- Version: ${{ github.ref_name }}" >> reports/deployment-${{ matrix.environment }}.md
        echo "- Commit: ${{ github.sha }}" >> reports/deployment-${{ matrix.environment }}.md
        echo "- Status: ${{ job.status }}" >> reports/deployment-${{ matrix.environment }}.md
        echo "- Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")" >> reports/deployment-${{ matrix.environment }}.md
    
    - name: Upload deployment reports
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: deployment-reports-${{ matrix.environment }}
        path: reports/
        retention-days: 90

  notify:
    runs-on: ubuntu-latest
    needs: deploy
    if: always()
    
    steps:
    - name: Notify Slack on success
      if: needs.deploy.result == 'success'
      uses: rtCamp/action-slack-notify@v2
      env:
        SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
        SLACK_CHANNEL: deployments
        SLACK_COLOR: good
        SLACK_MESSAGE: |
          ✅ Deployment successful
          Version: ${{ github.ref_name }}
          Environments: ${{ join(fromJson(needs.validate.outputs.matrix).environment, ', ') }}
          Commit: ${{ github.sha }}
    
    - name: Notify Slack on failure
      if: needs.deploy.result == 'failure'
      uses: rtCamp/action-slack-notify@v2
      env:
        SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
        SLACK_CHANNEL: deployments
        SLACK_COLOR: danger
        SLACK_MESSAGE: |
          ❌ Deployment failed
          Version: ${{ github.ref_name }}
          Pipeline: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          Commit: ${{ github.sha }}
```

## Advanced CI/CD Patterns

### GitOps Integration with ArgoCD
```yaml
# argocd-application.yml - GitOps application definition
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: webapp-production
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  
  source:
    repoURL: https://github.com/company/k8s-manifests
    path: applications/webapp/overlays/production
    targetRevision: HEAD
    
    # Helm integration
    helm:
      valueFiles:
        - values-production.yaml
      parameters:
        - name: image.tag
          value: $ARGOCD_APP_SOURCE_TARGET_REVISION
  
  destination:
    server: https://kubernetes.default.svc
    namespace: webapp-production
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  
  # Health checks
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
  
  # Notification configuration
  operation:
    info:
      - name: "Deployment triggered by"
        value: "{{.app.operation.initiatedBy.username}}"
    sync:
      hook:
        force: true

---
# Ansible integration hook for GitOps
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: webapp-ansible-config
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/company/ansible-infrastructure
    path: k8s-integration/
    targetRevision: HEAD
    
    # Custom resource for Ansible execution
    plugin:
      name: ansible-plugin
      env:
        - name: ENVIRONMENT
          value: production
        - name: PLAYBOOK
          value: k8s-post-deploy.yml
  
  destination:
    server: https://kubernetes.default.svc
    namespace: ansible-runner
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: false
```

### Multi-Cloud Deployment Pipeline
```python
#!/usr/bin/env python3
"""
Multi-cloud deployment orchestrator using Ansible
"""
import asyncio
import json
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import subprocess
import yaml

@dataclass
class CloudEnvironment:
    name: str
    provider: str  # aws, azure, gcp
    region: str
    inventory_path: str
    vault_file: str
    ssh_key_path: str

@dataclass
class DeploymentConfig:
    app_version: str
    environments: List[CloudEnvironment]
    playbooks: Dict[str, str]
    parallelism: int = 3
    rollback_on_failure: bool = True

class MultiCloudDeployer:
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.deployment_results = {}
        
    async def deploy_all_environments(self) -> Dict[str, Any]:
        """Deploy to all environments in parallel"""
        self.logger.info(f"Starting deployment of version {self.config.app_version}")
        
        # Create semaphore to limit concurrent deployments
        semaphore = asyncio.Semaphore(self.config.parallelism)
        
        # Create deployment tasks
        tasks = []
        for env in self.config.environments:
            task = self.deploy_to_environment(env, semaphore)
            tasks.append(task)
        
        # Execute deployments
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        for i, result in enumerate(results):
            env_name = self.config.environments[i].name
            
            if isinstance(result, Exception):
                self.logger.error(f"Deployment to {env_name} failed: {result}")
                self.deployment_results[env_name] = {
                    'status': 'failed',
                    'error': str(result)
                }
                
                if self.config.rollback_on_failure:
                    await self.rollback_environment(self.config.environments[i])
            else:
                self.logger.info(f"Deployment to {env_name} successful")
                self.deployment_results[env_name] = {
                    'status': 'success',
                    'details': result
                }
                success_count += 1
        
        # Generate summary
        total_environments = len(self.config.environments)
        summary = {
            'total_environments': total_environments,
            'successful_deployments': success_count,
            'failed_deployments': total_environments - success_count,
            'success_rate': success_count / total_environments * 100,
            'results': self.deployment_results
        }
        
        return summary
    
    async def deploy_to_environment(self, env: CloudEnvironment, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Deploy to a single environment"""
        async with semaphore:
            self.logger.info(f"Deploying to {env.name} ({env.provider} - {env.region})")
            
            # Prepare deployment command
            cmd = self.build_ansible_command(env)
            
            # Execute deployment
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    self.run_ansible_deployment,
                    cmd,
                    env
                )
            
            return result
    
    def build_ansible_command(self, env: CloudEnvironment) -> List[str]:
        """Build Ansible command for environment"""
        base_cmd = [
            'ansible-playbook',
            '--inventory', env.inventory_path,
            '--vault-password-file', env.vault_file,
            '--private-key', env.ssh_key_path,
            '--extra-vars', json.dumps({
                'app_version': self.config.app_version,
                'environment': env.name,
                'cloud_provider': env.provider,
                'region': env.region,
                'deployment_timestamp': asyncio.get_event_loop().time()
            })
        ]
        
        # Add playbook
        playbook = self.config.playbooks.get(env.provider, self.config.playbooks['default'])
        base_cmd.append(playbook)
        
        return base_cmd
    
    def run_ansible_deployment(self, cmd: List[str], env: CloudEnvironment) -> Dict[str, Any]:
        """Execute Ansible deployment command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
                check=True
            )
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'execution_time': result.returncode  # Placeholder
            }
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Ansible deployment failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Deployment timed out after 30 minutes")
    
    async def rollback_environment(self, env: CloudEnvironment):
        """Rollback deployment in case of failure"""
        self.logger.warning(f"Rolling back deployment in {env.name}")
        
        rollback_cmd = [
            'ansible-playbook',
            '--inventory', env.inventory_path,
            '--vault-password-file', env.vault_file,
            '--private-key', env.ssh_key_path,
            self.config.playbooks.get('rollback', 'playbooks/rollback.yml')
        ]
        
        try:
            result = subprocess.run(
                rollback_cmd,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes timeout for rollback
                check=True
            )
            
            self.logger.info(f"Rollback successful for {env.name}")
            
        except Exception as e:
            self.logger.error(f"Rollback failed for {env.name}: {e}")

# Usage example
async def main():
    # Configuration
    environments = [
        CloudEnvironment(
            name='aws-us-east-1',
            provider='aws',
            region='us-east-1',
            inventory_path='inventory/aws/us-east-1',
            vault_file='/etc/ansible-vault/aws-password',
            ssh_key_path='/etc/ssh-keys/aws-key.pem'
        ),
        CloudEnvironment(
            name='azure-eastus',
            provider='azure',
            region='eastus',
            inventory_path='inventory/azure/eastus',
            vault_file='/etc/ansible-vault/azure-password',
            ssh_key_path='/etc/ssh-keys/azure-key.pem'
        ),
        CloudEnvironment(
            name='gcp-us-central1',
            provider='gcp',
            region='us-central1',
            inventory_path='inventory/gcp/us-central1',
            vault_file='/etc/ansible-vault/gcp-password',
            ssh_key_path='/etc/ssh-keys/gcp-key.pem'
        )
    ]
    
    config = DeploymentConfig(
        app_version='v2.1.0',
        environments=environments,
        playbooks={
            'aws': 'playbooks/aws-deploy.yml',
            'azure': 'playbooks/azure-deploy.yml',
            'gcp': 'playbooks/gcp-deploy.yml',
            'default': 'playbooks/generic-deploy.yml',
            'rollback': 'playbooks/rollback.yml'
        },
        parallelism=2,
        rollback_on_failure=True
    )
    
    # Execute deployment
    deployer = MultiCloudDeployer(config)
    results = await deployer.deploy_all_environments()
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    if results['failed_deployments'] > 0:
        exit(1)
    else:
        exit(0)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

This comprehensive CI/CD integration guide provides production-ready pipelines for major CI/CD platforms with advanced patterns like GitOps, multi-cloud deployments, and enterprise-grade automation workflows using Ansible.