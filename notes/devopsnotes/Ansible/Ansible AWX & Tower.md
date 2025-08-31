## Enterprise Automation Platform

### AWX vs Ansible Tower
- **AWX**: Open-source upstream project, community-supported
- **Ansible Tower**: Enterprise version with Red Hat support, additional features
- **Automation Controller**: New name for Ansible Tower in Automation Platform 2.x

## Architecture & Components

### Core Components
```yaml
# AWX/Tower Architecture
components:
  web_interface:
    description: "Web UI for managing automation"
    port: 80/443
    features:
      - Job management
      - Inventory visualization
      - User access control
      - Workflow designer
  
  api_server:
    description: "REST API for automation control"
    port: 80/443
    endpoints:
      - /api/v2/jobs/
      - /api/v2/inventories/
      - /api/v2/projects/
      - /api/v2/templates/
  
  task_engine:
    description: "Executes automation jobs"
    components:
      - Job dispatcher
      - Ansible playbook executor
      - Result processor
  
  database:
    description: "PostgreSQL backend"
    stores:
      - Job history
      - Inventories
      - Credentials
      - User data
  
  message_queue:
    description: "Redis/RabbitMQ for task distribution"
    purpose:
      - Job queuing
      - Real-time updates
      - Scaling coordination
```

## Installation & Configuration

### Docker Compose Installation (AWX)
```yaml
# docker-compose.yml
version: '3.7'

services:
  web:
    image: quay.io/ansible/awx:21.0.0
    container_name: awx_web
    depends_on:
      - redis
      - postgres
    ports:
      - "80:8052"
    environment:
      - SECRET_KEY=awxsecret
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=awx
      - DATABASE_USER=awx
      - DATABASE_PASSWORD=awxpass
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - awx_web_data:/var/lib/awx
      - ./projects:/var/lib/awx/projects:rw
    
  task:
    image: quay.io/ansible/awx:21.0.0
    container_name: awx_task
    depends_on:
      - redis
      - postgres
    environment:
      - SECRET_KEY=awxsecret
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=awx
      - DATABASE_USER=awx
      - DATABASE_PASSWORD=awxpass
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - awx_task_data:/var/lib/awx
      - ./projects:/var/lib/awx/projects:rw
    command: ["/usr/bin/launch_awx_task.sh"]

  redis:
    image: redis:6.2
    container_name: awx_redis
    volumes:
      - awx_redis_data:/data

  postgres:
    image: postgres:13
    container_name: awx_postgres
    environment:
      - POSTGRES_DB=awx
      - POSTGRES_USER=awx
      - POSTGRES_PASSWORD=awxpass
    volumes:
      - awx_postgres_data:/var/lib/postgresql/data

volumes:
  awx_web_data:
  awx_task_data:
  awx_redis_data:
  awx_postgres_data:
```

### Kubernetes Installation
```yaml
# awx-operator.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: awx
---
apiVersion: awx.ansible.com/v1beta1
kind: AWX
metadata:
  name: awx-production
  namespace: awx
spec:
  service_type: LoadBalancer
  ingress_type: ingress
  hostname: awx.company.com
  
  # Database configuration
  postgres_configuration_secret: awx-postgres-configuration
  postgres_storage_class: fast-ssd
  postgres_storage_requirements:
    requests:
      storage: 100Gi
  
  # Web/Task container resources
  web_resource_requirements:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  
  task_resource_requirements:
    requests:
      cpu: 2000m
      memory: 4Gi
    limits:
      cpu: 4000m
      memory: 8Gi
  
  # Redis configuration
  redis_resource_requirements:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi
  
  # Storage for projects
  projects_persistence: true
  projects_storage_class: standard
  projects_storage_size: 50Gi
  
  # Additional configurations
  replicas: 3
  admin_user: admin
  admin_email: admin@company.com
```

## Core Concepts & Management

### Organizations
```yaml
# Organization structure for enterprise
organizations:
  production:
    description: "Production environment management"
    users:
      - production_admins
      - production_operators
    projects:
      - production-infrastructure
      - production-applications
    inventories:
      - production-hosts
      - production-cloud-inventory
  
  staging:
    description: "Staging environment management"
    users:
      - staging_team
      - developers
    projects:
      - staging-infrastructure
      - application-testing
  
  development:
    description: "Development and testing"
    users:
      - development_team
      - qa_team
    projects:
      - dev-playground
      - feature-testing
```

