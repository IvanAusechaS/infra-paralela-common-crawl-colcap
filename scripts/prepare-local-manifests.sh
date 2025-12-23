#!/bin/bash

# ========================================
# Script: Preparar manifests para Minikube
# ========================================
# Convierte los manifests de EKS a versión local

set -e

echo "🔧 Preparando manifests para entorno local (Minikube/Kind)..."

# Directorio de destino
LOCAL_DIR="k8s/local"

# Crear directorio si no existe
mkdir -p $LOCAL_DIR

# Copiar todos los manifests
echo "📁 Copiando manifests..."
cp k8s/*.yaml $LOCAL_DIR/

# Reemplazar ${ECR_REGISTRY} con nombres locales
echo "🔄 Reemplazando referencias a ECR con imágenes locales..."
cd $LOCAL_DIR

for file in *.yaml; do
  # Reemplazar ECR_REGISTRY
  sed -i.bak 's|${ECR_REGISTRY}/news2market/|news2market/|g' "$file"
  sed -i.bak 's|${ECR_REGISTRY}/|news2market/|g' "$file"
  
  # Cambiar imagePullPolicy
  sed -i.bak 's|imagePullPolicy: Always|imagePullPolicy: Never|g' "$file"
  
  # Remover anotaciones de AWS Load Balancer
  sed -i.bak '/service.beta.kubernetes.io\/aws-load-balancer/d' "$file"
  
  # Cambiar LoadBalancer a ClusterIP para desarrollo local
  sed -i.bak 's|type: LoadBalancer|type: ClusterIP|g' "$file"
  
  # Limpiar archivos backup
  rm -f "$file.bak"
done

cd ../..

# Verificar cambios
echo ""
echo "✅ Manifests preparados en: $LOCAL_DIR/"
echo ""
echo "📋 Cambios realizados:"
echo "   - Imágenes: ${ECR_REGISTRY}/news2market/* → news2market/*"
echo "   - imagePullPolicy: Always → Never"
echo "   - Services: LoadBalancer → ClusterIP"
echo "   - Anotaciones AWS removidas"
echo ""
echo "🔍 Verificando imágenes en manifests:"
grep "image:" $LOCAL_DIR/*.yaml | grep -v "#"
echo ""
echo "✅ Listo para desplegar en Minikube/Kind"
echo ""
echo "Siguiente paso:"
echo "   eval \$(minikube docker-env)  # Configurar Docker para Minikube"
echo "   # Construir imágenes..."
echo "   kubectl apply -f k8s/local/"
