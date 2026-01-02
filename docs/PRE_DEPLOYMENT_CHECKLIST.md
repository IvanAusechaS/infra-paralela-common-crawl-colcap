# ========================================
# CHECKLIST PRE-DESPLIEGUE EN AWS EKS
# ========================================
# News2Market - Infraestructuras Paralelas y Distribuidas
# Fecha: Diciembre 2025
# Objetivo: Validar que TODO esté listo antes de gastar crédito en AWS

## ✅ FASE 1: VALIDACIÓN LOCAL (0 USD - Sin costo)

### 1.1 Docker Compose funciona completamente
- [ ] `docker-compose up` levanta todos los servicios sin errores
- [ ] Todos los health checks están en verde
- [ ] Frontend accesible en http://localhost
- [ ] API Gateway responde en http://localhost:8000/health
- [ ] Puedes hacer una búsqueda de noticias (Data Acquisition)
- [ ] Puedes procesar texto (Text Processor)
- [ ] Puedes calcular correlación (Correlation Service)

**Comando de validación**:
```bash
cd backend
docker-compose up -d
docker-compose ps  # Todos deben estar "Up (healthy)"
curl http://localhost:8000/health  # Debe devolver {"status": "healthy"}
```

---

### 1.2 Imágenes Docker se construyen correctamente
- [ ] api-gateway/Dockerfile builds sin errores
- [ ] data-acquisition/Dockerfile builds sin errores
- [ ] text-processor/Dockerfile builds sin errores
- [ ] correlation-service/Dockerfile builds sin errores
- [ ] frontend/Dockerfile builds sin errores

**Comando de validación**:
```bash
docker build -t test-api-gateway ./backend/api-gateway
docker build -t test-data-acquisition ./backend/data-acquisition
docker build -t test-text-processor ./backend/text-processor
docker build -t test-correlation-service ./backend/correlation-service
docker build -t test-frontend ./frontend
```

---

### 1.3 Variables de entorno correctas
- [ ] ConfigMap tiene todos los hosts/ports correctos
- [ ] Secrets tiene credenciales de DB (aunque sean simples)
- [ ] No hay hardcoded IPs o localhost en manifests

**Archivos a revisar**:
- `k8s/configmap.yaml`
- `k8s/secrets.yaml`
- `backend/*/app.py` (verificar que usen env vars)

---

## ✅ FASE 2: VALIDACIÓN CON MINIKUBE/KIND (0 USD - Sin costo)

### 2.1 Instalar Minikube o Kind
- [ ] Minikube instalado y funcionando
- [ ] Metrics server habilitado

**Instalación rápida (Linux)**:
```bash
# Opción 1: Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
minikube start --cpus=4 --memory=8192

# Opción 2: Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
kind create cluster --config k8s/kind-config.yaml
```

---

### 2.2 Cargar imágenes en Minikube
- [ ] Imágenes disponibles en el cluster local

**Comandos**:
```bash
# Con Minikube
eval $(minikube docker-env)
docker build -t news2market/api-gateway:latest ./backend/api-gateway
docker build -t news2market/data-acquisition:latest ./backend/data-acquisition
docker build -t news2market/text-processor:latest ./backend/text-processor
docker build -t news2market/correlation-service:latest ./backend/correlation-service
docker build -t news2market/frontend:latest ./frontend

# Con Kind
kind load docker-image news2market/api-gateway:latest
kind load docker-image news2market/data-acquisition:latest
# ... repetir para cada imagen
```

---

### 2.3 Desplegar en Minikube con dry-run
- [ ] Namespace se crea sin errores
- [ ] ConfigMap y Secrets son válidos
- [ ] Todos los Deployments pasan validación
- [ ] Services se crean correctamente
- [ ] HPA es válido