### Projects (SCM Integration)
```yaml
# Git-based project configuration
project_configuration:
  name: "Production Infrastructure"
  organization: "production"
  scm_type: "git"
  scm_url: "https://github.com/company/ansible-infrastructure.git"
  scm_branch: "main"
  scm_credential: "github-deploy-key"
  
  # Advanced SCM settings
  scm_clean: true
  scm_delete_on_update: true
  scm_update_on_launch: true
  scm_update_cache_timeout: 300
  
  # Project sync webhook
  webhook_service: "github"
  webhook_credential: "github-webhook-secret"
  
  # Directory structure mapping
  playbook_directory: "playbooks/"
  roles_directory: "roles/"
  collections_directory: "collections/"
```

### Inventories & Smart Inventories
```yaml
# Dynamic inventory from cloud providers
cloud_inventory:
  name: "AWS Production Inventory"
  organization: "production"
  source: "amazon_aws"
  credential: "aws-production-readonly"
  
  # Source variables for AWS EC2
  source_vars:
    regions:
      - us-east-1
      - us-west-2
    filters:
      tag:Environment: production
      instance-state-name: running
    
    # Grouping configuration
    keyed_groups:
      - key: tags.Role
        prefix: role
      - key: tags.Environment
        prefix: env
      - key: placement.availability_zone
        prefix: az
    
    compose:
      ansible_host: public_ip_address | default(private_ip_address)
      instance_type: instance_type
      ansible_user: "'ec2-user' if image.name.find('RHEL') != -1 else 'ubuntu'"

# Smart Inventory for complex filtering
smart_inventory:
  name: "Web Servers Production"
  organization: "production"
  host_filter: 'group_names__contains="role_webserver" and group_names__contains="env_production"'
  
  # Additional filters
  filters:
    - 'instance_type__startswith="m5"'
    - 'tags__Environment="production"'
    - 'tags__Role="webserver"'
```

### Job Templates
```yaml
# Production deployment template
job_template:
  name: "Deploy Web Application"
  organization: "production"
  project: "production-infrastructure"
  playbook: "playbooks/deploy-webapp.yml"
  inventory: "production-hosts"
  credential: "production-ssh-key"
  
  # Execution configuration
  job_type: "run"
  verbosity: 1
  forks: 10
  timeout: 3600
  
  # Survey (runtime parameters)
  survey_enabled: true
  survey_spec:
    - variable: "app_version"
      question_name: "Application Version"
      question_description: "Version tag to deploy"
      type: "text"
      required: true
      default: "latest"
    
    - variable: "deployment_strategy"
      question_name: "Deployment Strategy"
      type: "multiplechoice"
      choices:
        - "blue-green"
        - "rolling"
        - "canary"
      default: "rolling"
    
    - variable: "run_smoke_tests"
      question_name: "Run smoke tests after deployment?"
      type: "boolean"
      default: true
  
  # Advanced options
  extra_vars:
    environment: "production"
    notification_email: "ops-team@company.com"
    rollback_enabled: true
  
  # Execution environment
  execution_environment: "production-ee"
  
  # Job scheduling
  schedule:
    name: "Nightly Deployment"
    rrule: "FREQ=DAILY;BYHOUR=2;BYMINUTE=0"
    enabled: true
```

## Workflows & Advanced Automation

### Complex Workflow Design
```yaml
# Multi-stage deployment workflow
deployment_workflow:
  name: "Full Application Deployment Pipeline"
  organization: "production"
  
  workflow_nodes:
    # Stage 1: Pre-deployment checks
    - identifier: "pre_checks"
      job_template: "Infrastructure Health Check"
      success_nodes: ["backup_database", "notify_start"]
      failure_nodes: ["notify_failure"]
    
    # Stage 2: Parallel backup and notification
    - identifier: "backup_database"
      job_template: "Database Backup"
      success_nodes: ["deploy_application"]
    
    - identifier: "notify_start"
      job_template: "Send Deployment Notification"
      success_nodes: ["deploy_application"]
    
    # Stage 3: Application deployment
    - identifier: "deploy_application"
      job_template: "Deploy Web Application"
      success_nodes: ["run_tests"]
      failure_nodes: ["rollback", "notify_failure"]
      
      # Conditional approval
      approval_node:
        name: "Production Deployment Approval"
        description: "Approve production deployment"
        timeout: 3600
    
    # Stage 4: Testing
    - identifier: "run_tests"
      job_template: "Smoke Tests"
      success_nodes: ["notify_success"]
      failure_nodes: ["rollback"]
    
    # Stage 5: Success/Failure handling
    - identifier: "notify_success"
      job_template: "Success Notification"
    
    - identifier: "rollback"
      job_template: "Rollback Application"
      always_nodes: ["notify_failure"]
    
    - identifier: "notify_failure"
      job_template: "Failure Notification"
  
  # Workflow variables
  extra_vars:
    max_fail_percentage: 10
    serial_execution: 3
    health_check_timeout: 300
```

