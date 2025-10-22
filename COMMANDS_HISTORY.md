# Complete Commands History

## Initial Setup

### 1. Install Docker
```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### 2. Install Minikube
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
minikube start --driver=docker
```

### 3. Install kubectl
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### 4. Install Jenkins on Kubernetes
```bash
kubectl create namespace jenkins
kubectl apply -f https://raw.githubusercontent.com/jenkins-infra/jenkins.io/master/content/doc/tutorials/kubernetes/installing-jenkins-on-kubernetes/jenkins-deployment.yaml
```

## Project Setup

### 1. Create Project Directory
```bash
mkdir -p ~/Desktop/Devops
cd ~/Desktop/Devops
```

### 2. Initialize Git Repository
```bash
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 3. Create Application Files
```bash
# Created: app.py, Dockerfile, requirements.txt, templates/index.html
# Created: deployment.yaml, service.yaml, Jenkinsfile, test_app.py
```

### 4. Connect to GitHub
```bash
git remote add origin https://github.com/yourusername/python-terminal.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

## Jenkins Configuration

### 1. Get Jenkins Password
```bash
kubectl exec -n jenkins <jenkins-pod> -- cat /var/jenkins_home/secrets/initialAdminPassword
```

### 2. Configure Jenkins
- Installed suggested plugins
- Created admin user
- Installed Docker Pipeline plugin
- Installed Kubernetes plugin
- Created pipeline job

### 3. Add GitHub Webhook
- URL: http://107.20.172.71:8080/github-webhook/
- Content type: application/json
- Events: Just the push event

## Deployment Commands

### Build Docker Image
```bash
eval $(minikube docker-env)
docker build -t python-terminal:latest .
```

### Deploy to Kubernetes
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Verify Deployment
```bash
kubectl get pods
kubectl get deployments
kubectl get services
minikube service python-terminal-service --url
```

## Maintenance Commands

### View Logs
```bash
# Application logs
kubectl logs -f <pod-name>

# Jenkins logs
kubectl logs -n jenkins <jenkins-pod>
```

### Update Application
```bash
git add .
git commit -m "Update message"
git push origin main
# Jenkins automatically builds and deploys
```

### Restart Services
```bash
kubectl rollout restart deployment python-terminal
```

### Clean Up
```bash
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
docker rmi python-terminal:latest
```

## Troubleshooting Commands

### Check Pod Status
```bash
kubectl get pods -o wide
kubectl describe pod <pod-name>
```

### Check Service
```bash
kubectl get svc
kubectl describe svc python-terminal-service
```

### Check Jenkins
```bash
kubectl get pods -n jenkins
kubectl port-forward -n jenkins <jenkins-pod> 8080:8080
```

### Docker Commands
```bash
docker ps
docker images
docker logs <container-id>
```
