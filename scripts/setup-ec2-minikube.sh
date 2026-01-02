#!/bin/bash
set -e

echo "🔧 Actualizando sistema..."
sudo yum update -y

echo "🐳 Instalando Docker..."
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

echo "📦 Instalando kubectl..."
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

echo "🎯 Instalando Minikube..."
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

echo "🚀 Iniciando Minikube..."
minikube start --driver=docker --cpus=2 --memory=3072

echo "📊 Habilitando metrics-server para HPA..."
minikube addons enable metrics-server

echo "✅ Instalación completada!"
echo ""
kubectl version --client
minikube version
docker --version
