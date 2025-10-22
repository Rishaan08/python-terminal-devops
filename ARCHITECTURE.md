# CI/CD Pipeline Architecture

## Flow Diagram
```
Developer → GitHub → Jenkins → Docker → Kubernetes → Production
    ↓         ↓         ↓         ↓          ↓            ↓
  Code     Webhook   Build    Image    Deployment    Live App
  Push     Trigger   Pipeline  Create   Update       (30080)
```

## Detailed Flow

1. **Code Change**
   - Developer modifies code locally
   - Commits changes with meaningful message
   - Pushes to GitHub main branch

2. **Webhook Trigger**
   - GitHub sends POST request to Jenkins
   - Jenkins receives webhook payload
   - New build is queued automatically

3. **Jenkins Pipeline Execution**
   - Stage 1: Clone repository from GitHub
   - Stage 2: Build Docker image with new code
   - Stage 3: Run automated tests (pytest)
   - Stage 4: Deploy to Kubernetes cluster

4. **Kubernetes Deployment**
   - Rolling update strategy (zero downtime)
   - Old pods gradually replaced with new ones
   - Health checks ensure stability
   - Service maintains consistent endpoint

5. **Production Access**
   - Application accessible at NodePort 30080
   - Load balanced across 2 replicas
   - Automatic pod recovery on failure

## Components Detail

### Jenkins Pipeline
- **Type**: Declarative Pipeline
- **Stages**: 4 (Clone, Build, Test, Deploy)
- **Trigger**: GitHub webhook
- **Agent**: Kubernetes pod

### Docker Image
- **Base**: python:3.9-slim
- **Size**: ~150MB
- **Registry**: Local Minikube
- **Tag**: Latest

### Kubernetes Resources
- **Deployment**: 2 replicas
- **Service**: NodePort (30080)
- **Strategy**: RollingUpdate
- **Namespace**: default

## Network Flow
```
Internet → EC2 (30080) → Minikube → Service → Pods → Containers
```

## Security Layers
1. GitHub authentication (personal access token)
2. Jenkins credentials management
3. Kubernetes RBAC
4. Docker image isolation
5. Network policies (can be added)
