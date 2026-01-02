# ========================================
# RESPUESTA COMPLETA: PREPARACIÓN PARA AWS
# ========================================
# Infraestructuras Paralelas y Distribuidas - News2Market

## 📋 ÍNDICE DE RESPUESTAS

1. [Componentes faltantes](#1-componentes-faltantes)
2. [Servicios AWS y orden de creación](#2-servicios-aws-y-orden)
3. [Archivos Kubernetes necesarios](#3-archivos-kubernetes)
4. [Estrategia de validación sin costo](#4-validación-sin-costo)
5. [Checklist pre-despliegue](#5-checklist-pre-despliegue)
6. [Recursos AWS: crear vs evitar](#6-recursos-aws)
7. [Demostrar paralelismo sin ALB](#7-demostrar-paralelismo)

---

## 1. COMPONENTES FALTANTES

### ✅ Lo que YA TIENES (bien hecho):
- ✅ Backend (4 microservicios) con Dockerfiles
- ✅ Frontend React con Dockerfile
- ✅ docker-compose.yml funcional
- ✅ Manifests K8s: namespace, configmap, secrets
- ✅ text-processor: Deployment + Service + HPA
- ✅ correlation-service: Deployment + Service
- ✅ frontend: Deployment + Service
- ✅ postgres y redis: StatefulSets
- ✅ metrics-server para HPA
- ✅ cluster-config.yaml para EKS

### ❌ Lo que FALTABA (ahora creado):

#### Manifests de Kubernetes:
1. **`k8s/api-gateway-deployment.yaml`** ✅ CREADO
   - Deployment del API Gateway
   - Service tipo LoadBalancer (cambiar a NodePort en Learner Lab)

2. **`k8s/data-acquisition-deployment.yaml`** ✅ CREADO
   - Deployment del servicio de adquisición de datos
   - Service tipo ClusterIP

3. **`k8s/ingress.yaml`** ✅ CREADO (opcional)
   - ALB Ingress Controller config
   - Alternativa simple con NodePort para Learner Lab

4. **`k8s/cluster-config-learner-lab.yaml`** ✅ CREADO
   - Configuración optimizada para $50 USD budget
   - t3.medium (no t3.large) para ahorrar
   - 2 nodos (no 3) para minimizar costos

#### Scripts de automatización:
5. **`scripts/prepare-local-manifests.sh`** ✅ CREADO
   - Convierte manifests de EKS a Minikube/Kind
   - Reemplaza ${ECR_REGISTRY} con nombres locales

6. **`scripts/build-and-push.sh`** ✅ CREADO
   - Build de todas las imágenes Docker
   - Push a ECR automático

7. **`scripts/validate-system.sh`** ✅ CREADO
   - Valida TODOS los prerequisitos
   - Revisa sintaxis de manifests

8. **`scripts/test-scalability-minikube.sh`** ✅ CREADO
   - Genera carga para probar HPA
   - Captura métricas de escalado

#### Documentación:
9. **`docs/PRE_DEPLOYMENT_CHECKLIST.md`** ✅ CREADO
   - Checklist completo antes de AWS
   - Fases detalladas con comandos

10. **`docs/LOCAL_VALIDATION_GUIDE.md`** ✅ CREADO
    - Guía paso a paso con Minikube/Kind
    - Pruebas de integración

11. **`docs/AWS_LEARNER_LAB_GUIDE.md`** ✅ CREADO
    - Específico para Learner Lab
    - Optimización de costos detallada

---

## 2. SERVICIOS AWS Y ORDEN

### 📅 ORDEN CRONOLÓGICO (sin gastar hasta el paso 5)

#### Fase 1: Preparación (0 USD)
```bash
# 1. Instalar herramientas
sudo apt install awscli kubectl  # Linux
brew install awscli kubectl eksctl  # macOS

# 2. Validar localmente
./scripts/validate-system.sh

# 3. Probar en Minikube
./scripts/prepare-local-manifests.sh
minikube start --cpus=4 --memory=8192
eval $(minikube docker-env)
# Build imágenes...
kubectl apply -f k8s/local/

# 4. Verificar HPA funciona
./scripts/test-scalability-minikube.sh
```

#### Fase 2: Credenciales AWS (0 USD)
```bash
# 5. Iniciar Learner Lab
#    - Ir a AWS Academy
#    - Iniciar sesión
#    - "Start Lab" → Esperar 🟢
#    - "AWS Details" → Copiar credenciales

# 6. Configurar AWS CLI
nano ~/.aws/credentials
# Pegar:
# [default]
# aws_access_key_id = ASIAV...
# aws_secret_access_key = ...
# aws_session_token = ...

# 7. Verificar
aws sts get-caller-identity
```

#### Fase 3: Registro de imágenes (~$0.20)
```bash
# 8. Crear repositorios ECR
aws ecr create-repository --repository-name news2market/api-gateway
aws ecr create-repository --repository-name news2market/data-acquisition
aws ecr create-repository --repository-name news2market/text-processor
aws ecr create-repository --repository-name news2market/correlation-service
aws ecr create-repository --repository-name news2market/frontend

# 9. Build y push de imágenes (tarda ~10 min)
./scripts/build-and-push.sh
```

#### Fase 4: Crear cluster EKS (~$0.30 por 15 min)
```bash
# 10. Crear cluster (tarda ~15 minutos)
eksctl create cluster -f k8s/cluster-config-learner-lab.yaml

# 11. Configurar kubectl
aws eks update-kubeconfig --region us-east-1 --name news2market-cluster

# 12. Verificar nodos
kubectl get nodes
```

#### Fase 5: Desplegar aplicación (~$0.50 por 30 min)
```bash
# 13. Aplicar manifests en orden
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-statefulset.yaml

# Esperar DBs
kubectl wait --for=condition=ready pod -l app=postgres -n news2market --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n news2market --timeout=300s

# Servicios
kubectl apply -f k8s/metrics-server.yaml
kubectl apply -f k8s/api-gateway-deployment.yaml
kubectl apply -f k8s/data-acquisition-deployment.yaml
kubectl apply -f k8s/text-processor-deployment.yaml
kubectl apply -f k8s/correlation-service-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/text-processor-hpa.yaml

# 14. Verificar
kubectl get pods -n news2market
kubectl get hpa -n news2market
```

#### Fase 6: Pruebas y evidencias (~$2.00 por 6-8 horas)
```bash
# 15. Acceder con NodePort
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
API_PORT=$(kubectl get svc api-gateway-service -n news2market -o jsonpath='{.spec.ports[0].nodePort}')
echo "API Gateway: http://$NODE_IP:$API_PORT"

# 16. Prueba de carga
./scripts/load-test.sh

# 17. Capturar evidencias
kubectl get hpa,pods -n news2market > evidencias.txt
kubectl logs -n news2market -l app=text-processor > logs.txt
```

#### Fase 7: LIMPIEZA (CRÍTICO) (~$0)
```bash
# 18. Eliminar namespace
kubectl delete namespace news2market

# 19. Eliminar cluster (tarda ~10 min)
eksctl delete cluster --name news2market-cluster --region us-east-1

# 20. Verificar sin recursos huérfanos
aws ec2 describe-instances
aws ec2 describe-volumes
```

### 💰 COSTO TOTAL ESTIMADO
- **Mínimo** (solo demo): $6-8 USD
- **Completo** (1 semana pruebas): $20-25 USD
- **Margen restante**: $25-30 USD

---

## 3. ARCHIVOS KUBERNETES

### ✅ Archivos creados (nuevos):

#### 1. `k8s/api-gateway-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: news2market
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    spec:
      containers:
      - name: api-gateway
        image: ${ECR_REGISTRY}/news2market/api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATA_SERVICE_URL
          value: "http://data-acquisition-service:8001"
        - name: PROCESS_SERVICE_URL
          value: "http://text-processor-service:8002"
        # ... más env vars
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
spec:
  type: NodePort  # Cambiar a NodePort para Learner Lab
  selector:
    app: api-gateway
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30800  # Puerto fijo (30000-32767)
```

**Cambios recomendados**:
- ✅ `type: LoadBalancer` → `type: NodePort` (ahorra $16/mes)
- ✅ `imagePullPolicy: Always` → OK para ECR
- ✅ `resources` ajustados a t3.medium

#### 2. `k8s/data-acquisition-deployment.yaml`
Similar estructura, puerto 8001, ClusterIP (interno).

#### 3. `k8s/cluster-config-learner-lab.yaml`
```yaml
metadata:
  name: news2market-cluster
  region: us-east-1

managedNodeGroups:
  - name: worker-nodes
    instanceType: t3.medium  # NO t3.large
    desiredCapacity: 2       # NO 3
    maxSize: 3
    volumeSize: 20           # NO 30
    privateNetworking: false # Evita NAT Gateway
```

### 📝 Cambios en archivos existentes:

#### `k8s/configmap.yaml` - OK, sin cambios necesarios
✅ Ya usa service names (postgres-service, redis-service)

#### `k8s/secrets.yaml` - REVISAR antes de AWS
⚠️ Cambiar contraseña por defecto:
```bash
# Generar nueva contraseña en base64
echo -n "TuPasswordSegura123!" | base64
# Reemplazar en secrets.yaml
```

#### `k8s/frontend-deployment.yaml` - Cambiar Service
```yaml
# ANTES (usa LoadBalancer = $$$ NLB)
spec:
  type: LoadBalancer

# DESPUÉS (usa NodePort = gratis)
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
```

#### `k8s/text-processor-hpa.yaml` - OK, sin cambios
✅ Ya está optimizado para t3.medium

#### `k8s/postgres-statefulset.yaml` - Reducir recursos
```yaml
# Ajustar si es necesario
resources:
  requests:
    memory: "256Mi"  # Reducir de 512Mi
    cpu: "100m"      # Reducir de 250m
```

---

## 4. VALIDACIÓN SIN COSTO

### Estrategia 1: Minikube (RECOMENDADO)

```bash
# 1. Instalar Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 2. Iniciar cluster local
minikube start --cpus=4 --memory=8192
minikube addons enable metrics-server

# 3. Preparar manifests
./scripts/prepare-local-manifests.sh

# 4. Build imágenes DENTRO de Minikube
eval $(minikube docker-env)
docker build -t news2market/api-gateway:latest ./backend/api-gateway
docker build -t news2market/data-acquisition:latest ./backend/data-acquisition
docker build -t news2market/text-processor:latest ./backend/text-processor
docker build -t news2market/correlation-service:latest ./backend/correlation-service
docker build -t news2market/frontend:latest ./frontend

# 5. Desplegar
kubectl apply -f k8s/local/namespace.yaml
kubectl apply -f k8s/local/configmap.yaml
kubectl apply -f k8s/local/secrets.yaml
kubectl apply -f k8s/local/postgres-statefulset.yaml
kubectl apply -f k8s/local/redis-statefulset.yaml
kubectl apply -f k8s/local/metrics-server.yaml
kubectl apply -f k8s/local/api-gateway-deployment.yaml
kubectl apply -f k8s/local/data-acquisition-deployment.yaml
kubectl apply -f k8s/local/text-processor-deployment.yaml
kubectl apply -f k8s/local/correlation-service-deployment.yaml
kubectl apply -f k8s/local/frontend-deployment.yaml
kubectl apply -f k8s/local/text-processor-hpa.yaml

# 6. Verificar
kubectl get pods -n news2market
kubectl get hpa -n news2market

# 7. Probar HPA
./scripts/test-scalability-minikube.sh
```

### Estrategia 2: Kind (más ligero)

```bash
# 1. Instalar Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/

# 2. Crear cluster
kind create cluster --name news2market

# 3. Cargar imágenes
kind load docker-image news2market/api-gateway:latest
# ... repetir para cada imagen

# 4. Desplegar (mismos pasos que Minikube)
```

### Estrategia 3: kubectl --dry-run

```bash
# Validar sintaxis SIN crear recursos
kubectl apply -f k8s/namespace.yaml --dry-run=client
kubectl apply -f k8s/configmap.yaml --dry-run=client
kubectl apply -f k8s/secrets.yaml --dry-run=client
# ... repetir para todos los manifests

# Si NO hay errores, los manifests son válidos
```

### Estrategia 4: Docker Compose primero

```bash
# SIEMPRE probar con docker-compose antes de K8s
cd backend
docker-compose up -d
docker-compose ps  # Verificar que todos están "Up (healthy)"
curl http://localhost:8000/health
```

---

## 5. CHECKLIST PRE-DESPLIEGUE

Ver archivo completo: [`docs/PRE_DEPLOYMENT_CHECKLIST.md`](docs/PRE_DEPLOYMENT_CHECKLIST.md)

### Resumen ejecutivo:

#### ✅ FASE 1: Local (Docker Compose)
- [ ] `docker-compose up` funciona sin errores
- [ ] Todos los health checks verdes
- [ ] Puedes hacer búsqueda, procesamiento y correlación

#### ✅ FASE 2: Minikube
- [ ] Minikube instalado
- [ ] Todas las imágenes buildeadas dentro de Minikube
- [ ] Pods en estado Running (no CrashLoopBackOff)
- [ ] HPA muestra métricas
- [ ] Prueba de carga escala de 2 a 4+ pods

#### ✅ FASE 3: AWS Config
- [ ] AWS CLI v2 instalado
- [ ] kubectl 1.28+ instalado
- [ ] eksctl instalado
- [ ] Credenciales del Learner Lab configuradas
- [ ] `aws sts get-caller-identity` funciona

#### ✅ FASE 4: Manifests
- [ ] `cluster-config-learner-lab.yaml` usa t3.medium
- [ ] Máximo 2-3 nodos
- [ ] Services usan NodePort (no LoadBalancer)
- [ ] Secrets tiene contraseña segura
- [ ] Todos los manifests pasan `--dry-run=client`

#### ✅ FASE 5: Scripts
- [ ] `validate-system.sh` ejecuta sin errores
- [ ] `build-and-push.sh` está listo (pero NO ejecutar aún)
- [ ] `deploy-to-eks.sh` revisado
- [ ] `load-test.sh` funciona en Minikube

---

## 6. RECURSOS AWS

### ✅ SÍ CREAR (Necesarios y baratos)

| Recurso | Cuándo | Costo/h | Total estimado |
|---------|--------|---------|----------------|
| **ECR Repositories (5)** | Antes del cluster | $0 | $0.10 total |
| **EKS Cluster** | Cuando estés listo | $0.10 | $4.00 (40h) |
| **2x EC2 t3.medium** | Con el cluster | $0.0832 | $3.33 (40h) |
| **EBS volumes (40 GB)** | Con los nodos | $0.005 | $0.12 |
| **Data Transfer** | Durante pruebas | Variable | $0.50 |

**Total: ~$8-10 USD** para una demostración académica completa.

### ❌ NO CREAR (Costosos para Learner Lab)

| Recurso | Por qué evitar | Costo evitado | Alternativa |
|---------|----------------|---------------|-------------|
| **ALB/NLB** | $0.0225/h + LCU | $16-20/mes | NodePort Services |
| **NAT Gateway** | $0.045/h + $0.045/GB | $32/mes | Subnets públicas |
| **RDS PostgreSQL** | $0.017/h | $12/mes | StatefulSet en K8s |
| **ElastiCache Redis** | $0.017/h | $12/mes | StatefulSet en K8s |
| **Elastic IPs sin usar** | $0.005/h | Pequeño pero acumula | No crear extras |
| **CloudWatch Logs detallados** | $0.50/GB | Variable | kubectl logs |
| **Route53 Hosted Zone** | $0.50/mes | $0.50 | No usar dominio custom |

**Ahorro total: ~$70+/mes** 🎉

---

## 7. DEMOSTRAR PARALELISMO

### Método 1: NodePort + curl (SIN ALB)

```bash
# 1. Obtener IP y puerto
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
API_PORT=$(kubectl get svc api-gateway-service -n news2market -o jsonpath='{.spec.ports[0].nodePort}')

echo "API Gateway: http://$NODE_IP:$API_PORT"

# 2. Generar carga
for i in {1..100}; do
  curl -s -X POST http://$NODE_IP:$API_PORT/api/v1/text/process \
    -H "Content-Type: application/json" \
    -d '{"text":"Test de paralelismo"}' &
done

# 3. Monitorear escalado
watch kubectl get hpa,pods -n news2market
```

### Método 2: kubectl port-forward (desde tu laptop)

```bash
# 1. Port forward
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 &

# 2. Usar el script de carga
./scripts/load-test.sh

# 3. El script automáticamente:
#    - Genera peticiones concurrentes
#    - Monitorea HPA
#    - Muestra distribución de carga entre pods
```

### Método 3: Logs paralelos

```bash
# Ver TODOS los workers procesando simultáneamente
kubectl logs -f -n news2market -l app=text-processor --all-containers --max-log-requests=10

# Output:
# [Pod 1] Processing text: "..."
# [Pod 2] Processing text: "..."
# [Pod 3] Processing text: "..."
# [Pod 1] Completed in 0.5s
# [Pod 2] Completed in 0.4s
```

### Evidencias académicas a capturar:

#### 1. Arquitectura distribuida
```bash
kubectl get all -n news2market -o wide
```
📸 Screenshot

#### 2. HPA escalando
```bash
watch -n 2 'kubectl get hpa,pods -n news2market'
```
🎥 Grabar video o serie de screenshots

#### 3. Distribución de carga
```bash
for pod in $(kubectl get pods -n news2market -l app=text-processor -o name); do
  echo "=== $pod ==="
  kubectl logs $pod -n news2market | grep -c "Processing"
done

# Output esperado:
# === pod/text-processor-abc123 ===
# 47
# === pod/text-processor-def456 ===
# 53
# === pod/text-processor-ghi789 ===
# 41
```
📊 Gráfico de distribución

#### 4. Métricas de recursos
```bash
kubectl top pods -n news2market
kubectl top nodes
```
📸 Screenshot mostrando CPU/RAM usage

#### 5. Speedup con más workers
```text
| Workers | Throughput | Tiempo 100 req | Speedup |
|---------|------------|----------------|---------|
| 1 pod   | 5 req/s    | 20s            | 1.0x    |
| 2 pods  | 9 req/s    | 11s            | 1.8x    |
| 3 pods  | 14 req/s   | 7s             | 2.9x    |
| 5 pods  | 22 req/s   | 4.5s           | 4.4x    |
```
📊 Tabla para el informe

---

## 🎯 RESUMEN EJECUTIVO

### Pasos finales antes de AWS:

1. **Ejecutar**:
   ```bash
   ./scripts/validate-system.sh
   ```
   ✅ Debe pasar sin errores

2. **Probar en Minikube**:
   ```bash
   ./scripts/prepare-local-manifests.sh
   minikube start --cpus=4 --memory=8192
   eval $(minikube docker-env)
   # Build imágenes...
   kubectl apply -f k8s/local/
   ./scripts/test-scalability-minikube.sh
   ```
   ✅ HPA debe escalar de 2 a 4+ pods

3. **Revisar archivos nuevos creados**:
   - `k8s/api-gateway-deployment.yaml`
   - `k8s/data-acquisition-deployment.yaml`
   - `k8s/cluster-config-learner-lab.yaml`
   - `scripts/build-and-push.sh`
   - `scripts/validate-system.sh`
   - `docs/AWS_LEARNER_LAB_GUIDE.md`

4. **Cuando estés listo para AWS**:
   ```bash
   # Iniciar Learner Lab
   # Configurar credenciales
   ./scripts/build-and-push.sh  # Push imágenes a ECR
   eksctl create cluster -f k8s/cluster-config-learner-lab.yaml
   # Desplegar...
   ./scripts/load-test.sh
   # Capturar evidencias
   # ELIMINAR TODO al terminar
   ```

---

## 📚 DOCUMENTACIÓN COMPLETA

- **`docs/PRE_DEPLOYMENT_CHECKLIST.md`**: Checklist detallado
- **`docs/LOCAL_VALIDATION_GUIDE.md`**: Guía de Minikube paso a paso
- **`docs/AWS_LEARNER_LAB_GUIDE.md`**: Optimización de costos AWS
- **`docs/AWS_DEPLOYMENT.md`**: Guía original de AWS EKS
- **`docs/BACKEND_ARCHITECTURE.md`**: Arquitectura del sistema

---

**✅ TODO LISTO PARA VALIDACIÓN LOCAL**  
**💰 COSTO ESTIMADO EN AWS: $20-25 USD de $50 disponibles**  
**🎓 EVIDENCIAS ACADÉMICAS: Paralelismo, escalabilidad, distribución**

**Última actualización**: 22 de diciembre de 2025
