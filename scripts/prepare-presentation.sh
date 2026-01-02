#!/bin/bash

# =========================================
# Script de Preparación para Presentación
# News2Market - Infraestructura Paralela
# =========================================

set -e

EC2_IP="13.220.67.109"
SSH_KEY="$HOME/.ssh/news2market-key.pem"
NAMESPACE="news2market"

echo "🎯 Preparando sistema para presentación..."
echo "=========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para verificar
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        return 1
    fi
}

# 1. Verificar conexión SSH
echo "1. Verificando conexión a EC2..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@$EC2_IP "echo 'Conexión exitosa'" > /dev/null 2>&1
check_status "Conexión SSH establecida"
echo ""

# 2. Verificar pods
echo "2. Verificando estado de pods..."
POD_STATUS=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
    "sudo kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | grep -v Running | wc -l")

if [ "$POD_STATUS" -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los pods están Running${NC}"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
        "sudo kubectl get pods -n $NAMESPACE"
else
    echo -e "${YELLOW}⚠ Hay $POD_STATUS pods no Running${NC}"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
        "sudo kubectl get pods -n $NAMESPACE"
fi
echo ""

# 3. Verificar HPA
echo "3. Verificando HPA (Horizontal Pod Autoscaler)..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
    "sudo kubectl get hpa -n $NAMESPACE"
check_status "HPA configurado"
echo ""

# 4. Verificar métricas
echo "4. Verificando métricas del sistema..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
    "sudo kubectl top pods -n $NAMESPACE 2>/dev/null" || echo -e "${YELLOW}⚠ Esperando métricas...${NC}"
echo ""

# 5. Verificar servicios
echo "5. Verificando servicios..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
    "sudo kubectl get services -n $NAMESPACE"
check_status "Servicios activos"
echo ""

# 6. Verificar port-forwards
echo "6. Verificando port-forwards..."
PF_COUNT=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
    "pgrep -f 'kubectl.*port-forward' | wc -l")

if [ "$PF_COUNT" -ge 2 ]; then
    echo -e "${GREEN}✓ Port-forwards activos ($PF_COUNT)${NC}"
else
    echo -e "${YELLOW}⚠ Reactivando port-forwards...${NC}"
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP << 'EOF'
        pkill -f "kubectl.*port-forward" 2>/dev/null || true
        sleep 2
        sudo kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 --address 0.0.0.0 > /tmp/pf-api.log 2>&1 &
        sudo kubectl port-forward -n news2market svc/frontend-service 8080:80 --address 0.0.0.0 > /tmp/pf-frontend.log 2>&1 &
        sleep 3
        echo "Port-forwards reiniciados"
EOF
    check_status "Port-forwards reiniciados"
fi
echo ""

# 7. Verificar acceso web
echo "7. Verificando acceso web..."
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://$EC2_IP:8000/api/v1/health" | grep -q "200"; then
    echo -e "${GREEN}✓ API Gateway accesible (http://$EC2_IP:8000)${NC}"
else
    echo -e "${RED}✗ API Gateway no accesible${NC}"
fi

if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://$EC2_IP:8080" | grep -q "200"; then
    echo -e "${GREEN}✓ Frontend accesible (http://$EC2_IP:8080)${NC}"
else
    echo -e "${RED}✗ Frontend no accesible${NC}"
fi
echo ""

# 8. Verificar almacenamiento
echo "8. Verificando almacenamiento persistente..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
    "sudo kubectl get pvc -n $NAMESPACE"
check_status "Volúmenes persistentes"
echo ""

# 9. Verificar logs (últimas líneas sin errores)
echo "9. Verificando logs recientes..."
ERROR_COUNT=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP \
    "sudo kubectl logs deployment/api-gateway -n $NAMESPACE --tail=50 2>/dev/null | grep -i error | wc -l")

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ Sin errores en logs recientes${NC}"
else
    echo -e "${YELLOW}⚠ $ERROR_COUNT errores encontrados en logs${NC}"
fi
echo ""

# 10. Resumen del sistema
echo "10. Resumen del sistema..."
echo "=========================================="
ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$EC2_IP << 'EOF'
    echo "Nodo Kubernetes:"
    sudo kubectl get nodes
    echo ""
    echo "Recursos del cluster:"
    sudo kubectl top node 2>/dev/null || echo "Esperando métricas..."
    echo ""
    echo "Pods por servicio:"
    sudo kubectl get pods -n news2market | grep -E "NAME|Running" | wc -l
    echo "Pods Running: $(($(sudo kubectl get pods -n news2market --no-headers | grep Running | wc -l)))"
    echo ""
    echo "HPA Status:"
    sudo kubectl get hpa -n news2market --no-headers
EOF
echo ""

# Resumen final
echo "=========================================="
echo -e "${GREEN}✅ Sistema preparado para presentación${NC}"
echo ""
echo "📋 URLs importantes:"
echo "  - Frontend: http://$EC2_IP:8080"
echo "  - API Gateway: http://$EC2_IP:8000/api/v1/health"
echo ""
echo "🔧 Comandos útiles:"
echo "  - Conectar SSH: ssh -i $SSH_KEY ubuntu@$EC2_IP"
echo "  - Ver pods: sudo kubectl get pods -n $NAMESPACE"
echo "  - Ver métricas: sudo kubectl top pods -n $NAMESPACE"
echo "  - Ver logs: sudo kubectl logs -f deployment/NOMBRE -n $NAMESPACE"
echo ""
echo "🎯 ¡Listo para la presentación!"
