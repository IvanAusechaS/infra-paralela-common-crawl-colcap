# 🎯 GUÍA RÁPIDA: TESTING LOCAL CON MINIKUBE

## ✅ Lo que ya hicimos:

1. ✅ Instalamos Minikube
2. ✅ Iniciamos cluster (`minikube start`)
3. ✅ Habilitamos metrics-server
4. ✅ Preparamos manifests locales (`k8s/local/`)
5. ✅ Configuramos Docker para Minikube
6. ✅ Construimos api-gateway y data-acquisition

## 🔄 Lo que falta:

### Construir las imágenes restantes:

```bash
# En el directorio raíz del proyecto
eval $(minikube docker-env)

# Text Processor (~3 min)
docker build -t news2market/text-processor:latest ./backend/text-processor

# Correlation Service (~4 min)
docker build -t news2market/correlation-service:latest ./backend/correlation-service

# Frontend (~2 min)
docker build -t news2market/frontend:latest ./frontend
```

### Verificar imágenes:
```bash
docker images | grep news2market
```

### Desplegar en Minikube:

```bash
# 1. Namespace
kubectl apply -f k8s/local/namespace.yaml

# 2. Configuración
kubectl apply -f k8s/local/configmap.yaml
kubectl apply -f k8s/local/secrets.yaml

# 3. Bases de datos
kubectl apply -f k8s/local/postgres-statefulset.yaml
kubectl apply -f k8s/local/redis-statefulset.yaml

# Esperar a que estén listas (2-3 min)
kubectl wait --for=condition=ready pod -l app=postgres -n news2market --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n news2market --timeout=300s

# 4. Metrics Server
kubectl apply -f k8s/local/metrics-server.yaml

# 5. Microservicios
kubectl apply -f k8s/local/api-gateway-deployment.yaml
kubectl apply -f k8s/local/data-acquisition-deployment.yaml
kubectl apply -f k8s/local/text-processor-deployment.yaml
kubectl apply -f k8s/local/correlation-service-deployment.yaml
kubectl apply -f k8s/local/frontend-deployment.yaml

# 6. HPA
kubectl apply -f k8s/local/text-processor-hpa.yaml
```

### Verificar despliegue:

```bash
# Ver todos los pods
kubectl get pods -n news2market

# Ver servicios
kubectl get svc -n news2market

# Ver HPA
kubectl get hpa -n news2market

# Ver métricas (esperar 1 min después del despliegue)
kubectl top pods -n news2market
```

### Acceder a los servicios:

```bash
# Opción 1: Port-forward al API Gateway
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 &

# Probar
curl http://localhost:8000/health

# Opción 2: Minikube service (abre en navegador)
minikube service frontend-service -n news2market
```

### Probar escalado automático:

```bash
# Ejecutar script de prueba
./scripts/test-scalability-minikube.sh

# O manualmente:
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 &

# Generar carga
for i in {1..100}; do
  curl -s -X POST http://localhost:8000/api/v1/text/process \
    -H "Content-Type: application/json" \
    -d '{"text":"Test de escalado"}' &
done

# Ver escalado en tiempo real
watch kubectl get hpa,pods -n news2market
```

## 📊 Evidencias a capturar:

1. **Pods running**:
   ```bash
   kubectl get pods -n news2market -o wide
   ```

2. **HPA escalando**:
   ```bash
   kubectl get hpa -n news2market --watch
   ```

3. **Métricas de recursos**:
   ```bash
   kubectl top pods -n news2market
   ```

4. **Logs de workers**:
   ```bash
   kubectl logs -f -n news2market -l app=text-processor --all-containers
   ```

5. **Distribución de carga**:
   ```bash
   for pod in $(kubectl get pods -n news2market -l app=text-processor -o name); do
     echo "=== $pod ==="
     kubectl logs $pod -n news2market | grep -c "Processing" || echo "0"
   done
   ```

## 🛑 Detener y limpiar:

```bash
# Eliminar todo
kubectl delete namespace news2market

# O detener Minikube completamente
minikube stop

# Eliminar cluster
minikube delete
```

## ⚠️ Troubleshooting:

### Pods en CrashLoopBackOff:
```bash
kubectl logs -n news2market <pod-name>
kubectl describe pod -n news2market <pod-name>
```

### HPA no muestra métricas:
```bash
# Esperar 1-2 minutos después del despliegue
# Verificar metrics-server
kubectl get deployment metrics-server -n kube-system
kubectl logs -n kube-system deployment/metrics-server
```

### Imágenes no se encuentran:
```bash
# Asegurarse de estar usando el daemon de Minikube
eval $(minikube docker-env)

# Verificar imágenes
docker images | grep news2market

# Reconstruir si es necesario
docker build -t news2market/text-processor:latest ./backend/text-processor
```

---

**Estado actual**: ✅ 2/5 imágenes construidas (api-gateway, data-acquisition)  
**Siguiente**: Construir text-processor, correlation-service, frontend  
**Tiempo estimado restante**: ~10 minutos

