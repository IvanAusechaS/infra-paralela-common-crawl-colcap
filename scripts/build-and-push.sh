#!/bin/bash

# ========================================
# Script: Build y push de imágenes a ECR
# ========================================
# Construye todas las imágenes Docker y las sube a ECR

set -e

echo "🚀 Build y push de imágenes Docker a AWS ECR..."

# Verificar prerequisitos
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI no está instalado"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker no está instalado"; exit 1; }

# Obtener información de AWS
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "❌ No se pudo obtener Account ID. ¿AWS CLI configurado?"
  exit 1
fi

AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "✅ Account ID: $AWS_ACCOUNT_ID"
echo "✅ Region: $AWS_REGION"
echo "✅ ECR Registry: $ECR_REGISTRY"
echo ""

# Crear repositorios ECR si no existen
echo "📦 Verificando/creando repositorios ECR..."
SERVICES=("api-gateway" "data-acquisition" "text-processor" "correlation-service" "frontend")

for service in "${SERVICES[@]}"; do
  aws ecr describe-repositories --repository-names "news2market/$service" --region $AWS_REGION >/dev/null 2>&1 || \
  {
    echo "   Creando repositorio: news2market/$service"
    aws ecr create-repository --repository-name "news2market/$service" --region $AWS_REGION >/dev/null 2>&1
  }
done

echo "✅ Repositorios verificados"
echo ""

# Login a ECR
echo "🔐 Autenticando con ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

if [ $? -ne 0 ]; then
  echo "❌ Fallo el login a ECR"
  exit 1
fi

echo "✅ Login exitoso"
echo ""

# Build y push de cada servicio
cd "$(dirname "$0")/.."  # Ir a la raíz del proyecto

echo "🏗️  Construyendo y publicando imágenes..."
echo ""

# API Gateway
echo "📦 [1/5] api-gateway..."
docker build -t news2market/api-gateway:latest ./backend/api-gateway
docker tag news2market/api-gateway:latest $ECR_REGISTRY/news2market/api-gateway:latest
docker push $ECR_REGISTRY/news2market/api-gateway:latest
echo "✅ api-gateway publicado"
echo ""

# Data Acquisition
echo "📦 [2/5] data-acquisition..."
docker build -t news2market/data-acquisition:latest ./backend/data-acquisition
docker tag news2market/data-acquisition:latest $ECR_REGISTRY/news2market/data-acquisition:latest
docker push $ECR_REGISTRY/news2market/data-acquisition:latest
echo "✅ data-acquisition publicado"
echo ""

# Text Processor
echo "📦 [3/5] text-processor..."
docker build -t news2market/text-processor:latest ./backend/text-processor
docker tag news2market/text-processor:latest $ECR_REGISTRY/news2market/text-processor:latest
docker push $ECR_REGISTRY/news2market/text-processor:latest
echo "✅ text-processor publicado"
echo ""

# Correlation Service
echo "📦 [4/5] correlation-service..."
docker build -t news2market/correlation-service:latest ./backend/correlation-service
docker tag news2market/correlation-service:latest $ECR_REGISTRY/news2market/correlation-service:latest
docker push $ECR_REGISTRY/news2market/correlation-service:latest
echo "✅ correlation-service publicado"
echo ""

# Frontend
echo "📦 [5/5] frontend..."
docker build -t news2market/frontend:latest ./frontend
docker tag news2market/frontend:latest $ECR_REGISTRY/news2market/frontend:latest
docker push $ECR_REGISTRY/news2market/frontend:latest
echo "✅ frontend publicado"
echo ""

# Verificar imágenes en ECR
echo "🔍 Verificando imágenes en ECR..."
echo ""
for service in "${SERVICES[@]}"; do
  echo "📦 news2market/$service:"
  aws ecr describe-images --repository-name "news2market/$service" --region $AWS_REGION \
    --query 'imageDetails[0].[imagePushedAt,imageSizeInBytes,imageTags[0]]' \
    --output table 2>/dev/null || echo "   (vacío)"
done

echo ""
echo "=========================================="
echo "✅ TODAS LAS IMÁGENES PUBLICADAS EN ECR"
echo "=========================================="
echo ""
echo "Registry: $ECR_REGISTRY"
echo ""
echo "Siguiente paso:"
echo "   eksctl create cluster -f k8s/cluster-config.yaml"
echo "   # O usar: ./scripts/deploy-to-eks.sh"
