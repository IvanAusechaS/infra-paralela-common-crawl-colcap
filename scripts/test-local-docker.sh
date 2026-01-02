#!/bin/bash

# ====================
# Script de prueba local con Docker Compose
# ====================
# Inicia todos los servicios para testing rápido

set -e

echo "🚀 Iniciando sistema con Docker Compose..."
echo ""

# Volver al directorio backend si no estamos ahí
cd "$(dirname "$0")/../backend" 2>/dev/null || cd backend 2>/dev/null || true

# 1. Iniciar bases de datos
echo "📦 [1/3] Iniciando bases de datos..."
docker compose up -d postgres redis

echo "⏳ Esperando a que PostgreSQL esté listo..."
sleep 10

# Verificar que postgres esté healthy
until docker compose exec -T postgres pg_isready -U news2market; do
  echo "   Esperando PostgreSQL..."
  sleep 2
done

echo "✅ PostgreSQL listo"
echo ""

# 2. Iniciar servicios backend (sin montar volúmenes en modo desarrollo)
echo "📦 [2/3] Construyendo e iniciando microservicios..."
docker compose up -d --build \
  --no-deps \
  data-acquisition \
  text-processor \
  correlation-service \
  api-gateway

echo "⏳ Esperando a que los servicios estén listos (15s)..."
sleep 15

# 3. Verificar estado
echo ""
echo "📊 [3/3] Estado de los servicios:"
docker compose ps

echo ""
echo "=========================================="
echo "✅ SISTEMA INICIADO"
echo "=========================================="
echo ""
echo "🌐 URLs de acceso:"
echo "   API Gateway:    http://localhost:8000"
echo "   Docs (Swagger): http://localhost:8000/docs"
echo "   PostgreSQL:     localhost:5432"
echo "   Redis:          localhost:6379"
echo ""
echo "🔍 Ver logs:"
echo "   docker compose logs -f api-gateway"
echo "   docker compose logs -f text-processor"
echo ""
echo "🧪 Probar health check:"
echo "   curl http://localhost:8000/health"
echo ""
echo "🛑 Detener sistema:"
echo "   docker compose down"
echo ""
echo "=========================================="