**Comando de dry-run (SIN CREAR NADA)**:
```bash
kubectl apply -f k8s/namespace.yaml --dry-run=client
kubectl apply -f k8s/configmap.yaml --dry-run=client
kubectl apply -f k8s/secrets.yaml --dry-run=client
kubectl apply -f k8s/postgres-statefulset.yaml --dry-run=client
kubectl apply -f k8s/redis-statefulset.yaml --dry-run=client
kubectl apply -f k8s/api-gateway-deployment.yaml --dry-run=client
kubectl apply -f k8s/data-acquisition-deployment.yaml --dry-run=client
kubectl apply -f k8s/text-processor-deployment.yaml --dry-run=client
kubectl apply -f k8s/correlation-service-deployment.yaml --dry-run=client
kubectl apply -f k8s/frontend-deployment.yaml --dry-run=client
kubectl apply -f k8s/text-processor-hpa.yaml --dry-run=client
```

**Si no hay errores, proceder a desplegar realmente**:
```bash
# Crear namespace
kubectl apply -f k8s/namespace.yaml

# Crear configuración
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Desplegar bases de datos
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-statefulset.yaml

# Esperar a que estén listas
kubectl wait --for=condition=ready pod -l app=postgres -n news2market --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n news2market --timeout=300s

# Desplegar servicios (sin ${ECR_REGISTRY}, usar imágenes locales)
# Editar temporalmente los manifests para quitar ${ECR_REGISTRY}
kubectl apply -f k8s/api-gateway-deployment.yaml
kubectl apply -f k8s/data-acquisition-deployment.yaml
kubectl apply -f k8s/text-processor-deployment.yaml
kubectl apply -f k8s/correlation-service-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Instalar metrics server
kubectl apply -f k8s/metrics-server.yaml

# Crear HPA
kubectl apply -f k8s/text-processor-hpa.yaml
```

---

### 2.4 Verificar pods y servicios en Minikube
- [ ] Todos los pods están en estado Running
- [ ] No hay CrashLoopBackOff
- [ ] Services tienen ClusterIP asignado
- [ ] HPA muestra métricas (puede tardar 1-2 min)

**Comandos de verificación**:
```bash
kubectl get pods -n news2market
kubectl get svc -n news2market
kubectl get hpa -n news2market
kubectl top pods -n news2market  # Verificar que metrics-server funciona
```

---

### 2.5 Probar la aplicación en Minikube
- [ ] Port-forward al API Gateway funciona
- [ ] Puedes hacer peticiones HTTP
- [ ] Frontend es accesible

**Port forwarding**:
```bash
# API Gateway
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 &

# Frontend
kubectl port-forward -n news2market svc/frontend-service 8080:80 &

# Probar
curl http://localhost:8000/health
curl http://localhost:8080
```

---

### 2.6 Probar escalado automático (HPA)
- [ ] HPA está activo
- [ ] Al enviar carga, los pods escalan
- [ ] Después de 5 min sin carga, los pods bajan

**Prueba de escalado local**:
```bash
# Ver estado inicial
kubectl get hpa text-processor-hpa -n news2market

# Generar carga (script simple)
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/text/process \
    -H "Content-Type: application/json" \
    -d '{"text":"Test de carga para activar HPA"}' &
done

# Monitorear escalado
watch kubectl get hpa,pods -n news2market
```

---

## ✅ FASE 3: PREPARACIÓN DE AWS (0 USD aún - Solo configuración)

### 3.1 Cuenta AWS Learner Lab lista
- [ ] Acceso a AWS Learner Lab activo
- [ ] Crédito de $50 USD disponible
- [ ] Región seleccionada: **us-east-1** (más barata)

---

### 3.2 AWS CLI configurado
- [ ] AWS CLI v2 instalado
- [ ] Credenciales temporales del Learner Lab copiadas

**Obtener credenciales en Learner Lab**:
1. Ir a "AWS Details" en Learner Lab
2. Copiar "AWS CLI" credentials
3. Pegar en `~/.aws/credentials`

**Verificar**:
```bash
aws --version  # Debe ser 2.x
aws sts get-caller-identity  # Debe mostrar tu Account ID
```

---

### 3.3 kubectl y eksctl instalados
- [ ] kubectl instalado (versión 1.28+)
- [ ] eksctl instalado

**Verificar**:
```bash
kubectl version --client
eksctl version
```

---

