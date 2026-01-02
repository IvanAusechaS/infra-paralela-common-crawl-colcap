#!/bin/bash

# ========================================
# Script: Validación completa del sistema
# ========================================
# Ejecuta todos los checks antes de desplegar en AWS

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}🔍 VALIDACIÓN COMPLETA DEL SISTEMA${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# ====================
# FASE 1: Docker
# ====================
echo -e "${BOLD}[1/6] Verificando Docker...${NC}"

if command -v docker >/dev/null 2>&1; then
  echo -e "${GREEN}✅ Docker instalado: $(docker --version)${NC}"
  
  # Verificar que Docker está corriendo
  if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker daemon está corriendo${NC}"
  else
    echo -e "${RED}❌ Docker daemon NO está corriendo${NC}"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo -e "${RED}❌ Docker NO está instalado${NC}"
  ERRORS=$((ERRORS + 1))
fi

echo ""

# ====================
# FASE 2: Docker Compose
# ====================
echo -e "${BOLD}[2/6] Verificando Docker Compose...${NC}"

if [ -f "backend/docker-compose.yml" ]; then
  echo -e "${GREEN}✅ docker-compose.yml existe${NC}"
  
  # Verificar sintaxis
  cd backend
  if docker-compose config >/dev/null 2>&1; then
    echo -e "${GREEN}✅ docker-compose.yml es válido${NC}"
  else
    echo -e "${RED}❌ docker-compose.yml tiene errores de sintaxis${NC}"
    ERRORS=$((ERRORS + 1))
  fi
  cd ..
else
  echo -e "${RED}❌ backend/docker-compose.yml NO existe${NC}"
  ERRORS=$((ERRORS + 1))
fi

echo ""

# ====================
# FASE 3: Dockerfiles
# ====================
echo -e "${BOLD}[3/6] Verificando Dockerfiles...${NC}"

DOCKERFILES=(
  "backend/api-gateway/Dockerfile"
  "backend/data-acquisition/Dockerfile"
  "backend/text-processor/Dockerfile"
  "backend/correlation-service/Dockerfile"
  "frontend/Dockerfile"
)

for dockerfile in "${DOCKERFILES[@]}"; do
  if [ -f "$dockerfile" ]; then
    echo -e "${GREEN}✅ $dockerfile existe${NC}"
  else
    echo -e "${RED}❌ $dockerfile NO existe${NC}"
    ERRORS=$((ERRORS + 1))
  fi
done

echo ""

# ====================
# FASE 4: Kubernetes manifests
# ====================
echo -e "${BOLD}[4/6] Verificando manifests de Kubernetes...${NC}"

REQUIRED_MANIFESTS=(
  "k8s/namespace.yaml"
  "k8s/configmap.yaml"
  "k8s/secrets.yaml"
  "k8s/postgres-statefulset.yaml"
  "k8s/redis-statefulset.yaml"
  "k8s/api-gateway-deployment.yaml"
  "k8s/data-acquisition-deployment.yaml"
  "k8s/text-processor-deployment.yaml"
  "k8s/correlation-service-deployment.yaml"
  "k8s/frontend-deployment.yaml"
  "k8s/text-processor-hpa.yaml"
  "k8s/metrics-server.yaml"
  "k8s/cluster-config.yaml"
)

for manifest in "${REQUIRED_MANIFESTS[@]}"; do
  if [ -f "$manifest" ]; then
    echo -e "${GREEN}✅ $manifest existe${NC}"
    
    # Validar YAML con kubectl (si está instalado)
    if command -v kubectl >/dev/null 2>&1; then
      if kubectl apply --dry-run=client -f "$manifest" >/dev/null 2>&1; then
        : # Silencioso si es válido
      else
        echo -e "${YELLOW}⚠️  $manifest tiene errores de sintaxis${NC}"
        WARNINGS=$((WARNINGS + 1))
      fi
    fi
  else
    echo -e "${RED}❌ $manifest NO existe${NC}"
    ERRORS=$((ERRORS + 1))
  fi
done

echo ""

# ====================
# FASE 5: Herramientas AWS
# ====================
echo -e "${BOLD}[5/6] Verificando herramientas AWS...${NC}"

# AWS CLI
if command -v aws >/dev/null 2>&1; then
  echo -e "${GREEN}✅ AWS CLI instalado: $(aws --version)${NC}"
  
  # Verificar credenciales
  if aws sts get-caller-identity >/dev/null 2>&1; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo -e "${GREEN}✅ Credenciales AWS configuradas (Account: $ACCOUNT_ID)${NC}"
  else
    echo -e "${YELLOW}⚠️  Credenciales AWS NO configuradas (ejecutar 'aws configure')${NC}"
    WARNINGS=$((WARNINGS + 1))
  fi
else
  echo -e "${YELLOW}⚠️  AWS CLI NO instalado (necesario para EKS)${NC}"
  WARNINGS=$((WARNINGS + 1))
fi

# kubectl
if command -v kubectl >/dev/null 2>&1; then
  echo -e "${GREEN}✅ kubectl instalado: $(kubectl version --client --short 2>/dev/null || kubectl version --client)${NC}"
else
  echo -e "${YELLOW}⚠️  kubectl NO instalado (necesario para Kubernetes)${NC}"
  WARNINGS=$((WARNINGS + 1))
fi

# eksctl
if command -v eksctl >/dev/null 2>&1; then
  echo -e "${GREEN}✅ eksctl instalado: $(eksctl version)${NC}"
else
  echo -e "${YELLOW}⚠️  eksctl NO instalado (necesario para crear cluster EKS)${NC}"
  WARNINGS=$((WARNINGS + 1))
fi

echo ""

# ====================
# FASE 6: Estructura de directorios
# ====================
echo -e "${BOLD}[6/6] Verificando estructura del proyecto...${NC}"

REQUIRED_DIRS=(
  "backend/api-gateway"
  "backend/data-acquisition"
  "backend/text-processor"
  "backend/correlation-service"
  "frontend"
  "k8s"
  "docs"
  "scripts"
)

for dir in "${REQUIRED_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo -e "${GREEN}✅ $dir/ existe${NC}"
  else
    echo -e "${RED}❌ $dir/ NO existe${NC}"
    ERRORS=$((ERRORS + 1))
  fi
done

echo ""

# ====================
# RESUMEN FINAL
# ====================
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}📊 RESUMEN DE VALIDACIÓN${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}${BOLD}✅ SISTEMA COMPLETAMENTE VALIDADO${NC}"
  echo ""
  echo "Todo está listo para:"
  echo "  1. Probar con Docker Compose: cd backend && docker-compose up"
  echo "  2. Probar con Minikube: ./scripts/prepare-local-manifests.sh"
  echo "  3. Desplegar en AWS EKS: ./scripts/build-and-push.sh && ./scripts/deploy-to-eks.sh"
  EXIT_CODE=0
elif [ $ERRORS -eq 0 ]; then
  echo -e "${YELLOW}${BOLD}⚠️  VALIDACIÓN CON ADVERTENCIAS${NC}"
  echo ""
  echo -e "${YELLOW}Advertencias: $WARNINGS${NC}"
  echo ""
  echo "Puedes proceder, pero revisa las advertencias."
  EXIT_CODE=0
else
  echo -e "${RED}${BOLD}❌ VALIDACIÓN FALLIDA${NC}"
  echo ""
  echo -e "${RED}Errores: $ERRORS${NC}"
  echo -e "${YELLOW}Advertencias: $WARNINGS${NC}"
  echo ""
  echo "Corrige los errores antes de continuar."
  EXIT_CODE=1
fi

echo ""
echo -e "${BOLD}========================================${NC}"

exit $EXIT_CODE
