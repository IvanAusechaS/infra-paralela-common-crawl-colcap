#!/bin/bash

# ====================
# Script de Despliegue Completo a AWS EKS
# ====================
# Uso: ./scripts/deploy-to-eks.sh

set -e  # Salir si hay error

echo "🚀 Iniciando despliegue de News2Market en AWS EKS..."

# ====================
# 1. Verificar prerequisitos
# ====================
echo ""
echo "📋 Verificando prerequisitos..."

command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI no está instalado"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl no está instalado"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker no está instalado"; exit 1; }

echo "✅ AWS CLI: $(aws --version)"
echo "✅ kubectl: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
echo "✅ Docker: $(docker --version)"

# ====================
# 2. Obtener información de AWS
# ====================
echo ""
echo "🔑 Obteniendo información de AWS..."

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME=${CLUSTER_NAME:-news2market-cluster}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "✅ Account ID: $AWS_ACCOUNT_ID"
echo "✅ Region: $AWS_REGION"
echo "✅ ECR Registry: $ECR_REGISTRY"
echo "✅ Cluster Name: $CLUSTER_NAME"

# ====================
# 3. Crear repositorios ECR si no existen
# ====================
echo ""
echo "📦 Creando repositorios ECR..."

SERVICES=("api-gateway" "data-acquisition" "text-processor" "correlation-service" "frontend")

for service in "${SERVICES[@]}"; do
  aws ecr describe-repositories --repository-names "news2market/$service" --region $AWS_REGION >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name "news2market/$service" --region $AWS_REGION >/dev/null 2>&1
  echo "✅ Repositorio: news2market/$service"
done

# ====================
# 4. Login a ECR
# ====================
echo ""
echo "🔐 Autenticando con ECR..."

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

echo "✅ Login exitoso"

# ====================
# 5. Build y Push de imágenes
# ====================
echo ""
echo "🏗️  Construyendo y publicando imágenes Docker..."

cd "$(dirname "$0")/.."  # Ir a la raíz del proyecto

# API Gateway
echo "  📦 api-gateway..."
docker build -t news2market/api-gateway:latest ./backend/api-gateway
docker tag news2market/api-gateway:latest $ECR_REGISTRY/news2market/api-gateway:latest
docker push $ECR_REGISTRY/news2market/api-gateway:latest

# Data Acquisition
echo "  📦 data-acquisition..."
docker build -t news2market/data-acquisition:latest ./backend/data-acquisition
docker tag news2market/data-acquisition:latest $ECR_REGISTRY/news2market/data-acquisition:latest
docker push $ECR_REGISTRY/news2market/data-acquisition:latest

# Text Processor
echo "  📦 text-processor..."
docker build -t news2market/text-processor:latest ./backend/text-processor
docker tag news2market/text-processor:latest $ECR_REGISTRY/news2market/text-processor:latest
docker push $ECR_REGISTRY/news2market/text-processor:latest

# Correlation Service
echo "  📦 correlation-service..."
docker build -t news2market/correlation-service:latest ./backend/correlation-service
docker tag news2market/correlation-service:latest $ECR_REGISTRY/news2market/correlation-service:latest
docker push $ECR_REGISTRY/news2market/correlation-service:latest

# Frontend
echo "  📦 frontend..."
docker build -t news2market/frontend:latest ./frontend
docker tag news2market/frontend:latest $ECR_REGISTRY/news2market/frontend:latest
docker push $ECR_REGISTRY/news2market/frontend:latest

echo "✅ Todas las imágenes publicadas"

# ====================
# 6. Configurar kubectl para EKS
# ====================
echo ""
echo "⚙️  Configurando kubectl para EKS..."

aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

echo "✅ kubectl configurado"
kubectl get nodes

# ====================
# 7. Actualizar manifests con ECR Registry
# ====================
echo ""
echo "🔧 Actualizando manifests con ECR registry..."

