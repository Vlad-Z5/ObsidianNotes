## Production Container-based Serverless

### Google Cloud Run Production Implementation

#### Cloud Run Service Configuration
```yaml
# cloudrun/service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: api-service
  namespace: production
  labels:
    cloud.googleapis.com/location: us-central1
    app: api-service
    environment: production
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/cpu-throttling: "false"  # Always allocate CPU
    run.googleapis.com/execution-environment: gen2
    run.googleapis.com/vpc-access-connector: production-connector
    run.googleapis.com/vpc-access-egress: private-ranges-only
spec:
  template:
    metadata:
      labels:
        app: api-service
        version: v1.2.3
      annotations:
        autoscaling.knative.dev/minScale: "1"     # Always keep 1 instance warm
        autoscaling.knative.dev/maxScale: "100"   # Scale up to 100 instances
        autoscaling.knative.dev/target: "70"      # Target 70 concurrent requests per instance
        run.googleapis.com/memory: "1Gi"
        run.googleapis.com/cpu: "1000m"
        run.googleapis.com/timeout: "300s"        # 5 minute timeout
        run.googleapis.com/startup-cpu-boost: "true"
    spec:
      containerConcurrency: 80  # Max concurrent requests per container
      timeoutSeconds: 300
      serviceAccountName: api-service@production-project.iam.gserviceaccount.com
      containers:
      - name: api-service
        image: gcr.io/production-project/api-service:v1.2.3
        ports:
        - name: http1
          containerPort: 8080
        env:
        - name: PORT
          value: "8080"
        - name: ENVIRONMENT
          value: "production"
        - name: PROJECT_ID
          value: "production-project"
        - name: DATABASE_HOST
          valueFrom:
            secretKeyRef:
              name: database-config
              key: host
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-config
              key: url
        - name: LOG_LEVEL
          value: "INFO"
        - name: GOOGLE_CLOUD_PROJECT
          value: "production-project"
        resources:
          requests:
            cpu: "1000m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 5
          failureThreshold: 10
          successThreshold: 1
        # Security context
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: true
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: var-log
          mountPath: /var/log
      volumes:
      - name: tmp
        emptyDir: {}
      - name: var-log
        emptyDir: {}
---
# IAM binding for Cloud Run service
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-service
  namespace: production
  annotations:
    iam.gke.io/gcp-service-account: api-service@production-project.iam.gserviceaccount.com
```

#### Production Dockerfile for Cloud Run
```dockerfile
# Dockerfile - Multi-stage production build
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production image
FROM node:18-alpine AS production

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Copy built application from builder stage
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package*.json ./

# Create necessary directories
RUN mkdir -p /tmp /var/log && chown nodejs:nodejs /tmp /var/log

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start application
CMD ["node", "dist/index.js"]
```

### AWS Fargate Serverless Implementation

#### Fargate Task Definition
```json
{
  "family": "api-service-production",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT-ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT-ID:role/api-service-task-role",
  "containerDefinitions": [
    {
      "name": "api-service",
      "image": "ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/api-service:v1.2.3",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/api-service-production",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      },
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        },
        {
          "name": "PORT",
          "value": "8080"
        },
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT-ID:secret:prod/database/url-ABCDEF"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT-ID:secret:prod/redis/url-GHIJKL"
        }
      ],
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8080/health || exit 1"
        ],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      },
      "stopTimeout": 30,
      "user": "1000:1000",
      "readonlyRootFilesystem": true,
      "linuxParameters": {
        "capabilities": {
          "drop": ["ALL"]
        }
      },
      "mountPoints": [
        {
          "sourceVolume": "tmp",
          "containerPath": "/tmp",
          "readOnly": false
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "tmp",
      "host": {}
    }
  ],
  "placementConstraints": [],
  "tags": [
    {
      "key": "Environment",
      "value": "production"
    },
    {
      "key": "Service",
      "value": "api-service"
    }
  ]
}
```