### 3.4 Manifests ajustados para EKS
- [ ] Todas las imágenes usan placeholder `${ECR_REGISTRY}`
- [ ] No hay `LoadBalancer` en Services (solo ClusterIP y NodePort)
- [ ] No hay `PersistentVolumeClaims` sin StorageClass
- [ ] Recursos (CPU/memoria) son razonables para t3.medium

---

### 3.5 Cluster config revisado
- [ ] `k8s/cluster-config.yaml` tiene instancias pequeñas (t3.small o t3.medium)
- [ ] No más de 3 nodos inicialmente
- [ ] Sin NAT Gateway (usar public subnets)

**Editar cluster-config.yaml**:
```yaml
nodeGroups:
  - name: main-nodes
    instanceType: t3.medium  # ✅ Cambiar de t3.large a t3.medium
    desiredCapacity: 2       # ✅ Cambiar de 3 a 2
    minSize: 2
    maxSize: 3               # ✅ Cambiar de 5 a 3
    volumeSize: 20           # ✅ Cambiar de 30 a 20
```

---

## ✅ FASE 4: COSTOS ESTIMADOS Y LÍMITES

### 4.1 Recursos que SÍ vas a crear (necesarios)
| Recurso | Costo/hora | Costo/24h | Notas |
|---------|------------|-----------|-------|
| **EKS Cluster** | $0.10 | $2.40 | Control plane, unavoidable |
| **2x t3.medium EC2** | $0.0832 | $2.00 | Nodos workers |
| **EBS volúmenes (40GB)** | $0.005 | $0.12 | Storage para nodos |
| **Data Transfer** | Variable | ~$0.50 | Salida a internet |
| **TOTAL** | ~$0.27/h | ~$6.50/día | **Para 1 semana: ~$45** |

✅ **Margen de seguridad**: Te quedan ~$5 USD para imprevistos.

---

### 4.2 Recursos que NO debes crear (costosos)
- ❌ **Application Load Balancer (ALB)**: $0.0225/h + $0.008/LCU = ~$20/mes
- ❌ **NAT Gateway**: $0.045/h = ~$32/mes
- ❌ **RDS (db.t3.micro)**: $0.017/h = ~$12/mes
- ❌ **ElastiCache (cache.t3.micro)**: $0.017/h = ~$12/mes
- ❌ **Elastic IPs sin usar**: $0.005/h cada una

**Alternativas**:
- En lugar de ALB → Usar `NodePort` Services
- En lugar de NAT → Usar subnets públicas
- En lugar de RDS → Usar `StatefulSet` de PostgreSQL
- En lugar de ElastiCache → Usar `StatefulSet` de Redis

---

## ✅ FASE 5: ESTRATEGIA DE DESPLIEGUE EN EKS (Cuando llegue el momento)

### 5.1 Orden de creación de recursos AWS
```
1. ✅ Crear ECR repositories (gratis hasta 500 MB)
2. ✅ Build y push de imágenes Docker
3. ✅ Crear cluster EKS con eksctl (~10-15 min)
4. ✅ Configurar kubectl
5. ✅ Aplicar manifests en orden
6. ✅ Verificar con NodePort (sin LoadBalancer)
7. ✅ Prueba de carga para demostrar HPA
8. ✅ Capturar evidencias (screenshots, logs)
9. ❗ DESTRUIR TODO al terminar
```

---

### 5.2 Comandos para crear infraestructura (SOLO cuando estés listo)

```bash
# 1. Crear repositorios ECR
aws ecr create-repository --repository-name news2market/api-gateway
aws ecr create-repository --repository-name news2market/data-acquisition
aws ecr create-repository --repository-name news2market/text-processor
aws ecr create-repository --repository-name news2market/correlation-service
aws ecr create-repository --repository-name news2market/frontend

# 2. Login a ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 3. Build y push (hacer esto ANTES de crear el cluster)
# Usar el script scripts/build-and-push.sh que crearemos

# 4. Crear cluster EKS
eksctl create cluster -f k8s/cluster-config.yaml

# 5. Desplegar aplicación
# Usar el script scripts/deploy-to-eks.sh que ya creamos

# 6. Acceder con NodePort (sin ALB)
kubectl get nodes -o wide  # Obtener IP pública de un nodo
NODE_PORT=$(kubectl get svc api-gateway-service -n news2market -o jsonpath='{.spec.ports[0].nodePort}')
# Acceder: http://<NODE_PUBLIC_IP>:$NODE_PORT
```