# Crear directorio temporal
TEMP_DIR=$(mktemp -d)
cp -r k8s/* $TEMP_DIR/

# Reemplazar ${ECR_REGISTRY} en todos los archivos
for file in $TEMP_DIR/*.yaml; do
  sed -i.bak "s|\${ECR_REGISTRY}|$ECR_REGISTRY|g" "$file"
  rm -f "$file.bak"
done

echo "✅ Manifests actualizados en $TEMP_DIR"

# ====================
# 8. Desplegar en Kubernetes
# ====================
echo ""
echo "☸️  Desplegando en Kubernetes..."

# Namespace
echo "  📁 Creando namespace..."
kubectl apply -f $TEMP_DIR/namespace.yaml

# ConfigMaps y Secrets
echo "  🔐 Aplicando ConfigMaps y Secrets..."
kubectl apply -f $TEMP_DIR/configmap.yaml
kubectl apply -f $TEMP_DIR/secrets.yaml

# Bases de datos
echo "  🗄️  Desplegando PostgreSQL y Redis..."
kubectl apply -f $TEMP_DIR/postgres-statefulset.yaml
kubectl apply -f $TEMP_DIR/redis-statefulset.yaml

# Esperar a que las bases de datos estén listas
echo "  ⏳ Esperando a que PostgreSQL esté listo..."
kubectl wait --for=condition=ready pod -l app=postgres -n news2market --timeout=300s

echo "  ⏳ Esperando a que Redis esté listo..."
kubectl wait --for=condition=ready pod -l app=redis -n news2market --timeout=300s

# Metrics Server (para HPA)
echo "  📊 Desplegando Metrics Server..."
kubectl apply -f $TEMP_DIR/metrics-server.yaml

# Microservicios
echo "  🚀 Desplegando microservicios..."
kubectl apply -f $TEMP_DIR/api-gateway-deployment.yaml
kubectl apply -f $TEMP_DIR/data-acquisition-deployment.yaml
kubectl apply -f $TEMP_DIR/text-processor-deployment.yaml
kubectl apply -f $TEMP_DIR/correlation-service-deployment.yaml
kubectl apply -f $TEMP_DIR/frontend-deployment.yaml

# HPA
echo "  📈 Configurando autoescalado..."
kubectl apply -f $TEMP_DIR/text-processor-hpa.yaml

# ====================
# 9. Verificar despliegue
# ====================
echo ""
echo "🔍 Verificando despliegue..."
echo ""

kubectl get pods -n news2market
echo ""
kubectl get svc -n news2market
echo ""
kubectl get hpa -n news2market

# ====================
# 10. Obtener URL del Load Balancer
# ====================
echo ""
echo "🌐 Obteniendo URL del Load Balancer..."
echo ""
echo "⏳ Esperando a que el Load Balancer esté disponible (esto puede tardar 2-3 minutos)..."

# Esperar a que el Load Balancer tenga hostname
for i in {1..60}; do
  FRONTEND_URL=$(kubectl get svc frontend-service -n news2market -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
  if [ -n "$FRONTEND_URL" ]; then
    break
  fi
  echo "  Intento $i/60..."
  sleep 5
done

API_GATEWAY_URL=$(kubectl get svc api-gateway-service -n news2market -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)

# ====================
# 11. Resumen final
# ====================
echo ""
echo "=========================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "=========================================="
echo ""
echo "🌐 URLs de acceso:"
echo ""
if [ -n "$FRONTEND_URL" ]; then
  echo "  Frontend:    http://$FRONTEND_URL"
else
  echo "  Frontend:    ⏳ Obtener con: kubectl get svc frontend-service -n news2market"
fi

if [ -n "$API_GATEWAY_URL" ]; then
  echo "  API Gateway: http://$API_GATEWAY_URL"
else
  echo "  API Gateway: ⏳ Obtener con: kubectl get svc api-gateway-service -n news2market"
fi
echo ""
echo "📊 Verificar estado:"
echo "  kubectl get pods -n news2market"
echo "  kubectl get hpa -n news2market"
echo "  kubectl logs -f -n news2market -l app=text-processor"
echo ""
echo "🧹 Limpiar recursos temporales:"
rm -rf $TEMP_DIR
echo "✅ Recursos temporales eliminados"
echo ""
echo "=========================================="