#### ECS Service with Auto Scaling
```json
{
  "serviceName": "api-service-production",
  "cluster": "production-cluster",
  "taskDefinition": "api-service-production:1",
  "desiredCount": 2,
  "launchType": "FARGATE",
  "platformVersion": "1.4.0",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": [
        "subnet-12345678",
        "subnet-87654321"
      ],
      "securityGroups": [
        "sg-api-service-production"
      ],
      "assignPublicIp": "DISABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:ACCOUNT-ID:targetgroup/api-service-prod/1234567890abcdef",
      "containerName": "api-service",
      "containerPort": 8080
    }
  ],
  "serviceRegistries": [
    {
      "registryArn": "arn:aws:servicediscovery:us-east-1:ACCOUNT-ID:service/srv-12345678",
      "containerName": "api-service"
    }
  ],
  "deploymentConfiguration": {
    "maximumPercent": 200,
    "minimumHealthyPercent": 50,
    "deploymentCircuitBreaker": {
      "enable": true,
      "rollback": true
    }
  },
  "enableExecuteCommand": true,
  "tags": [
    {
      "key": "Environment",
      "value": "production"
    }
  ]
}
```

### Container Serverless Deployment Script

```bash
#!/bin/bash
# scripts/container-serverless-deploy.sh - Production container serverless deployment

set -euo pipefail

readonly SERVICE_NAME="api-service"
readonly ENVIRONMENT="production"
readonly REGION="us-central1"  # For GCP
readonly AWS_REGION="us-east-1"  # For AWS

log_info() { echo -e "[$(date '+%H:%M:%S')] INFO: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] SUCCESS: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] WARN: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ERROR: $*"; }

# Deploy to Google Cloud Run
deploy_cloud_run() {
    local image_tag="$1"
    local project_id="$2"
    
    log_info "Deploying $SERVICE_NAME to Cloud Run with image: $image_tag"
    
    # Build image if needed
    if [[ "${BUILD_IMAGE:-false}" == "true" ]]; then
        build_and_push_image "$image_tag" "$project_id"
    fi
    
    # Deploy to Cloud Run
    gcloud run deploy "$SERVICE_NAME" \
        --image="gcr.io/${project_id}/${SERVICE_NAME}:${image_tag}" \
        --platform=managed \
        --region="$REGION" \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300s \
        --concurrency=80 \
        --min-instances=1 \
        --max-instances=100 \
        --set-env-vars="ENVIRONMENT=${ENVIRONMENT}" \
        --set-secrets="/secrets/database=database-config:latest" \
        --set-secrets="/secrets/redis=redis-config:latest" \
        --vpc-connector="production-connector" \
        --vpc-egress=private-ranges-only \
        --service-account="api-service@${project_id}.iam.gserviceaccount.com" \
        --labels="app=${SERVICE_NAME},environment=${ENVIRONMENT}" \
        --port=8080 \
        --no-cpu-throttling \
        --execution-environment=gen2 \
        --project="$project_id"
    
    # Wait for deployment to complete
    local service_url
    service_url=$(gcloud run services describe "$SERVICE_NAME" \
                 --platform=managed \
                 --region="$REGION" \
                 --project="$project_id" \
                 --format="value(status.url)")
    
    log_info "Cloud Run service URL: $service_url"
    
    # Health check
    if ! validate_cloud_run_deployment "$service_url"; then
        log_error "Cloud Run deployment validation failed"
        return 1
    fi
    
    # Configure traffic allocation if needed
    if [[ "${TRAFFIC_SPLIT:-}" == "true" ]]; then
        configure_cloud_run_traffic "$project_id"
    fi
    
    log_success "Cloud Run deployment completed successfully"
}

# Deploy to AWS Fargate
deploy_fargate() {
    local image_tag="$1"
    local cluster_name="$2"
    
    log_info "Deploying $SERVICE_NAME to Fargate with image: $image_tag"
    
    # Build and push image to ECR if needed
    if [[ "${BUILD_IMAGE:-false}" == "true" ]]; then
        build_and_push_ecr_image "$image_tag"
    fi
    
    # Register new task definition
    local task_definition_arn
    task_definition_arn=$(register_fargate_task_definition "$image_tag")
    
    if [[ -z "$task_definition_arn" ]]; then
        log_error "Failed to register task definition"
        return 1
    fi
    
    # Update ECS service
    log_info "Updating ECS service with new task definition"
    
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "${SERVICE_NAME}-${ENVIRONMENT}" \
        --task-definition "$task_definition_arn" \
        --region "$AWS_REGION"
    
    # Wait for deployment to complete
    log_info "Waiting for service deployment to complete..."
    
    if ! aws ecs wait services-stable \
         --cluster "$cluster_name" \
         --services "${SERVICE_NAME}-${ENVIRONMENT}" \
         --region "$AWS_REGION"; then
        log_error "ECS service deployment failed or timed out"
        return 1
    fi
    
    # Validate deployment
    if ! validate_fargate_deployment "$cluster_name"; then
        log_error "Fargate deployment validation failed"
        return 1
    fi
    
    log_success "Fargate deployment completed successfully"
}

# Build and push image to Google Container Registry
build_and_push_image() {
    local image_tag="$1"
    local project_id="$2"
    
    log_info "Building and pushing image: gcr.io/${project_id}/${SERVICE_NAME}:${image_tag}"
    
    # Configure Docker for GCR
    gcloud auth configure-docker --quiet
    
    # Build image
    docker build \
        --tag "gcr.io/${project_id}/${SERVICE_NAME}:${image_tag}" \
        --tag "gcr.io/${project_id}/${SERVICE_NAME}:latest" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        --cache-from "gcr.io/${project_id}/${SERVICE_NAME}:latest" \
        .
    
    # Push image
    docker push "gcr.io/${project_id}/${SERVICE_NAME}:${image_tag}"
    docker push "gcr.io/${project_id}/${SERVICE_NAME}:latest"
    
    log_success "Image pushed successfully"
}

# Build and push image to ECR
build_and_push_ecr_image() {
    local image_tag="$1"
    local account_id
    account_id=$(aws sts get-caller-identity --query Account --output text)
    local ecr_repo="${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${SERVICE_NAME}"
    
    log_info "Building and pushing image to ECR: ${ecr_repo}:${image_tag}"
    
    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$ecr_repo"
    
    # Create repository if it doesn't exist
    aws ecr describe-repositories --repository-names "$SERVICE_NAME" --region "$AWS_REGION" >/dev/null 2>&1 || \
        aws ecr create-repository --repository-name "$SERVICE_NAME" --region "$AWS_REGION"
    
    # Build image
    docker build \
        --tag "${ecr_repo}:${image_tag}" \
        --tag "${ecr_repo}:latest" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        .
    
    # Push image
    docker push "${ecr_repo}:${image_tag}"
    docker push "${ecr_repo}:latest"
    
    log_success "ECR image pushed successfully"
}

# Register Fargate task definition
register_fargate_task_definition() {
    local image_tag="$1"
    local account_id
    account_id=$(aws sts get-caller-identity --query Account --output text)
    local ecr_repo="${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${SERVICE_NAME}"
    
    # Create task definition JSON
    local task_def_file="/tmp/task-definition.json"
    
    cat > "$task_def_file" <<EOF
{
  "family": "${SERVICE_NAME}-${ENVIRONMENT}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::${account_id}:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::${account_id}:role/${SERVICE_NAME}-task-role",
  "containerDefinitions": [
    {
      "name": "${SERVICE_NAME}",
      "image": "${ecr_repo}:${image_tag}",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${SERVICE_NAME}-${ENVIRONMENT}",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      },
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "${ENVIRONMENT}"
        },
        {
          "name": "PORT",
          "value": "8080"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${account_id}:secret:${ENVIRONMENT}/database/url"
        }
      ],
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8080/health || exit 1"
        ],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF
    
    # Register task definition
    local task_def_arn
    task_def_arn=$(aws ecs register-task-definition \
                  --cli-input-json "file://${task_def_file}" \
                  --region "$AWS_REGION" \
                  --query 'taskDefinition.taskDefinitionArn' \
                  --output text)
    
    echo "$task_def_arn"
}

# Validate Cloud Run deployment
validate_cloud_run_deployment() {
    local service_url="$1"
    local max_attempts=30
    local attempt=1
    
    log_info "Validating Cloud Run deployment..."
    
    while [[ $attempt -le $max_attempts ]]; do
        # Health check
        if curl -sf "${service_url}/health" >/dev/null 2>&1; then
            log_success "Health check passed on attempt $attempt"
            
            # Additional validation
            local response
            response=$(curl -s "${service_url}/health")
            
            if echo "$response" | jq -e '.status == "healthy"' >/dev/null 2>&1; then
                log_success "Service is healthy and responding correctly"
                return 0
            fi
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 10s..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health check validation failed after $max_attempts attempts"
    return 1
}

# Validate Fargate deployment
validate_fargate_deployment() {
    local cluster_name="$1"
    
    log_info "Validating Fargate deployment..."
    
    # Check service status
    local service_info
    service_info=$(aws ecs describe-services \
                  --cluster "$cluster_name" \
                  --services "${SERVICE_NAME}-${ENVIRONMENT}" \
                  --region "$AWS_REGION")
    
    local running_count desired_count
    running_count=$(echo "$service_info" | jq -r '.services[0].runningCount')
    desired_count=$(echo "$service_info" | jq -r '.services[0].desiredCount')
    
    if [[ "$running_count" -ne "$desired_count" ]]; then
        log_error "Service not stable: running=$running_count, desired=$desired_count"
        return 1
    fi
    
    # Check task health
    local task_arns
    task_arns=$(aws ecs list-tasks \
               --cluster "$cluster_name" \
               --service-name "${SERVICE_NAME}-${ENVIRONMENT}" \
               --region "$AWS_REGION" \
               --query 'taskArns' \
               --output text)
    
    for task_arn in $task_arns; do
        local task_status
        task_status=$(aws ecs describe-tasks \
                     --cluster "$cluster_name" \
                     --tasks "$task_arn" \
                     --region "$AWS_REGION" \
                     --query 'tasks[0].lastStatus' \
                     --output text)
        
        if [[ "$task_status" != "RUNNING" ]]; then
            log_error "Task not running: $task_arn (status: $task_status)"
            return 1
        fi
    done
    
    log_success "Fargate deployment validation passed"
    return 0
}

# Configure Cloud Run traffic splitting
configure_cloud_run_traffic() {
    local project_id="$1"
    
    log_info "Configuring Cloud Run traffic allocation..."
    
    # Get current and previous revisions
    local revisions
    revisions=$(gcloud run revisions list \
               --service="$SERVICE_NAME" \
               --platform=managed \
               --region="$REGION" \
               --project="$project_id" \
               --sort-by="~metadata.creationTimestamp" \
               --limit=2 \
               --format="value(metadata.name)")
    
    local revision_array=($revisions)
    local latest_revision="${revision_array[0]}"
    local previous_revision="${revision_array[1]:-}"
    
    if [[ -n "$previous_revision" ]]; then
        # Split traffic 50/50 between latest and previous
        gcloud run services update-traffic "$SERVICE_NAME" \
            --to-revisions="${latest_revision}=50,${previous_revision}=50" \
            --platform=managed \
            --region="$REGION" \
            --project="$project_id"
        
        log_info "Traffic split configured: 50% to $latest_revision, 50% to $previous_revision"
    else
        log_info "No previous revision found, all traffic to latest revision"
    fi
}

# Monitor deployment metrics
monitor_deployment() {
    local platform="$1"  # cloudrun or fargate
    local duration="${2:-300}"  # 5 minutes default
    
    log_info "Monitoring deployment metrics for ${duration}s..."
    
    local end_time=$(($(date +%s) + duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        case "$platform" in
            "cloudrun")
                monitor_cloud_run_metrics
                ;;
            "fargate")
                monitor_fargate_metrics
                ;;
        esac
        
        sleep 30
    done
}

# Monitor Cloud Run metrics
monitor_cloud_run_metrics() {
    # Get request count and error rate using gcloud metrics
    local end_time_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local start_time_iso=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ)
    
    # This would integrate with Cloud Monitoring APIs
    log_info "Monitoring Cloud Run metrics (placeholder implementation)"
    
    # In practice, you would query Cloud Monitoring APIs here
    # Example metrics: request count, latency, error rate, instance count
}

# Monitor Fargate metrics
monitor_fargate_metrics() {
    # Get metrics from CloudWatch
    local end_time_iso=$(date -u +%Y-%m-%dT%H:%M:%S)
    local start_time_iso=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)
    
    # CPU utilization
    local cpu_utilization
    cpu_utilization=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/ECS" \
        --metric-name "CPUUtilization" \
        --dimensions Name=ServiceName,Value="${SERVICE_NAME}-${ENVIRONMENT}" \
        --start-time "$start_time_iso" \
        --end-time "$end_time_iso" \
        --period 300 \
        --statistics Average \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "0")
    
    # Memory utilization
    local memory_utilization
    memory_utilization=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/ECS" \
        --metric-name "MemoryUtilization" \
        --dimensions Name=ServiceName,Value="${SERVICE_NAME}-${ENVIRONMENT}" \
        --start-time "$start_time_iso" \
        --end-time "$end_time_iso" \
        --period 300 \
        --statistics Average \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "0")
    
    log_info "Fargate Metrics: CPU=${cpu_utilization}%, Memory=${memory_utilization}%"
}

# Main function
main() {
    local command="${1:-help}"
    local platform="${2:-}"
    local image_tag="${3:-}"
    
    case "$command" in
        "deploy-cloudrun")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            local project_id="${4:-$(gcloud config get-value project)}"
            deploy_cloud_run "$image_tag" "$project_id"
            ;;
        "deploy-fargate")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            local cluster_name="${4:-production-cluster}"
            deploy_fargate "$image_tag" "$cluster_name"
            ;;
        "monitor")
            [[ -z "$platform" ]] && { log_error "Platform (cloudrun|fargate) required"; exit 1; }
            monitor_deployment "$platform" "${3:-300}"
            ;;
        "build")
            [[ -z "$platform" ]] && { log_error "Platform (cloudrun|fargate) required"; exit 1; }
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            
            case "$platform" in
                "cloudrun")
                    local project_id="${4:-$(gcloud config get-value project)}"
                    build_and_push_image "$image_tag" "$project_id"
                    ;;
                "fargate")
                    build_and_push_ecr_image "$image_tag"
                    ;;
            esac
            ;;
        *)
            cat <<EOF
Container Serverless Deployment Tool

Usage: $0 <command> [options]

Commands:
  deploy-cloudrun <image-tag> [project-id]    - Deploy to Google Cloud Run
  deploy-fargate <image-tag> [cluster-name]   - Deploy to AWS Fargate
  monitor <platform> [duration]               - Monitor deployment metrics
  build <platform> <image-tag> [project/account] - Build and push container image

Examples:
  $0 deploy-cloudrun v1.2.3 my-project
  $0 deploy-fargate v1.2.3 production-cluster
  $0 monitor cloudrun 600
  $0 build fargate v1.2.3

Environment Variables:
  BUILD_IMAGE=true    - Build and push image during deployment
  TRAFFIC_SPLIT=true  - Enable traffic splitting (Cloud Run)
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive container-based serverless implementation for both Google Cloud Run and AWS Fargate with production-ready configurations, deployment automation, and monitoring capabilities.