### Custom Execution Environments
```dockerfile
# Custom execution environment
FROM registry.redhat.io/ubi8/python-39:latest

USER root

# Install system dependencies
RUN dnf update -y && \
    dnf install -y \
        git \
        rsync \
        openssh-clients \
        sshpass \
        && dnf clean all

# Install Python packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Ansible collections
COPY requirements.yml /tmp/
RUN ansible-galaxy collection install -r /tmp/requirements.yml

# Install custom modules and plugins
COPY plugins/ /usr/share/ansible/plugins/

# Set working directory
WORKDIR /runner

USER 1001
```

```yaml
# requirements.yml for execution environment
collections:
  - name: community.general
    version: ">=5.0.0"
  - name: ansible.posix
    version: ">=1.4.0"
  - name: community.crypto
    version: ">=2.0.0"
  - name: kubernetes.core
    version: ">=2.3.0"
  - name: amazon.aws
    version: ">=4.0.0"
  - name: azure.azcollection
    version: ">=1.13.0"
  - name: google.cloud
    version: ">=1.0.0"

# requirements.txt for Python packages
packages:
  - boto3>=1.24.0
  - botocore>=1.27.0
  - azure-identity>=1.10.0
  - azure-mgmt-compute>=27.0.0
  - google-cloud-compute>=1.5.0
  - kubernetes>=24.0.0
  - requests>=2.28.0
  - jinja2>=3.1.0
  - netaddr>=0.8.0
  - dnspython>=2.2.0
```

## Integration & API Usage

### REST API Integration
```python
#!/usr/bin/env python3
"""
AWX/Tower API integration example
"""
import requests
import json
import time
from typing import Dict, Any, Optional

class AWXClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def launch_job_template(self, template_id: int, extra_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        """Launch a job template with optional extra variables"""
        url = f"{self.base_url}/api/v2/job_templates/{template_id}/launch/"
        
        data = {}
        if extra_vars:
            data['extra_vars'] = json.dumps(extra_vars)
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """Get current job status"""
        url = f"{self.base_url}/api/v2/jobs/{job_id}/"
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_job(self, job_id: int, timeout: int = 3600, poll_interval: int = 10) -> Dict[str, Any]:
        """Wait for job completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            job_data = self.get_job_status(job_id)
            status = job_data.get('status')
            
            if status in ['successful', 'failed', 'error', 'canceled']:
                return job_data
            
            print(f"Job {job_id} status: {status}")
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
    
    def get_job_output(self, job_id: int) -> str:
        """Get job execution output"""
        url = f"{self.base_url}/api/v2/jobs/{job_id}/stdout/"
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json().get('content', '')
    
    def update_inventory_source(self, inventory_source_id: int) -> Dict[str, Any]:
        """Trigger inventory source update"""
        url = f"{self.base_url}/api/v2/inventory_sources/{inventory_source_id}/update/"
        response = self.session.post(url)
        response.raise_for_status()
        
        return response.json()

# Usage example
def deploy_application():
    awx = AWXClient(
        base_url="https://awx.company.com",
        username="automation-user",
        password="secure-password"
    )
    
    # Launch deployment
    deployment_vars = {
        "app_version": "v2.1.0",
        "deployment_strategy": "blue-green",
        "run_smoke_tests": True,
        "notification_email": "ops@company.com"
    }
    
    job_result = awx.launch_job_template(
        template_id=42,
        extra_vars=deployment_vars
    )
    
    job_id = job_result['id']
    print(f"Deployment job launched: {job_id}")
    
    # Wait for completion
    try:
        final_result = awx.wait_for_job(job_id, timeout=1800)
        
        if final_result['status'] == 'successful':
            print("Deployment completed successfully!")
        else:
            print(f"Deployment failed with status: {final_result['status']}")
            output = awx.get_job_output(job_id)
            print(f"Job output:\n{output}")
    
    except TimeoutError:
        print("Deployment timed out")

if __name__ == "__main__":
    deploy_application()
```

