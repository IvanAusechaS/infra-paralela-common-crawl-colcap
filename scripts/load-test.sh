#!/bin/bash

# ====================
# Script de Prueba de Carga para demostrar escalabilidad
# ====================
# Genera tráfico hacia text-processor para activar HPA
# Uso: ./scripts/load-test.sh

set -e

echo "🔥 Iniciando prueba de carga para News2Market..."

# Configuración
NAMESPACE="news2market"
API_GATEWAY_URL=${API_GATEWAY_URL:-$(kubectl get svc api-gateway-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')}

if [ -z "$API_GATEWAY_URL" ]; then
  echo "❌ No se pudo obtener la URL del API Gateway"
  echo "Asegúrate de que el servicio esté desplegado o exporta API_GATEWAY_URL"
  exit 1
fi

echo "✅ API Gateway URL: http://$API_GATEWAY_URL"
echo ""

# ====================
# 1. Estado inicial
# ====================
echo "📊 Estado inicial del sistema:"
echo ""
kubectl get hpa -n $NAMESPACE
echo ""
kubectl get pods -n $NAMESPACE -l app=text-processor
echo ""

# ====================
# 2. Generar carga
# ====================
echo "🚀 Generando carga durante 5 minutos..."
echo "Esto enviará peticiones de procesamiento de texto de forma concurrente"
echo ""

END_TIME=$((SECONDS+300))  # 5 minutos
REQUEST_COUNT=0

# Función para enviar petición
send_request() {
  curl -s -X POST "http://$API_GATEWAY_URL/api/v1/text/process" \
    -H "Content-Type: application/json" \
    -d "{
      \"text\": \"Las acciones de Bancolombia registraron un alza del 3.5% en la jornada de hoy, impulsadas por resultados financieros positivos en el tercer trimestre. Los analistas proyectan un crecimiento sostenido para el sector bancario colombiano, con el COLCAP alcanzando nuevos máximos históricos. La inflación se mantiene controlada según el Banco de la República, lo que podría favorecer nuevas inversiones en el mercado de valores.\",
      \"metadata\": {\"source\": \"load-test\"}
    }" >/dev/null 2>&1
}

# Loop para generar carga
while [ $SECONDS -lt $END_TIME ]; do
  # Enviar 10 peticiones en paralelo
  for i in {1..10}; do
    send_request &
  done
  
  REQUEST_COUNT=$((REQUEST_COUNT + 10))
  
  # Mostrar progreso cada 30 segundos
  if [ $((REQUEST_COUNT % 100)) -eq 0 ]; then
    echo "📈 Peticiones enviadas: $REQUEST_COUNT"
    echo "   Pods actuales:"
    kubectl get pods -n $NAMESPACE -l app=text-processor --no-headers | wc -l
    echo "   HPA status:"
    kubectl get hpa text-processor-hpa -n $NAMESPACE --no-headers
    echo ""
  fi
  
  # Esperar un poco entre batches
  sleep 2
done

# Esperar a que terminen los últimos requests
wait

echo ""
echo "✅ Prueba de carga completada"
echo "📊 Total de peticiones enviadas: $REQUEST_COUNT"
echo ""

# ====================
# 3. Estado final
# ====================
echo "📊 Estado final del sistema:"
echo ""
echo "HPA:"
kubectl get hpa -n $NAMESPACE
echo ""
echo "Pods de text-processor:"
kubectl get pods -n $NAMESPACE -l app=text-processor
echo ""
echo "Eventos de escalado:"
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | grep text-processor | tail -10

# ====================
# 4. Métricas
# ====================
echo ""
echo "📈 Métricas de rendimiento:"
echo ""

POD_COUNT=$(kubectl get pods -n $NAMESPACE -l app=text-processor --no-headers | wc -l)
echo "  Pods escalados: $POD_COUNT"
echo "  Throughput: ~$((REQUEST_COUNT / 300)) req/s"
echo "  Total requests: $REQUEST_COUNT"

# ====================
# 5. Instrucciones para monitoring
# ====================
echo ""
echo "=========================================="
echo "📊 EVIDENCIAS PARA EL INFORME ACADÉMICO"
echo "=========================================="
echo ""
echo "1. Capturar scaling events:"
echo "   kubectl get hpa text-processor-hpa -n news2market --watch"
echo ""
echo "2. Ver logs de un worker:"
echo "   kubectl logs -f -n news2market -l app=text-processor --tail=50"
echo ""
echo "3. Monitorear métricas de CPU/Memoria:"
echo "   kubectl top pods -n news2market -l app=text-processor"
echo ""
echo "4. Verificar distribución de carga:"
echo "   for pod in \$(kubectl get pods -n news2market -l app=text-processor -o name); do"
echo "     echo \$pod; kubectl logs \$pod -n news2market | grep 'Processing' | wc -l"
echo "   done"
echo ""
echo "5. Exportar métricas para gráficos:"
echo "   kubectl get hpa text-processor-hpa -n news2market -o json > hpa-metrics.json"
echo ""
echo "=========================================="
