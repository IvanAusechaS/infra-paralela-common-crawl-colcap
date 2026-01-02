#!/bin/bash

# ========================================
# Script: Test de escalabilidad en Minikube
# ========================================
# Genera carga para demostrar HPA funcionando

set -e

echo "🧪 Iniciando prueba de escalabilidad en Minikube..."
echo ""

# Verificar que estamos en Minikube
if ! kubectl get nodes | grep -q minikube 2>/dev/null; then
  echo "⚠️  No estás conectado a Minikube"
  echo "Ejecuta: eval \$(minikube docker-env)"
  exit 1
fi

# Verificar que el namespace existe
if ! kubectl get namespace news2market >/dev/null 2>&1; then
  echo "❌ Namespace 'news2market' no existe"
  echo "Despliega la aplicación primero con: kubectl apply -f k8s/local/"
  exit 1
fi

# Port forward si no está activo
echo "🔌 Configurando port-forward al API Gateway..."
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 >/dev/null 2>&1 &
PF_PID=$!
sleep 3

# Verificar que el port-forward funciona
if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
  echo "❌ No se puede conectar al API Gateway en localhost:8000"
  echo "Verifica que el servicio esté corriendo: kubectl get svc -n news2market"
  kill $PF_PID 2>/dev/null
  exit 1
fi

echo "✅ Port-forward activo"
echo ""

# ====================
# Estado inicial
# ====================
echo "📊 Estado inicial del sistema:"
echo ""
echo "HPA:"
kubectl get hpa text-processor-hpa -n news2market 2>/dev/null || echo "  (HPA no encontrado)"
echo ""
echo "Pods de text-processor:"
kubectl get pods -n news2market -l app=text-processor
echo ""
echo "Métricas:"
kubectl top pods -n news2market -l app=text-processor 2>/dev/null || echo "  (Métricas no disponibles aún)"
echo ""

read -p "Presiona ENTER para iniciar la prueba de carga..."

# ====================
# Generar carga
# ====================
echo ""
echo "🚀 Generando carga durante 3 minutos..."
echo "Esto enviará peticiones de procesamiento de texto concurrentes"
echo ""

END_TIME=$((SECONDS+180))  # 3 minutos
REQUEST_COUNT=0
START_TIME=$(date +%s)

# Función para enviar petición
send_request() {
  curl -s -X POST http://localhost:8000/api/v1/text/process \
    -H "Content-Type: application/json" \
    -d '{
      "text": "Las acciones de Bancolombia registraron un alza del 3.5% en la jornada de hoy, impulsadas por resultados financieros positivos en el tercer trimestre. Los analistas proyectan un crecimiento sostenido para el sector bancario colombiano.",
      "metadata": {"source": "load-test", "timestamp": "'$(date +%s)'"}
    }' >/dev/null 2>&1
}

# Loop para generar carga
while [ $SECONDS -lt $END_TIME ]; do
  # Enviar 5 peticiones en paralelo
  for i in {1..5}; do
    send_request &
  done
  
  REQUEST_COUNT=$((REQUEST_COUNT + 5))
  
  # Mostrar progreso cada 20 segundos
  ELAPSED=$((SECONDS - START_TIME))
  if [ $((ELAPSED % 20)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
    echo ""
    echo "⏱️  Tiempo transcurrido: ${ELAPSED}s"
    echo "📊 Peticiones enviadas: $REQUEST_COUNT"
    echo ""
    echo "   HPA Status:"
    kubectl get hpa text-processor-hpa -n news2market --no-headers 2>/dev/null | \
      awk '{print "      Target: " $5 " | Replicas: " $7 "/" $8 "/" $9}'
    echo ""
    echo "   Pods activos:"
    kubectl get pods -n news2market -l app=text-processor --no-headers | wc -l
    echo ""
  fi
  
  # Esperar entre batches
  sleep 1
done

# Esperar a que terminen los últimos requests
wait

END=$(date +%s)
DURATION=$((END - START_TIME))

echo ""
echo "✅ Prueba de carga completada"
echo ""

# ====================
# Estado final
# ====================
echo "=========================================="
echo "📊 RESULTADOS DE LA PRUEBA"
echo "=========================================="
echo ""
echo "Duración: ${DURATION}s"
echo "Total de peticiones: $REQUEST_COUNT"
echo "Throughput promedio: ~$((REQUEST_COUNT / DURATION)) req/s"
echo ""

echo "HPA final:"
kubectl get hpa text-processor-hpa -n news2market
echo ""

echo "Pods de text-processor:"
kubectl get pods -n news2market -l app=text-processor
echo ""

echo "Métricas de CPU/Memoria:"
kubectl top pods -n news2market -l app=text-processor 2>/dev/null || echo "  (Métricas no disponibles)"
echo ""

echo "Últimos eventos de escalado:"
kubectl get events -n news2market --sort-by='.lastTimestamp' | \
  grep -E 'text-processor|HorizontalPodAutoscaler' | tail -10
echo ""

# ====================
# Distribución de carga
# ====================
echo "📊 Distribución de carga entre pods:"
echo ""

for pod in $(kubectl get pods -n news2market -l app=text-processor -o name); do
  POD_NAME=$(echo $pod | cut -d/ -f2)
  PROCESSED=$(kubectl logs $pod -n news2market 2>/dev/null | grep -i "processing" | wc -l || echo "0")
  echo "  $POD_NAME: $PROCESSED peticiones procesadas"
done

echo ""

# ====================
# Instrucciones finales
# ====================
echo "=========================================="
echo "📸 EVIDENCIAS PARA EL INFORME"
echo "=========================================="
echo ""
echo "1. Captura el estado final del HPA:"
echo "   kubectl get hpa -n news2market"
echo ""
echo "2. Ver logs de un worker:"
echo "   kubectl logs -f -n news2market -l app=text-processor --tail=50"
echo ""
echo "3. Monitorear escalado en tiempo real:"
echo "   watch kubectl get hpa,pods -n news2market"
echo ""
echo "4. Ver eventos completos:"
echo "   kubectl describe hpa text-processor-hpa -n news2market"
echo ""
echo "5. Exportar métricas:"
echo "   kubectl get hpa text-processor-hpa -n news2market -o json > hpa-results.json"
echo ""

# Cleanup
kill $PF_PID 2>/dev/null

echo "=========================================="
echo "✅ Prueba finalizada"
echo "=========================================="
