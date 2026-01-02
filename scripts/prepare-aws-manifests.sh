#!/bin/bash
set -e

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "🔧 Preparando manifests para AWS..."
echo "ECR Registry: $ECR_REGISTRY"

# Crear directorio aws/ si no existe
mkdir -p k8s/aws

# Copiar todos los manifests
cp k8s/namespace.yaml k8s/aws/
cp k8s/configmap.yaml k8s/aws/
cp k8s/secrets.yaml k8s/aws/
cp k8s/*-deployment.yaml k8s/aws/
cp k8s/*-statefulset.yaml k8s/aws/
cp k8s/*-hpa.yaml k8s/aws/
cp k8s/metrics-server.yaml k8s/aws/

# Reemplazar ${ECR_REGISTRY} con el valor real
find k8s/aws/ -type f -name "*.yaml" -exec sed -i "s|\${ECR_REGISTRY}|$ECR_REGISTRY|g" {} \;

# Cambiar imagePullPolicy de Never a Always
find k8s/aws/ -type f -name "*.yaml" -exec sed -i "s|imagePullPolicy: Never|imagePullPolicy: Always|g" {} \;

# Agregar ENV: production al ConfigMap si no existe
grep -q "ENV:" k8s/aws/configmap.yaml || sed -i '/LOG_LEVEL:/i \  ENV: production' k8s/aws/configmap.yaml

# Cambiar API Gateway Service a LoadBalancer
sed -i 's/type: NodePort/type: LoadBalancer/' k8s/aws/api-gateway-deployment.yaml
sed -i '/nodePort:/d' k8s/aws/api-gateway-deployment.yaml
sed -i 's/port: 8000$/port: 80/' k8s/aws/api-gateway-deployment.yaml

# Agregar storageClassName: gp3 a StatefulSets
sed -i '/accessModes:/i \      storageClassName: gp3' k8s/aws/postgres-statefulset.yaml
sed -i '/accessModes:/i \      storageClassName: gp3' k8s/aws/redis-statefulset.yaml

# Aumentar storage a 5Gi mínimo
sed -i 's/storage: 1Gi/storage: 5Gi/g' k8s/aws/postgres-statefulset.yaml
sed -i 's/storage: 1Gi/storage: 5Gi/g' k8s/aws/redis-statefulset.yaml

echo "✅ Manifests preparados en k8s/aws/"
ls -la k8s/aws/
