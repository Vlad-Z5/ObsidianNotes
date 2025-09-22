### GitHub Actions with Docker

```yaml
# .github/workflows/docker.yml
name: Docker Build and Push

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      if: github.event_name != 'pull_request'
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=semver,pattern={{major}}
          type=sha,prefix={{branch}}-

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        build-args: |
          BUILD_DATE=${{ steps.meta.outputs.created }}
          VCS_REF=${{ github.sha }}

    - name: Security scan with Trivy
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'
```

### GitLab CI with Docker

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - security
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  LATEST_TAG: $CI_REGISTRY_IMAGE:latest

services:
  - docker:20.10.16-dind

before_script:
  - echo $CI_REGISTRY_PASSWORD | docker login -u $CI_REGISTRY_USER --password-stdin $CI_REGISTRY

build:
  stage: build
  image: docker:20.10.16
  script:
    - docker build 
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
        --build-arg VCS_REF=$CI_COMMIT_SHA
        --cache-from $CI_REGISTRY_IMAGE:latest
        --tag $IMAGE_TAG
        --tag $LATEST_TAG
        .
    - docker push $IMAGE_TAG
    - docker push $LATEST_TAG
  only:
    - main
    - develop
    - merge_requests

test:
  stage: test
  image: docker:20.10.16
  script:
    - docker run --rm $IMAGE_TAG npm test
  dependencies:
    - build

security-scan:
  stage: security
  image: 
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy image --exit-code 0 --format template --template "@contrib/gitlab.tpl" -o gl-container-scanning-report.json $IMAGE_TAG
    - trivy image --exit-code 1 --severity CRITICAL $IMAGE_TAG
  artifacts:
    reports:
      container_scanning: gl-container-scanning-report.json
  dependencies:
    - build

deploy-staging:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" -d '{"image":"'$IMAGE_TAG'","environment":"staging"}'
  only:
    - develop

deploy-production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" -d '{"image":"'$IMAGE_TAG'","environment":"production"}'
  only:
    - main
  when: manual
```

### Jenkins Pipeline with Docker

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'myapp'
        DOCKER_CREDENTIALS = credentials('docker-registry-credentials')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                script {
                    def buildDate = new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone('UTC'))
                    def imageTag = "${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    def latestTag = "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
                    
                    docker.withRegistry("https://${DOCKER_REGISTRY}", env.DOCKER_CREDENTIALS) {
                        def image = docker.build(imageTag, 
                            "--build-arg BUILD_DATE=${buildDate} " +
                            "--build-arg VCS_REF=${env.GIT_COMMIT} " +
                            "--cache-from ${latestTag} ."
                        )
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        
        stage('Test') {
            steps {
                script {
                    def imageTag = "${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    docker.image(imageTag).inside {
                        sh 'npm test'
                    }
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                script {
                    def imageTag = "${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    sh """
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \\
                            aquasec/trivy:latest image --exit-code 1 --severity CRITICAL ${imageTag}
                    """
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    def imageTag = "${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    sh """
                        docker-compose -f docker-compose.staging.yml down
                        IMAGE_TAG=${imageTag} docker-compose -f docker-compose.staging.yml up -d
                    """
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                script {
                    def imageTag = "${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    sh """
                        docker-compose -f docker-compose.prod.yml down
                        IMAGE_TAG=${imageTag} docker-compose -f docker-compose.prod.yml up -d
                    """
                }
            }
        }
    }
    
    post {
        always {
            sh 'docker system prune -f'
        }
        failure {
            emailext (
                subject: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build failed. Check console output at ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

### Azure DevOps with Docker

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
  tags:
    include:
      - v*

variables:
  dockerRegistryServiceConnection: 'docker-registry-connection'
  imageRepository: 'myapp'
  containerRegistry: 'myregistry.azurecr.io'
  dockerfilePath: '$(Build.SourcesDirectory)/Dockerfile'
  tag: '$(Build.BuildId)'

stages:
- stage: Build
  displayName: Build and push stage
  jobs:
  - job: Build
    displayName: Build
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: Docker@2
      displayName: Build and push an image to container registry
      inputs:
        command: buildAndPush
        repository: $(imageRepository)
        dockerfile: $(dockerfilePath)
        containerRegistry: $(dockerRegistryServiceConnection)
        tags: |
          $(tag)
          latest
        arguments: |
          --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
          --build-arg VCS_REF=$(Build.SourceVersion)

    - task: AquaSecurityTrivy@4
      displayName: 'Aqua Security Trivy scan'
      inputs:
        image: '$(containerRegistry)/$(imageRepository):$(tag)'
        exitCode: 1
        severity: 'CRITICAL,HIGH'

- stage: Deploy
  displayName: Deploy stage
  dependsOn: Build
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - deployment: Deploy
    displayName: Deploy
    pool:
      vmImage: 'ubuntu-latest'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureWebAppContainer@1
            displayName: 'Azure Web App on Container Deploy'
            inputs:
              azureSubscription: 'azure-subscription'
              appName: 'myapp-prod'
              containers: '$(containerRegistry)/$(imageRepository):$(tag)'
```

