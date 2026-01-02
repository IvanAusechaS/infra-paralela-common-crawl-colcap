# ========================================
# GUÍA: VALIDACIÓN LOCAL SIN AWS
# ========================================
# Cómo probar TODA la arquitectura sin gastar ni un centavo

## 🎯 Objetivo
Validar que tu aplicación funciona completamente en Kubernetes ANTES de desplegar en AWS EKS.

---

## 🛠️ OPCIÓN 1: Minikube (Recomendado - Más similar a EKS)

### Paso 1: Instalar Minikube

**Linux (Fedora/Ubuntu)**:
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Verificar
minikube version
```

**macOS**:
```bash
brew install minikube
```

**Windows**:
```powershell
choco install minikube
```

---

### Paso 2: Iniciar Minikube

```bash
# Iniciar con recursos suficientes
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Verificar
kubectl get nodes
minikube status

# Habilitar metrics-server (necesario para HPA)
minikube addons enable metrics-server

# Verificar que metrics-server funciona (puede tardar 1 min)
kubectl top nodes
```

---

### Paso 3: Construir imágenes dentro de Minikube

**Importante**: Las imágenes deben estar disponibles DENTRO del cluster de Minikube.

```bash
# Configurar Docker para usar el daemon de Minikube
eval $(minikube docker-env)

# Ahora todos los builds se harán dentro de Minikube
cd /home/ivanausecha/Documentos/infra-paralela-common-crawl-colcap

# Build de cada servicio
docker build -t news2market/api-gateway:latest ./backend/api-gateway
docker build -t news2market/data-acquisition:latest ./backend/data-acquisition
docker build -t news2market/text-processor:latest ./backend/text-processor
docker build -t news2market/correlation-service:latest ./backend/correlation-service
docker build -t news2market/frontend:latest ./frontend

# Verificar que las imágenes están disponibles
docker images | grep news2market
```

**⚠️ Nota**: Si cierras la terminal, ejecuta de nuevo `eval $(minikube docker-env)` para reconectar.

---

### Paso 4: Preparar manifests para Minikube

Los manifests actuales tienen `${ECR_REGISTRY}` que no funcionará en Minikube. Necesitas versiones locales:

```bash
# Crear directorio para manifests locales
mkdir -p k8s/local

