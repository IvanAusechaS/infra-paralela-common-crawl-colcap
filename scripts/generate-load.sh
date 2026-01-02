#!/bin/bash

# =========================================
# Script de Generación de Carga
# Text Processor Load Generator
# =========================================

set -e

# Configuración
API_GATEWAY_URL="${API_GATEWAY_URL:-http://localhost:8000}"
NUM_REQUESTS="${NUM_REQUESTS:-50}"
BATCH_SIZE="${BATCH_SIZE:-5}"
BATCH_DELAY="${BATCH_DELAY:-1}"

echo "🔥 Generador de Carga - Text Processor"
echo "=========================================="
echo "URL: $API_GATEWAY_URL"
echo "Requests: $NUM_REQUESTS"
echo "Batch size: $BATCH_SIZE"
echo "Delay entre batches: ${BATCH_DELAY}s"
echo ""

# Textos de muestra variados
TEXTS=(
  "Análisis económico: El mercado bursátil colombiano mostró fluctuaciones importantes en el índice COLCAP durante el último trimestre. Los analistas financieros sugieren que factores macroeconómicos como la inflación, tasas de interés y políticas monetarias del Banco de la República han influenciado significativamente el comportamiento del mercado."
  
  "Reporte financiero: Empresas del sector energético y bancario lideraron las alzas en la bolsa de valores, mientras que sectores como retail y construcción mostraron desempeños mixtos. Inversionistas institucionales incrementaron posiciones en bonos del tesoro como refugio ante la volatilidad del mercado accionario."
  
  "Noticia económica: El índice COLCAP cerró la sesión con una variación positiva del 2.3%, impulsado por el buen desempeño de las acciones de Ecopetrol y Bancolombia. El volumen de negociación superó los COP 500 mil millones, reflejando un renovado interés de inversionistas locales e internacionales."
  
  "Análisis sectorial: El sector financiero mostró una recuperación notable en el último mes, con bancos reportando incrementos en su cartera de créditos y mejoras en sus indicadores de morosidad. La política monetaria expansiva del banco central ha facilitado condiciones favorables para el crédito empresarial."
  
  "Perspectiva macroeconómica: Las proyecciones de crecimiento económico para Colombia se ajustaron al alza, estimando un PIB del 3.5% anual. Factores como la recuperación del consumo interno, aumento en las exportaciones y estabilización de la tasa de cambio contribuyen a este panorama positivo."
)

# Contador
SUCCESS=0
FAILED=0
START_TIME=$(date +%s)

echo "⚡ Enviando requests..."
echo ""

for i in $(seq 1 $NUM_REQUESTS); do
  # Seleccionar texto aleatorio
  TEXT_INDEX=$((RANDOM % ${#TEXTS[@]}))
  TEXT="${TEXTS[$TEXT_INDEX]}"
  
  # Agregar número único al texto
  UNIQUE_TEXT="Request #$i - $TEXT Timestamp: $(date +%s%N)"
  
  # Enviar request en background
  (
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST \
      "${API_GATEWAY_URL}/api/v1/process/text" \
      -H "Content-Type: application/json" \
      -d "{\"text\": \"$UNIQUE_TEXT\"}" \
      --max-time 10 2>/dev/null)
    
    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "202" ]; then
      echo "✓"
    else
      echo "✗ ($RESPONSE)"
    fi
  ) &
  
  # Pequeña pausa cada BATCH_SIZE requests
  if [ $((i % BATCH_SIZE)) -eq 0 ]; then
    sleep $BATCH_DELAY
    echo "  [$i/$NUM_REQUESTS requests enviados...]"
  fi
done

# Esperar a que todos los requests terminen
echo ""
echo "⏳ Esperando completar todos los requests..."
wait

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Resumen
echo ""
echo "=========================================="
echo "✅ Generación de carga completada"
echo "=========================================="
echo "Total requests: $NUM_REQUESTS"
echo "Tiempo total: ${DURATION}s"
echo "Tasa: $((NUM_REQUESTS / DURATION)) requests/segundo"
echo ""
echo "💡 Tip: Ver métricas con:"
echo "   kubectl top pods -n news2market | grep text-processor"
echo ""