### Docker Compose for CI/CD Environments

```yaml
# docker-compose.ci.yml - Optimized for CI/CD
version: '3.8'

services:
  web:
    build:
      context: .
      target: test
      cache_from:
        - myapp:latest
        - myapp:build-cache
    image: myapp:${BUILD_NUMBER:-latest}
    environment:
      - NODE_ENV=test
      - CI=true
    depends_on:
      - db
      - redis
    command: npm run test:ci

  db:
    image: postgres:13-alpine
    environment:
      POSTGRES_DB: myapp_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    tmpfs:
      - /var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    tmpfs:
      - /data

# docker-compose.staging.yml
version: '3.8'

services:
  web:
    image: myregistry.com/myapp:${IMAGE_TAG}
    environment:
      - NODE_ENV=staging
      - DATABASE_URL=${STAGING_DATABASE_URL}
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
    networks:
      - staging-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - web
    networks:
      - staging-network

networks:
  staging-network:
    driver: bridge
```

### Container Registry Integration

```bash
# Docker Hub
docker login
docker tag myapp:latest username/myapp:v1.0.0
docker push username/myapp:v1.0.0

# Amazon ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
docker tag myapp:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/myapp:v1.0.0
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/myapp:v1.0.0

# Google Container Registry
gcloud auth configure-docker
docker tag myapp:latest gcr.io/project-id/myapp:v1.0.0
docker push gcr.io/project-id/myapp:v1.0.0

# Azure Container Registry
az acr login --name myregistry
docker tag myapp:latest myregistry.azurecr.io/myapp:v1.0.0
docker push myregistry.azurecr.io/myapp:v1.0.0

# GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u username --password-stdin
docker tag myapp:latest ghcr.io/username/myapp:v1.0.0
docker push ghcr.io/username/myapp:v1.0.0
```

### CI/CD Best Practices

```bash
# Multi-stage build for CI/CD
FROM node:16-alpine AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:16-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN npm run test

FROM node:16-alpine AS runtime
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package*.json ./
USER 1001
EXPOSE 3000
CMD ["node", "dist/server.js"]

# Cache optimization for CI/CD
# Use BuildKit cache mounts
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production

# Use registry cache
docker build --cache-from myapp:latest --tag myapp:$BUILD_NUMBER .

# Parallel builds
docker build --platform linux/amd64,linux/arm64 --tag myapp:$BUILD_NUMBER .
```

### Deployment Strategies

```yaml
# Blue-Green Deployment with Docker Compose
# docker-compose.blue.yml
version: '3.8'
services:
  web-blue:
    image: myapp:${NEW_VERSION}
    environment:
      - SLOT=blue
    networks:
      - app-network

# docker-compose.green.yml  
version: '3.8'
services:
  web-green:
    image: myapp:${NEW_VERSION}
    environment:
      - SLOT=green
    networks:
      - app-network

# Rolling update script
#!/bin/bash
NEW_VERSION=$1
CURRENT_SLOT=$(docker-compose ps --services --filter status=running | grep web- | head -1 | cut -d'-' -f2)

if [ "$CURRENT_SLOT" = "blue" ]; then
    NEW_SLOT="green"
else
    NEW_SLOT="blue"
fi

# Deploy to new slot
NEW_VERSION=$NEW_VERSION docker-compose -f docker-compose.$NEW_SLOT.yml up -d

# Health check
sleep 30
if curl -f http://localhost:8080/health; then
    # Switch traffic
    docker-compose -f docker-compose.$CURRENT_SLOT.yml down
    echo "Deployment successful. Traffic switched to $NEW_SLOT"
else
    # Rollback
    docker-compose -f docker-compose.$NEW_SLOT.yml down
    echo "Deployment failed. Rolled back to $CURRENT_SLOT"
    exit 1
fi
```