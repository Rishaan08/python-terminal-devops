# Python Web Terminal - CI/CD Pipeline Project

## Overview
A fully automated CI/CD pipeline that builds, tests, and deploys a Python web terminal application using Jenkins, Docker, and Kubernetes.

## Architecture
- **Source Control**: GitHub
- **CI/CD**: Jenkins (with webhook automation)
- **Containerization**: Docker
- **Orchestration**: Kubernetes (Minikube)
- **Application**: Flask-based Python web terminal

## Components
1. **Flask Application** (`app.py`)
   - Web-based terminal interface
   - Command execution API
   - Real-time output display

2. **Docker Container**
   - Base: Python 3.9-slim
   - Exposed Port: 5001
   - Auto-built on code changes

3. **Kubernetes Deployment**
   - 2 replica pods for high availability
   - NodePort service (30080)
   - Auto-rolling updates

4. **Jenkins Pipeline**
   - Automated GitHub webhook triggers
   - Multi-stage pipeline (Clone → Build → Test → Deploy)
   - Console output logging

## Pipeline Stages
1. **Clone Repository** - Fetch latest code from GitHub
2. **Build Docker Image** - Create containerized application
3. **Run Tests** - Execute pytest suite
4. **Deploy to Kubernetes** - Rolling update deployment

## URLs
- **Application**: http://107.20.172.71:30080
- **Jenkins**: http://107.20.172.71:8080
- **GitHub Repo**: [Your repository URL]

## How It Works
1. Developer pushes code to GitHub
2. GitHub webhook triggers Jenkins build
3. Jenkins clones repository
4. Docker image is built with new code
5. Automated tests run
6. If tests pass, Kubernetes deployment updates
7. Application is live with zero downtime

## Testing the Pipeline
```bash
# Make a code change
vim templates/index.html

# Commit and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin main

# Watch Jenkins automatically build and deploy
```

## Project Structure
```
Devops/
├── app.py                 # Flask application
├── Dockerfile             # Container definition
├── deployment.yaml        # Kubernetes deployment
├── service.yaml          # Kubernetes service
├── requirements.txt      # Python dependencies
├── test_app.py          # Pytest tests
├── templates/
│   └── index.html       # Web terminal UI
├── Jenkinsfile          # Pipeline definition
└── README.md            # This file
```

## Commands Reference

### Docker Commands
```bash
# Build image
docker build -t python-terminal:latest .

# Run locally
docker run -p 5001:5001 python-terminal:latest

# List images
docker images
```

### Kubernetes Commands
```bash
# Apply deployment
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods
kubectl get deployments
kubectl get services

# View logs
kubectl logs <pod-name>

# Delete resources
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
```

### Git Commands
```bash
# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "Your message"

# Push to GitHub
git push origin main

# View history
git log --oneline
```

## Troubleshooting

### Jenkins Build Fails
```bash
# Check Jenkins logs
kubectl logs -n jenkins <jenkins-pod>

# Verify webhook
# GitHub repo → Settings → Webhooks → Check recent deliveries
```

### Pods Not Running
```bash
# Check pod status
kubectl get pods

# View pod logs
kubectl logs <pod-name>

# Describe pod
kubectl describe pod <pod-name>
```

### Application Not Accessible
```bash
# Check service
kubectl get svc python-terminal-service

# Verify NodePort
kubectl describe svc python-terminal-service

# Check Minikube IP
minikube ip
```

## Future Enhancements
- [ ] Add staging environment
- [ ] Implement blue-green deployment
- [ ] Add monitoring with Prometheus/Grafana
- [ ] Set up automated backups
- [ ] Add security scanning (Trivy/Snyk)
- [ ] Implement GitOps with ArgoCD
- [ ] Add load balancing
- [ ] Set up logging with ELK stack

## Author
Rishaan Yadav
Jayanth Nair
Dhruv Veragiwala

## License
MIT License
