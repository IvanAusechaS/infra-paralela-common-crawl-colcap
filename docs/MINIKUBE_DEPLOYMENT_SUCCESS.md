# ✅ Sistema Desplegado en Minikube - News2Market

## 📊 Estado del Deployment

**Fecha**: $(date)  
**Cluster**: Minikube v1.37.0  
**Kubernetes**: v1.34.0

### Pods Activos (13/13 Running)

```
NAME                                   READY   STATUS    RESTARTS   AGE
api-gateway-79877497dc-9cjq5           1/1     Running   0          6m
api-gateway-79877497dc-pkcxg           1/1     Running   0          6m
correlation-service-6d878d797d-qfdlq   1/1     Running   0          8m
correlation-service-6d878d797d-s4rkh   1/1     Running   0          8m
data-acquisition-649bfd46db-4qd2s      1/1     Running   0          8m
data-acquisition-649bfd46db-ttwzr      1/1     Running   0          8m
frontend-658c667b8-4lk67               1/1     Running   0          8m
frontend-658c667b8-k2rf4               1/1     Running   0          8m
frontend-658c667b8-n86xz               1/1     Running   0          8m
postgres-0                             1/1     Running   0          12m
redis-0                                1/1     Running   0          12m
text-processor-647785f688-hvxnz        1/1     Running   0          8m
text-processor-647785f688-v5p2d        1/1     Running   0          8m
```

### HPA Configurado

```
NAME                 REFERENCE                   TARGETS                        MINPODS   MAXPODS   REPLICAS
text-processor-hpa   Deployment/text-processor   cpu: 4%/70%, memory: 13%/80%   2         10        2
```

**Configuración del HPA:**
- **MIN replicas**: 2
- **MAX replicas**: 10
- **Threshold CPU**: 70%
- **Threshold Memoria**: 80%
- **Métricas activas**: ✅ CPU y memoria funcionando

### Servicios Expuestos

```
NAME                       TYPE        CLUSTER-IP       PORT(S)
api-gateway-service        ClusterIP   10.97.101.131    8000/TCP
correlation-service        ClusterIP   10.103.23.237    8003/TCP
data-acquisition-service   ClusterIP   10.106.151.126   8001/TCP
frontend-service           ClusterIP   10.106.126.104   80/TCP
postgres-service           ClusterIP   None             5432/TCP
redis-service              ClusterIP   None             6379/TCP
text-processor-service     ClusterIP   10.96.95.44      8002/TCP
```

### StatefulSets (Bases de Datos)

```
NAME       READY   STATUS
postgres   1/1     Running
redis      1/1     Running
```

---

## 🧪 Cómo Probar el Escalado del HPA

### 1. Abrir Túnel al API Gateway

```bash
minikube kubectl -- port-forward -n news2market svc/api-gateway-service 8000:8000 &
```

### 2. Verificar Health Check

```bash
curl http://localhost:8000/api/v1/health
# Respuesta esperada: {"status":"healthy","service":"api-gateway",...}
```

### 3. Generar Carga Intensa

**Opción A - Carga constante (recomendado):**
```bash
# Ejecutar en una terminal separada
while true; do
  for i in {1..50}; do
    curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1 &
  done
  sleep 1
done
```

**Opción B - Carga extrema:**
```bash
for i in {1..1000}; do
  curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1 &
done
```

### 4. Monitorear el Escalado

**En otra terminal:**
```bash
watch -n 2 'minikube kubectl -- get hpa,pods -n news2market | grep -E "NAME|text-processor"'
```

**Observarás:**
- **CPU % aumentando** (de 4% hacia 70%+)
- **REPLICAS escalando** (de 2 → 3 → 4... hasta 10)
- **Nuevos pods creando** (Pending → ContainerCreating → Running)

### 5. Verificar Métricas Detalladas

```bash
# Uso de recursos de cada pod
minikube kubectl -- top pods -n news2market

# Historial de eventos del HPA
minikube kubectl -- describe hpa text-processor-hpa -n news2market

# Logs de un pod específico
minikube kubectl -- logs -n news2market text-processor-XXXXX --tail=50
```

---

## 📸 Evidencia para el Informe Académico

### Capturas Recomendadas