### CI/CD Pipeline Integration
```bash
#!/bin/bash
# Jenkins pipeline integration with AWX

set -euo pipefail

# Configuration
AWX_URL="https://awx.company.com"
AWX_TOKEN="${AWX_API_TOKEN}"
DEPLOYMENT_TEMPLATE_ID=42
TESTING_TEMPLATE_ID=43

# Function to make AWX API calls
awx_api_call() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"
    
    curl -s -X "${method}" \
         -H "Authorization: Bearer ${AWX_TOKEN}" \
         -H "Content-Type: application/json" \
         "${AWX_URL}/api/v2${endpoint}" \
         ${data:+-d "$data"}
}

# Function to wait for job completion
wait_for_job() {
    local job_id="$1"
    local timeout="${2:-1800}"
    local poll_interval="${3:-10}"
    local start_time
    
    start_time=$(date +%s)
    
    while true; do
        local current_time
        current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $timeout ]]; then
            echo "ERROR: Job $job_id timed out after ${timeout} seconds"
            return 1
        fi
        
        local job_status
        job_status=$(awx_api_call "GET" "/jobs/${job_id}/" | jq -r '.status')
        
        case "$job_status" in
            "successful")
                echo "Job $job_id completed successfully"
                return 0
                ;;
            "failed"|"error"|"canceled")
                echo "ERROR: Job $job_id failed with status: $job_status"
                awx_api_call "GET" "/jobs/${job_id}/stdout/" | jq -r '.content'
                return 1
                ;;
            *)
                echo "Job $job_id status: $job_status (elapsed: ${elapsed}s)"
                sleep "$poll_interval"
                ;;
        esac
    done
}

# Main deployment function
deploy_to_environment() {
    local environment="$1"
    local app_version="$2"
    
    echo "Deploying version $app_version to $environment"
    
    # Prepare deployment variables
    local extra_vars
    extra_vars=$(jq -n \
                    --arg env "$environment" \
                    --arg version "$app_version" \
                    --arg build_number "$BUILD_NUMBER" \
                    --arg git_commit "$GIT_COMMIT" \
                    '{
                        environment: $env,
                        app_version: $version,
                        build_number: $build_number,
                        git_commit: $git_commit,
                        deployment_strategy: "rolling",
                        health_check_enabled: true,
                        rollback_enabled: true
                    }')
    
    # Launch deployment job
    local job_data
    job_data=$(awx_api_call "POST" "/job_templates/${DEPLOYMENT_TEMPLATE_ID}/launch/" \
                           "{\"extra_vars\": $(echo "$extra_vars" | jq -c .)}")
    
    local job_id
    job_id=$(echo "$job_data" | jq -r '.id')
    
    echo "Deployment job launched: $job_id"
    echo "Job URL: ${AWX_URL}/#/jobs/playbook/${job_id}"
    
    # Wait for deployment completion
    if wait_for_job "$job_id" 1800; then
        echo "✅ Deployment to $environment completed successfully"
        
        # Launch post-deployment tests if in staging
        if [[ "$environment" == "staging" ]]; then
            echo "Running post-deployment tests..."
            local test_job_data
            test_job_data=$(awx_api_call "POST" "/job_templates/${TESTING_TEMPLATE_ID}/launch/" \
                                        "{\"extra_vars\": $(echo "$extra_vars" | jq -c .)}")
            
            local test_job_id
            test_job_id=$(echo "$test_job_data" | jq -r '.id')
            
            if wait_for_job "$test_job_id" 900; then
                echo "✅ Post-deployment tests passed"
            else
                echo "❌ Post-deployment tests failed"
                return 1
            fi
        fi
    else
        echo "❌ Deployment to $environment failed"
        return 1
    fi
}

# Pipeline stages
case "${1:-}" in
    "staging")
        deploy_to_environment "staging" "${APP_VERSION:-latest}"
        ;;
    "production")
        deploy_to_environment "production" "${APP_VERSION:-latest}"
        ;;
    *)
        echo "Usage: $0 {staging|production}"
        echo "Environment variables:"
        echo "  APP_VERSION - Application version to deploy"
        echo "  AWX_API_TOKEN - AWX authentication token"
        exit 1
        ;;
esac
```