# Copiar todos los manifests
cp k8s/*.yaml k8s/local/

# Reemplazar ${ECR_REGISTRY} con el nombre local
cd k8s/local
sed -i 's|${ECR_REGISTRY}/news2market/|news2market/|g' *.yaml

# También cambiar imagePullPolicy a Never (para que no intente descargar)
sed -i 's|imagePullPolicy: Always|imagePullPolicy: Never|g' *.yaml

# Verificar cambios
grep "image:" *.yaml
```

**O usar este script automatizado**:

```bash
#!/bin/bash
# scripts/prepare-local-manifests.sh

set -e

echo "🔧 Preparando manifests para Minikube..."

# Crear directorio
mkdir -p k8s/local
cp k8s/*.yaml k8s/local/

# Reemplazar ECR_REGISTRY
cd k8s/local
for file in *.yaml; do
  sed -i.bak 's|${ECR_REGISTRY}/news2market/|news2market/|g' "$file"
  sed -i.bak 's|imagePullPolicy: Always|imagePullPolicy: Never|g' "$file"
  rm -f "$file.bak"
done

echo "✅ Manifests listos en k8s/local/"
```

---

### Paso 5: Desplegar en Minikube

```bash
cd /home/ivanausecha/Documentos/infra-paralela-common-crawl-colcap

# 1. Namespace
kubectl apply -f k8s/local/namespace.yaml

# 2. Configuración
kubectl apply -f k8s/local/configmap.yaml
kubectl apply -f k8s/local/secrets.yaml

# 3. Bases de datos (esto puede tardar 1-2 min)
kubectl apply -f k8s/local/postgres-statefulset.yaml
kubectl apply -f k8s/local/redis-statefulset.yaml

# Esperar a que estén listas
echo "⏳ Esperando a PostgreSQL..."
kubectl wait --for=condition=ready pod -l app=postgres -n news2market --timeout=300s

echo "⏳ Esperando a Redis..."
kubectl wait --for=condition=ready pod -l app=redis -n news2market --timeout=300s

# 4. Metrics server (para HPA)
kubectl apply -f k8s/local/metrics-server.yaml

# 5. Microservicios
kubectl apply -f k8s/local/api-gateway-deployment.yaml
kubectl apply -f k8s/local/data-acquisition-deployment.yaml
kubectl apply -f k8s/local/text-processor-deployment.yaml
kubectl apply -f k8s/local/correlation-service-deployment.yaml
kubectl apply -f k8s/local/frontend-deployment.yaml

# 6. HPA
kubectl apply -f k8s/local/text-processor-hpa.yaml

# Ver el despliegue en tiempo real
watch kubectl get pods -n news2market
```

---

### Paso 6: Verificar que todo funciona

```bash
# Ver todos los recursos
kubectl get all -n news2market

# Ver pods específicos
kubectl get pods -n news2market

# Ver logs de un servicio
kubectl logs -f -n news2market -l app=api-gateway

# Ver eventos (útil para debuggear)
kubectl get events -n news2market --sort-by='.lastTimestamp'

# Verificar que metrics-server funciona (necesario para HPA)
kubectl top pods -n news2market

# Ver HPA
kubectl get hpa -n news2market
```

**Salida esperada**:
```
NAME                    REFERENCE                    TARGETS         MINPODS   MAXPODS   REPLICAS
text-processor-hpa      Deployment/text-processor    15%/70%, 20%/80%   2         10        2
```

---

### Paso 7: Acceder a los servicios

Minikube no tiene LoadBalancer real, así que usamos port-forwarding:

```bash
# API Gateway (puerto 8000)
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 &

# Frontend (puerto 8080)
kubectl port-forward -n news2market svc/frontend-service 8080:80 &

# Ahora puedes acceder:
# http://localhost:8000 - API Gateway
# http://localhost:8080 - Frontend

# Probar health check
curl http://localhost:8000/health
```

**O usar Minikube tunnel** (crea un LoadBalancer real localmente):
```bash
# En una terminal separada
minikube tunnel

# Esto requiere sudo y debe estar corriendo siempre
# Ahora puedes obtener IPs externas:
kubectl get svc -n news2market
```

---

### Paso 8: Probar el HPA (Escalado automático)

```bash
# Ver estado inicial
kubectl get hpa text-processor-hpa -n news2market

# Generar carga
for i in {1..200}; do
  curl -s -X POST http://localhost:8000/api/v1/text/process \
    -H "Content-Type: application/json" \
    -d '{
      "text": "Prueba de carga para demostrar escalado horizontal automático en Kubernetes. Las acciones de Bancolombia subieron un 5% impulsadas por buenos resultados financieros.",
      "metadata": {"test": true}
    }' &
done

# Monitorear escalado en tiempo real
watch kubectl get hpa,pods -n news2market

# Deberías ver:
# - CPU usage subiendo en el HPA
# - REPLICAS aumentando de 2 a 3, 4, 5... hasta 10
# - Nuevos pods de text-processor en estado Running
```

---

## 🛠️ OPCIÓN 2: Kind (Kubernetes in Docker)

Kind es más ligero pero menos similar a EKS.

### Instalación

```bash
# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verificar
kind version
```

### Crear cluster

```bash
# Crear configuración de Kind
cat > k8s/kind-config.yaml <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

# Crear cluster
kind create cluster --name news2market --config k8s/kind-config.yaml

# Verificar
kubectl cluster-info --context kind-news2market
kubectl get nodes
```

### Cargar imágenes en Kind

```bash
# Build en tu máquina local
docker build -t news2market/api-gateway:latest ./backend/api-gateway
docker build -t news2market/data-acquisition:latest ./backend/data-acquisition
docker build -t news2market/text-processor:latest ./backend/text-processor
docker build -t news2market/correlation-service:latest ./backend/correlation-service
docker build -t news2market/frontend:latest ./frontend

# Cargar en Kind
kind load docker-image news2market/api-gateway:latest --name news2market
kind load docker-image news2market/data-acquisition:latest --name news2market
kind load docker-image news2market/text-processor:latest --name news2market
kind load docker-image news2market/correlation-service:latest --name news2market
kind load docker-image news2market/frontend:latest --name news2market
```

**Luego seguir los mismos pasos de despliegue que Minikube**.

---

## 🧪 PRUEBAS DE INTEGRACIÓN

### Test 1: Health Checks

```bash
# Todos los servicios deben responder
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 &

curl http://localhost:8000/health
# Debe devolver: {"status": "healthy", "services": {...}}

# Verificar base de datos
kubectl exec -it -n news2market postgres-0 -- psql -U news2market -d news2market -c "SELECT version();"
```

---

### Test 2: Flujo completo de datos

```bash
# 1. Buscar noticias (Data Acquisition)
curl -X POST http://localhost:8000/api/v1/data/search \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["economia", "mercado"], "max_results": 10}'

# 2. Procesar texto (Text Processor)
curl -X POST http://localhost:8000/api/v1/text/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Las acciones del sector bancario subieron hoy..."}'

# 3. Calcular correlación (Correlation Service)
curl -X POST http://localhost:8000/api/v1/correlation/correlate \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "metrics": ["volume", "sentiment"],
    "lag_days": 0
  }'

# 4. Ver resultados
curl http://localhost:8000/api/v1/correlation/results
```

---

### Test 3: Escalabilidad y paralelismo

**Script automatizado** `scripts/test-scalability-local.sh`:

```bash
#!/bin/bash

set -e

echo "🧪 Prueba de escalabilidad en Minikube"

# Port forward si no está activo
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 >/dev/null 2>&1 &
PF_PID=$!
sleep 2

# Estado inicial
echo "📊 Estado inicial:"
kubectl get hpa text-processor-hpa -n news2market
kubectl get pods -n news2market -l app=text-processor

# Generar carga ligera por 3 minutos
echo ""
echo "🚀 Generando carga durante 3 minutos..."
END_TIME=$((SECONDS+180))
COUNT=0

while [ $SECONDS -lt $END_TIME ]; do
  for i in {1..5}; do
    curl -s -X POST http://localhost:8000/api/v1/text/process \
      -H "Content-Type: application/json" \
      -d '{"text":"Test de carga para HPA en Minikube"}' >/dev/null &
  done
  COUNT=$((COUNT + 5))
  
  # Mostrar progreso cada 30s
  if [ $((SECONDS % 30)) -eq 0 ]; then
    echo "   Requests enviados: $COUNT"
    kubectl get hpa text-processor-hpa -n news2market --no-headers
  fi
  
  sleep 2
done

wait

# Estado final
echo ""
echo "📊 Estado final:"
kubectl get hpa text-processor-hpa -n news2market
kubectl get pods -n news2market -l app=text-processor

# Cleanup
kill $PF_PID 2>/dev/null

echo ""
echo "✅ Prueba completada. Total requests: $COUNT"
```

---

## 📊 EVIDENCIAS PARA EL INFORME ACADÉMICO

### Capturas necesarias:

1. **Arquitectura desplegada**:
```bash
kubectl get all -n news2market -o wide
```

2. **Pods running**:
```bash
kubectl get pods -n news2market
```

3. **HPA antes de la carga**:
```bash
kubectl get hpa -n news2market
kubectl top pods -n news2market
```

4. **HPA durante la carga** (mientras corres el script):
```bash
watch -n 2 'kubectl get hpa,pods -n news2market'
```

5. **Logs de workers procesando en paralelo**:
```bash
# Ver logs de todos los text-processor simultáneamente
kubectl logs -f -n news2market -l app=text-processor --all-containers --max-log-requests=10
```

6. **Distribución de carga entre pods**:
```bash
for pod in $(kubectl get pods -n news2market -l app=text-processor -o name); do
  echo "=== $pod ==="
  kubectl logs $pod -n news2market | grep -i "processing" | wc -l
done
```

---

## 🧹 LIMPIEZA

```bash
# Eliminar el namespace (borra todo)
kubectl delete namespace news2market

# O reiniciar Minikube completamente
minikube stop
minikube delete

# Destruir cluster de Kind
kind delete cluster --name news2market
```

---

## ✅ CHECKLIST DE VALIDACIÓN LOCAL

Antes de ir a AWS, asegúrate de que TODO esto funciona en Minikube:

- [ ] Todos los pods están Running (no CrashLoopBackOff)
- [ ] Health checks responden correctamente
- [ ] PostgreSQL y Redis están funcionando
- [ ] Puedes hacer peticiones HTTP a todos los servicios
- [ ] Frontend carga correctamente
- [ ] HPA está activo y muestra métricas
- [ ] Al generar carga, los pods escalan (de 2 a 4+)
- [ ] Después de 5 min sin carga, los pods bajan
- [ ] Logs muestran procesamiento paralelo en múltiples workers

**Si todo esto funciona en Minikube, funcionará en EKS** ✅

---

**Última actualización**: Diciembre 2025