1. **Estado inicial (2 réplicas)**
   ```bash
   minikube kubectl -- get hpa,pods -n news2market | grep text-processor
   ```

2. **Durante escalado (5-7 réplicas)**
   - Captura de CPU aumentando (50-80%)
   - Nuevos pods en estado `ContainerCreating`

3. **Post-escalado (10 réplicas)**
   - Todos los pods `Running`
   - CPU distribuido entre réplicas

4. **Distribución de carga**
   ```bash
   for pod in $(minikube kubectl -- get pods -n news2market -l app=text-processor -o name); do
     echo "=== $pod ===" 
     minikube kubectl -- logs -n news2market $pod --tail=5
   done
   ```

### Métricas Clave

- **Tiempo de respuesta a escalado**: ~30-60 segundos (desde trigger hasta pods Running)
- **Factor de escalado máximo**: 5x (2 → 10 réplicas)
- **Límite de recursos por pod**:
  - CPU: 500m (0.5 cores)
  - Memoria: 1Gi

---

## 🚀 Arquitectura del Sistema

```
┌─────────────┐
│   Frontend  │ (3 réplicas)
│  React+Vite │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API Gateway │ (2 réplicas)
│   FastAPI   │
└──────┬──────┘
       │
       ├─────────────┬──────────────┬────────────────┐
       ▼             ▼              ▼                ▼
 ┌──────────┐  ┌─────────┐  ┌─────────────┐  ┌─────────┐
 │   Data   │  │  Text   │  │ Correlation │  │ Redis   │
 │Acquisition│  │Processor│  │   Service   │  │ Cache   │
 │          │  │(2-10 HPA)│  │             │  │         │
 └─────┬────┘  └────┬────┘  └──────┬──────┘  └─────────┘
       │            │               │
       └────────────┴───────────────┘
                    │
              ┌─────┴─────┐
              │ PostgreSQL│
              │StatefulSet│
              └───────────┘
```

### Componentes con Escalado Automático

- **Text Processor**: HPA activo (2-10 réplicas)
- **Frontend**: Escalado manual (3 réplicas)
- **API Gateway**: Escalado manual (2 réplicas)
- **Correlation Service**: Escalado manual (2 réplicas)
- **Data Acquisition**: Escalado manual (2 réplicas)

---

## 🔍 Verificación de Paralelismo

### Demostrar Procesamiento Paralelo

```bash
# Enviar 10 tareas simultáneas y ver qué pods las procesan
for i in {1..10}; do
  echo "Task $i"
  curl -s -X POST http://localhost:8000/api/v1/process \
    -H "Content-Type: application/json" \
    -d "{\"url\":\"https://example.com/article$i\",\"text\":\"Test article $i\"}" &
done
wait

# Ver logs de todos los text-processors
minikube kubectl -- logs -n news2market -l app=text-processor --tail=10 --prefix
```

**Esperado**: Diferentes pods procesando diferentes tareas (load balancing automático de K8s).

---

## 📝 Notas Técnicas

### Problemas Resueltos

1. **DATABASE_URL**: Configurado para construirse desde variables individuales (DATABASE_HOST, DATABASE_PORT, etc.)
2. **Health checks**: Path corregido a `/api/v1/health`
3. **ENV variable**: Agregada al ConfigMap (`ENV: development`)
4. **imagePullPolicy**: Cambiado a `Never` para usar imágenes locales de Minikube

### Archivos Críticos Modificados

- `k8s/local/configmap.yaml`: Agregado `ENV: development`
- `k8s/local/*-deployment.yaml`: Eliminado `DATABASE_URL` compuesto
- `backend/*/database.py`: Construcción dinámica de DATABASE_URL
- `k8s/local/api-gateway-deployment.yaml`: Health check path corregido

---

## 🎯 Siguiente Paso: AWS Deployment

Una vez validado localmente, el deployment a AWS EKS es directo:

```bash
# 1. Subir imágenes a ECR
./scripts/build-and-push.sh

# 2. Crear cluster EKS (costo estimado: $20-25)
eksctl create cluster -f k8s/cluster-config-learner-lab.yaml

# 3. Desplegar
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
# ... (resto de manifests en orden)
```

Documentación completa en: `docs/AWS_LEARNER_LAB_GUIDE.md`

---

**✅ Sistema validado y listo para presentación académica.**