## Monitoring & Observability

### Job Analytics & Reporting
```sql
-- AWX database queries for analytics
-- Job success rate by template
SELECT 
    jt.name as template_name,
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN j.status = 'successful' THEN 1 END) as successful_jobs,
    ROUND(
        COUNT(CASE WHEN j.status = 'successful' THEN 1 END) * 100.0 / COUNT(*), 2
    ) as success_rate
FROM main_job j
JOIN main_jobtemplate jt ON j.job_template_id = jt.id
WHERE j.created >= NOW() - INTERVAL '30 days'
GROUP BY jt.name
ORDER BY success_rate DESC;

-- Average execution time by template
SELECT 
    jt.name as template_name,
    AVG(EXTRACT(EPOCH FROM (j.finished - j.started))/60) as avg_duration_minutes,
    MIN(EXTRACT(EPOCH FROM (j.finished - j.started))/60) as min_duration_minutes,
    MAX(EXTRACT(EPOCH FROM (j.finished - j.started))/60) as max_duration_minutes
FROM main_job j
JOIN main_jobtemplate jt ON j.job_template_id = jt.id
WHERE j.status = 'successful' 
    AND j.finished IS NOT NULL 
    AND j.started IS NOT NULL
    AND j.created >= NOW() - INTERVAL '30 days'
GROUP BY jt.name
ORDER BY avg_duration_minutes DESC;
```

### Prometheus Monitoring Integration
```yaml
# Prometheus configuration for AWX monitoring
scrape_configs:
  - job_name: 'awx-metrics'
    static_configs:
      - targets: ['awx.company.com:8052']
    metrics_path: '/api/v2/metrics/'
    basic_auth:
      username: 'monitoring-user'
      password: 'monitoring-password'
    scrape_interval: 30s
    scrape_timeout: 10s

# Custom metrics via Python script
#!/usr/bin/env python3
"""
AWX metrics exporter for Prometheus
"""
import time
import requests
from prometheus_client import start_http_server, Gauge, Counter, Histogram

# Metrics definitions
job_duration = Histogram('awx_job_duration_seconds', 'Job execution time', ['template', 'status'])
job_total = Counter('awx_jobs_total', 'Total jobs executed', ['template', 'status'])
active_jobs = Gauge('awx_active_jobs', 'Currently running jobs')
queue_depth = Gauge('awx_job_queue_depth', 'Jobs waiting in queue')

class AWXMetricsExporter:
    def __init__(self, awx_url, username, password):
        self.awx_url = awx_url
        self.session = requests.Session()
        self.session.auth = (username, password)
    
    def collect_metrics(self):
        """Collect metrics from AWX API"""
        try:
            # Get active jobs
            active_response = self.session.get(f"{self.awx_url}/api/v2/jobs/", 
                                             params={'status': 'running'})
            active_jobs.set(active_response.json()['count'])
            
            # Get queued jobs
            queued_response = self.session.get(f"{self.awx_url}/api/v2/jobs/", 
                                             params={'status': 'pending'})
            queue_depth.set(queued_response.json()['count'])
            
            # Get recent job history
            recent_jobs = self.session.get(f"{self.awx_url}/api/v2/jobs/", 
                                         params={'created__gte': time.strftime('%Y-%m-%d', time.gmtime(time.time() - 3600))})
            
            for job in recent_jobs.json()['results']:
                template_name = job.get('job_template_name', 'unknown')
                status = job['status']
                
                # Update counters
                job_total.labels(template=template_name, status=status).inc()
                
                # Update duration histogram if job is complete
                if job.get('started') and job.get('finished'):
                    duration = (job['finished'] - job['started']).total_seconds()
                    job_duration.labels(template=template_name, status=status).observe(duration)
        
        except Exception as e:
            print(f"Error collecting metrics: {e}")

if __name__ == '__main__':
    exporter = AWXMetricsExporter(
        'https://awx.company.com',
        'monitoring-user',
        'monitoring-password'
    )
    
    # Start Prometheus metrics server
    start_http_server(8000)
    
    # Collect metrics every 30 seconds
    while True:
        exporter.collect_metrics()
        time.sleep(30)
```

This comprehensive guide covers enterprise-level AWX/Tower implementation with practical examples for deployment, automation workflows, API integration, and monitoring. The content provides production-ready configurations and real-world patterns for scaling Ansible automation in enterprise environments.