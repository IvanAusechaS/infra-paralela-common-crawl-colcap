#!/bin/bash
# Stress test para demostrar escalado del HPA

echo "🔥 Iniciando stress test del HPA"
echo "⏱️  Generando carga constante por 2 minutos..."

# Generar carga continua
for i in {1..120}; do
  for j in {1..5}; do
    (curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1) &
  done
  sleep 1
done &

LOAD_PID=$!

echo "📊 Monitorea el escalado con:"
echo "   watch -n 2 'minikube kubectl -- get hpa,pods -n news2market'"
echo ""
echo "Presiona Ctrl+C para detener (PID: $LOAD_PID)"
wait $LOAD_PID