---

### 5.3 Evidencias académicas a capturar

**Antes del despliegue**:
- [ ] Screenshot de `docker-compose ps` funcionando
- [ ] Screenshot de Minikube con todos los pods Running
- [ ] Screenshot de HPA escalando en Minikube

**Durante el despliegue en EKS**:
- [ ] Screenshot de cluster EKS en consola AWS
- [ ] Output de `kubectl get nodes`
- [ ] Output de `kubectl get pods -n news2market`
- [ ] Output de `kubectl top pods -n news2market`
- [ ] Screenshot de HPA escalando (de 2 a 5+ pods)

**Demostración de paralelismo**:
- [ ] Logs de múltiples workers procesando simultáneamente
- [ ] Gráfico de CPU usage durante carga
- [ ] Tiempo de procesamiento con 1 worker vs 5 workers

**Comandos para capturar logs**:
```bash
# Ver todos los logs de text-processor
kubectl logs -n news2market -l app=text-processor --all-containers --tail=100

# Ver distribución de carga entre pods
for pod in $(kubectl get pods -n news2market -l app=text-processor -o name); do
  echo "=== $pod ==="
  kubectl logs $pod -n news2market | grep -c "Processing"
done
```

---

## ✅ FASE 6: LIMPIEZA Y DESTRUCCIÓN (IMPORTANTE)

### 6.1 Destruir recursos en orden inverso
```bash
# 1. Eliminar todos los recursos de Kubernetes
kubectl delete namespace news2market

# 2. Eliminar cluster EKS (esto tarda ~10 min)
eksctl delete cluster --name news2market-cluster --region us-east-1

# 3. Eliminar imágenes de ECR (opcional, pero ahorra espacio)
aws ecr delete-repository --repository-name news2market/api-gateway --force
aws ecr delete-repository --repository-name news2market/data-acquisition --force
aws ecr delete-repository --repository-name news2market/text-processor --force
aws ecr delete-repository --repository-name news2market/correlation-service --force
aws ecr delete-repository --repository-name news2market/frontend --force

# 4. Verificar que NO queden recursos huérfanos
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' --output table
aws ec2 describe-volumes --query 'Volumes[*].[VolumeId,State]' --output table
aws elb describe-load-balancers --output table
```

---

## 📊 CHECKLIST FINAL ANTES DE CREAR EL CLUSTER

- [ ] ✅ Docker Compose funciona 100%
- [ ] ✅ Todas las imágenes se construyen sin errores
- [ ] ✅ Minikube deployment exitoso
- [ ] ✅ HPA funciona en Minikube
- [ ] ✅ AWS CLI configurado con credenciales del Learner Lab
- [ ] ✅ cluster-config.yaml tiene instancias t3.medium (no t3.large)
- [ ] ✅ Máximo 2-3 nodos inicialmente
- [ ] ✅ Services usan ClusterIP o NodePort (NO LoadBalancer en servicios internos)
- [ ] ✅ Tienes un plan de limpieza al terminar
- [ ] ✅ Sabes que tienes ~$45-50 USD para 1 semana de pruebas
- [ ] ✅ Documentación lista para capturar evidencias

---

## 🎓 CONSEJOS ACADÉMICOS FINALES

1. **No dejes el cluster corriendo de noche**: Cada hora cuenta. Apágalo cuando no lo uses.
2. **Usa Minikube para iteraciones**: Cualquier prueba o debug, hazlo primero en Minikube.
3. **Captura evidencias INMEDIATAMENTE**: Una vez que todo funciona, toma screenshots/logs antes de apagar.
4. **Documenta costos reales**: AWS Cost Explorer te muestra el gasto exacto. Inclúyelo en tu informe.
5. **Ten un plan B**: Si algo sale mal en EKS, Minikube es suficiente para demostrar la arquitectura.

---

**Última actualización**: Diciembre 2025
**Autor**: Asistente de GitHub Copilot
