# 🎓 Guía de Despliegue AWS EKS - Paso a Paso
## Para Proyecto Académico (AWS Learner Lab - $50 USD)

---

## 📋 RESUMEN EJECUTIVO

**Situación**: Proyecto completo y funcionando en Minikube  
**Objetivo**: Desplegarlo en AWS EKS para demostrar paralelismo y escalabilidad  
**Presupuesto**: $50 USD MÁXIMO  
**Tiempo estimado**: 2-3 horas  
**Costo estimado**: $20-$25 USD si se destruye después de 24 horas

---

## 🚫 LO QUE NO DEBES HACER (para no gastar dinero)

❌ **NO crear**: ALB, NLB, NAT Gateway  
❌ **NO habilitar**: CloudWatch Logs, RDS, ElastiCache  
❌ **NO usar**: instancias grandes (solo t3.small o t3.medium)  
❌ **NO dejar corriendo**: Apagar cluster después de las pruebas  
❌ **NO usar**: múltiples zonas de disponibilidad (solo 1 AZ es suficiente)

---

## 📦 PREREQUISITOS (ANTES DE EMPEZAR)

### 1. Software Necesario

```bash
# Verificar instalaciones
aws --version      # AWS CLI 2.x
kubectl version    # kubectl 1.28+
docker --version   # Docker 20+

# Si falta algo:
# AWS CLI: https://aws.amazon.com/cli/
# kubectl: curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
# eksctl: curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
```

### 2. Credenciales AWS Learner Lab

```bash
# En AWS Learner Lab, ve a:
# AWS Details → Show → AWS CLI credentials

# Copiar y pegar en terminal:
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="us-east-1"

# Verificar que funciona:
aws sts get-caller-identity
# Deberías ver tu Account ID
```

---

## 📁 ARCHIVOS DEL PROYECTO - ANÁLISIS COMPLETO

### GRUPO 1: Archivos que NO necesitan cambios

#### 1.1 Dockerfiles (5 archivos)

**Ubicación**: 
- `backend/api-gateway/Dockerfile`
- `backend/data-acquisition/Dockerfile`
- `backend/text-processor/Dockerfile`
- `backend/correlation-service/Dockerfile`
- `frontend/Dockerfile`

**¿Qué hacen?**: Definen cómo construir las imágenes Docker  
**¿Cambiar algo?**: ❌ NO  
**¿Por qué?**: Ya funcionan en Minikube, funcionarán igual en AWS  
**Servicio AWS**: Amazon ECR (Elastic Container Registry)  
**Costo**: $0.10/GB/mes (despreciable para proyecto pequeño)

---

#### 1.2 Backend Code (Python FastAPI)

**Ubicación**: `backend/*/`  
**¿Cambiar algo?**: ❌ NO  
**¿Por qué?**: El código ya maneja variables de entorno correctamente  
**Nota importante**: Ya tienes el fix de `DATABASE_URL` (construcción dinámica)

---

### GRUPO 2: Archivos de Kubernetes que SÍ necesitan ajuste

#### 2.1 ConfigMap (`k8s/configmap.yaml`)

**¿Qué es?**: Variables de configuración compartidas  
**¿Cambiar algo?**: ✅ SÍ - Agregar `ENV: production`

```yaml
# ANTES (Minikube):
data:
  LOG_LEVEL: INFO
  USE_MOCK_COLCAP: "true"

# DESPUÉS (AWS):
data:
  ENV: production          # ← AGREGAR ESTA LÍNEA
  LOG_LEVEL: INFO
  USE_MOCK_COLCAP: "true"
```

**¿Por qué?**: Los servicios esperan la variable `ENV`  
**Servicio AWS**: Ninguno (solo Kubernetes)  
**Costo**: $0  
**Comando exacto**: (Lo verás en PASO 6)

---

#### 2.2 Secrets (`k8s/secrets.yaml`)

**¿Qué es?**: Credenciales de base de datos (password)  
**¿Cambiar algo?**: ⚠️ OPCIONAL - Cambiar password por seguridad

```yaml
# Contraseña actual (base64): "password"
data:
  DATABASE_PASSWORD: cGFzc3dvcmQ=

# Para cambiar (genera base64):
echo -n "nueva_contraseña_segura" | base64
# Ejemplo resultado: bnVldmFfY29udHJhc2XDsWFfc2VndXJh

# Reemplazar en el archivo:
data:
  DATABASE_PASSWORD: bnVldmFfY29udHJhc2XDsWFfc2VndXJh
```

**¿Es obligatorio?**: ❌ NO (para demo académica está bien)  
**Servicio AWS**: Ninguno  
**Costo**: $0

---

#### 2.3 Deployments (5 archivos)

**Ubicación**: `k8s/*-deployment.yaml`

**¿Qué cambiar?**: La referencia a las imágenes Docker

**ANTES (Minikube)**:
```yaml
image: news2market/api-gateway:latest
imagePullPolicy: Never  # ← Usa imagen local
```

**DESPUÉS (AWS)**:
```yaml
image: ${ECR_REGISTRY}/news2market/api-gateway:latest
imagePullPolicy: Always  # ← Descarga de ECR
```

**¿Cómo lo hago?**: Con el script `prepare-aws-manifests.sh` (lo crearemos)  
**Servicio AWS**: ECR (registry de imágenes)  
**Costo**: $0.10/GB/mes

**Archivos afectados**:
1. `k8s/api-gateway-deployment.yaml`
2. `k8s/data-acquisition-deployment.yaml`
3. `k8s/text-processor-deployment.yaml`
4. `k8s/correlation-service-deployment.yaml`
5. `k8s/frontend-deployment.yaml`

---

#### 2.4 Services (Networking)

**¿Qué son?**: Exponen los pods dentro del cluster  
**¿Cambiar algo?**: ⚠️ SÍ - Cambiar tipo de servicio

**Para API Gateway** (`k8s/api-gateway-deployment.yaml`):

```yaml
# ANTES (Minikube):
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
spec:
  type: NodePort  # ← Minikube usa NodePort
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30800

# DESPUÉS (AWS):
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
spec:
  type: LoadBalancer  # ← AWS usa LoadBalancer
  ports:
  - port: 80          # ← Puerto externo (HTTP estándar)
    targetPort: 8000  # ← Puerto interno del pod
```

**¿Por qué?**: En AWS, `LoadBalancer` crea automáticamente un CLB (Classic Load Balancer)  
**Servicio AWS**: CLB (Classic Load Balancer)  
**Costo**: ⚠️ $0.025/hora (~$0.60/día) + $0.008/GB transferido  
**¿Es obligatorio?**: ✅ SÍ (para acceder desde fuera)

**Para los demás servicios** (data-acquisition, text-processor, correlation, frontend):
```yaml
spec:
  type: ClusterIP  # ← Mantener ClusterIP (solo interno)
```

**¿Por qué ClusterIP?**: Solo necesitas acceso externo al API Gateway, lo demás es interno.

---

#### 2.5 HPA (`k8s/text-processor-hpa.yaml`)

**¿Qué es?**: Horizontal Pod Autoscaler (escalado automático)  
**¿Cambiar algo?**: ❌ NO  

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: text-processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: text-processor
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**¿Por qué no cambiar?**: Ya está optimizado  
**Servicio AWS**: EKS Metrics Server (incluido gratis)  
**Costo**: $0  
**¿Es obligatorio?**: ✅ SÍ (es parte del objetivo académico)

---

#### 2.6 StatefulSets (PostgreSQL y Redis)

**Ubicación**:
- `k8s/postgres-statefulset.yaml`
- `k8s/redis-statefulset.yaml`

**¿Cambiar algo?**: ⚠️ Ajustar storage

**ANTES (Minikube)**:
```yaml
spec:
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

**DESPUÉS (AWS)**:
```yaml
spec:
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3  # ← Especificar tipo de volumen AWS
      resources:
        requests:
          storage: 5Gi  # ← Mínimo en EBS (AWS limita < 1Gi)
```

**Servicio AWS**: EBS (Elastic Block Store)  
**Costo**: $0.08/GB/mes = $0.40/mes por 5GB  
**¿Es obligatorio?**: ✅ SÍ (necesitas persistencia)

---

### GRUPO 3: Configuración del Cluster

#### 3.1 Cluster Config (`k8s/cluster-config-learner-lab.yaml`)

**¿Qué es?**: Configuración de tu cluster EKS  
**¿Cambiar algo?**: ⚠️ Revisar región y versión

```yaml
metadata:
  name: news2market-cluster
  region: us-east-1  # ← Verificar que sea tu región
  version: "1.28"    # ← Versión de Kubernetes

managedNodeGroups:
  - name: worker-nodes
    instanceType: t3.medium  # 2 CPU, 4 GB RAM
    desiredCapacity: 2       # 2 nodos
    minSize: 2
    maxSize: 3               # Permitir 1 nodo extra para HPA
```

**¿Está bien así?**: ✅ SÍ (ya optimizado para Learner Lab)  
**Servicio AWS**: EKS Control Plane + EC2 instances  
**Costo**: 
- EKS Control Plane: $0.10/hora = $2.40/día
- 2x t3.medium: $0.0832/hora = $2.00/día
- **TOTAL: ~$4.40/día**

**¿Es obligatorio?**: ✅ SÍ (es tu cluster Kubernetes)

---

### GRUPO 4: Scripts de Automatización

#### 4.1 Build and Push (`scripts/build-and-push.sh`)

**¿Qué hace?**: 
1. Construye las 5 imágenes Docker
2. Las sube a Amazon ECR

**¿Cambiar algo?**: ❌ NO (ya está listo)

**Variables importantes**:
```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
```

**Servicio AWS**: ECR  
**Costo**: ~$0.50 total (imágenes pequeñas)  
**¿Es obligatorio?**: ✅ SÍ (necesitas las imágenes en la nube)

---

#### 4.2 Deploy to EKS (`scripts/deploy-to-eks.sh`)

**¿Qué hace?**: Despliega todo en EKS automáticamente  
**¿Cambiar algo?**: ❌ NO (ya está listo)

**¿Es obligatorio?**: ⚠️ OPCIONAL (puedes hacerlo manual)

---

### GRUPO 5: Archivos que NO usar

#### 5.1 Ingress (`k8s/ingress.yaml`)

**¿Qué es?**: Load Balancer avanzado (ALB)  
**¿Usar?**: ❌ NO (cuesta $18-$22/mes)  
**Alternativa**: Usar Service type LoadBalancer (más barato)

---

## 🚀 PASOS DE EJECUCIÓN - ORDEN EXACTO

### PASO 0: Preparación Local

```bash
# 1. Ir al directorio del proyecto
cd /home/ivanausecha/Documentos/infra-paralela-common-crawl-colcap

# 2. Configurar credenciales AWS (desde Learner Lab)
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="us-east-1"

# 3. Verificar acceso
aws sts get-caller-identity
```

**Costo**: $0  
**Tiempo**: 2 minutos

---

### PASO 1: Instalar eksctl

```bash
# Descargar eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp

# Mover a PATH
sudo mv /tmp/eksctl /usr/local/bin

# Verificar
eksctl version
```

**Costo**: $0  
**Tiempo**: 1 minuto  
**¿Es obligatorio?**: ✅ SÍ (para crear el cluster)

---

### PASO 2: Crear Repositorios ECR

```bash
# Obtener Account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1

# Crear repositorios
aws ecr create-repository --repository-name news2market/api-gateway --region $AWS_REGION
aws ecr create-repository --repository-name news2market/data-acquisition --region $AWS_REGION
aws ecr create-repository --repository-name news2market/text-processor --region $AWS_REGION
aws ecr create-repository --repository-name news2market/correlation-service --region $AWS_REGION
aws ecr create-repository --repository-name news2market/frontend --region $AWS_REGION
```

**Servicio AWS**: ECR  
**Costo**: $0 (solo pagas por almacenamiento después)  
**Tiempo**: 2 minutos  
**¿Es obligatorio?**: ✅ SÍ

---

### PASO 3: Build y Push Imágenes

```bash
# Login a ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Usar el script automático
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh
```

**Alternativa manual** (si el script falla):
```bash
export ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# API Gateway
docker build -t news2market/api-gateway:latest ./backend/api-gateway
docker tag news2market/api-gateway:latest $ECR_REGISTRY/news2market/api-gateway:latest
docker push $ECR_REGISTRY/news2market/api-gateway:latest

# Repetir para los otros 4 servicios...
```

**Servicio AWS**: ECR  
**Costo**: ~$0.50 (almacenamiento de imágenes)  
**Tiempo**: 20-30 minutos (build de 5 imágenes)  
**¿Es obligatorio?**: ✅ SÍ

---

### PASO 4: Crear Cluster EKS

```bash
# Crear cluster (TARDA 15-20 MINUTOS)
eksctl create cluster -f k8s/cluster-config-learner-lab.yaml
```

**¿Qué hace?**:
1. Crea el EKS Control Plane
2. Lanza 2 instancias EC2 (t3.medium)
3. Configura networking (VPC, subnets, security groups)
4. Instala addons (CoreDNS, kube-proxy, VPC-CNI)

**Servicio AWS**: EKS + EC2 + VPC  
**Costo**: $0.10/hora (EKS) + $0.0832/hora (2x t3.medium) = **$0.19/hora**  
**Tiempo**: 15-20 minutos  
**¿Es obligatorio?**: ✅ SÍ

**Verificar que funcionó**:
```bash
# Ver nodos
kubectl get nodes

# Deberías ver algo como:
# NAME                        STATUS   ROLES    AGE   VERSION
# ip-192-168-x-x.ec2.internal Ready    <none>   5m    v1.28.x
# ip-192-168-y-y.ec2.internal Ready    <none>   5m    v1.28.x
```

---

### PASO 5: Preparar Manifests para AWS

Crear script para reemplazar referencias de imágenes:

```bash
# Crear script
cat > scripts/prepare-aws-manifests.sh << 'EOF'
#!/bin/bash
set -e

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "🔧 Preparando manifests para AWS..."
echo "ECR Registry: $ECR_REGISTRY"

# Crear directorio aws/ si no existe
mkdir -p k8s/aws

# Copiar todos los manifests
cp k8s/namespace.yaml k8s/aws/
cp k8s/configmap.yaml k8s/aws/
cp k8s/secrets.yaml k8s/aws/
cp k8s/*-deployment.yaml k8s/aws/
cp k8s/*-statefulset.yaml k8s/aws/
cp k8s/*-hpa.yaml k8s/aws/
cp k8s/metrics-server.yaml k8s/aws/

# Reemplazar ${ECR_REGISTRY} con el valor real
find k8s/aws/ -type f -name "*.yaml" -exec sed -i "s|\${ECR_REGISTRY}|$ECR_REGISTRY|g" {} \;

# Cambiar imagePullPolicy de Never a Always
find k8s/aws/ -type f -name "*.yaml" -exec sed -i "s|imagePullPolicy: Never|imagePullPolicy: Always|g" {} \;

# Agregar ENV: production al ConfigMap
sed -i '/LOG_LEVEL:/i \  ENV: production' k8s/aws/configmap.yaml

# Cambiar API Gateway Service a LoadBalancer
sed -i 's/type: NodePort/type: LoadBalancer/' k8s/aws/api-gateway-deployment.yaml
sed -i '/nodePort:/d' k8s/aws/api-gateway-deployment.yaml

# Agregar storageClassName: gp3 a StatefulSets
sed -i '/accessModes:/i \      storageClassName: gp3' k8s/aws/postgres-statefulset.yaml
sed -i '/accessModes:/i \      storageClassName: gp3' k8s/aws/redis-statefulset.yaml

# Aumentar storage a 5Gi mínimo
sed -i 's/storage: 1Gi/storage: 5Gi/g' k8s/aws/postgres-statefulset.yaml
sed -i 's/storage: 1Gi/storage: 5Gi/g' k8s/aws/redis-statefulset.yaml

echo "✅ Manifests preparados en k8s/aws/"
EOF

chmod +x scripts/prepare-aws-manifests.sh
./scripts/prepare-aws-manifests.sh
```

**Servicio AWS**: Ninguno  
**Costo**: $0  
**Tiempo**: 1 minuto  
**¿Es obligatorio?**: ✅ SÍ

---

### PASO 6: Desplegar en Kubernetes

```bash
# 1. Namespace
kubectl apply -f k8s/aws/namespace.yaml

# 2. ConfigMap y Secrets
kubectl apply -f k8s/aws/configmap.yaml
kubectl apply -f k8s/aws/secrets.yaml

# 3. Databases (StatefulSets)
kubectl apply -f k8s/aws/postgres-statefulset.yaml
kubectl apply -f k8s/aws/redis-statefulset.yaml

# Esperar que estén listas (IMPORTANTE)
kubectl wait --for=condition=ready pod -l app=postgres -n news2market --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n news2market --timeout=300s

# 4. Metrics Server (para HPA)
kubectl apply -f k8s/aws/metrics-server.yaml

# Esperar 30 segundos
sleep 30

# 5. Microservicios
kubectl apply -f k8s/aws/api-gateway-deployment.yaml
kubectl apply -f k8s/aws/data-acquisition-deployment.yaml
kubectl apply -f k8s/aws/text-processor-deployment.yaml
kubectl apply -f k8s/aws/correlation-service-deployment.yaml
kubectl apply -f k8s/aws/frontend-deployment.yaml

# 6. HPA
kubectl apply -f k8s/aws/text-processor-hpa.yaml
```

**Servicio AWS**: EKS (ya pagado)  
**Costo**: $0 adicional  
**Tiempo**: 5-10 minutos  
**¿Es obligatorio?**: ✅ SÍ

---

### PASO 7: Verificar Despliegue

```bash
# Ver todos los pods
kubectl get pods -n news2market

# Deberías ver 13 pods Running:
# - api-gateway (2)
# - data-acquisition (2)
# - text-processor (2)
# - correlation-service (2)
# - frontend (3)
# - postgres (1)
# - redis (1)

# Ver servicios
kubectl get svc -n news2market

# Ver HPA
kubectl get hpa -n news2market
```

**Costo**: $0  
**Tiempo**: 2 minutos

---

### PASO 8: Acceder al Sistema

```bash
# Obtener URL del Load Balancer (API Gateway)
kubectl get svc api-gateway-service -n news2market

# Esperar 2-3 minutos a que el LoadBalancer esté listo
# Verás algo como:
# NAME                  TYPE           EXTERNAL-IP
# api-gateway-service   LoadBalancer   a1b2c3...us-east-1.elb.amazonaws.com

# Guardar URL
export LB_URL=$(kubectl get svc api-gateway-service -n news2market -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Probar health check
curl http://$LB_URL/api/v1/health
```

**Servicio AWS**: Classic Load Balancer (creado automáticamente)  
**Costo**: $0.025/hora = $0.60/día  
**Tiempo**: 3 minutos  
**¿Es obligatorio?**: ✅ SÍ (para acceso externo)

---

### PASO 9: Probar HPA (Escalado Automático)

```bash
# Generar carga
for i in {1..1000}; do
  curl -s http://$LB_URL/api/v1/health > /dev/null &
done

# En otra terminal, monitorear
watch -n 2 'kubectl get hpa,pods -n news2market | grep text-processor'

# Deberías ver:
# - CPU aumentando (0% → 70%+)
# - REPLICAS escalando (2 → 3 → 4... → 10)
# - Nuevos pods: Pending → Running
```

**Costo**: $0 (uso normal)  
**Tiempo**: 5 minutos de prueba  
**¿Es obligatorio?**: ✅ SÍ (es el objetivo del proyecto)

---

### PASO 10: Capturar Evidencia (Para Informe)

```bash
# 1. Estado inicial
kubectl get hpa,pods -n news2market > evidencia-estado-inicial.txt

# 2. Después de generar carga
kubectl get hpa,pods -n news2market > evidencia-post-carga.txt

# 3. Logs de diferentes pods (paralelismo)
kubectl logs -n news2market -l app=text-processor --prefix --tail=20 > evidencia-logs-paralelismo.txt

# 4. Recursos consumidos
kubectl top pods -n news2market > evidencia-recursos.txt

# 5. Arquitectura del cluster
kubectl get all -n news2market > evidencia-arquitectura.txt
```

**Costo**: $0  
**Tiempo**: 5 minutos

---

## 💰 RESUMEN DE COSTOS

### Costos por Servicio

| Servicio | Tipo | Costo/hora | Costo/día | Obligatorio |
|----------|------|-----------|-----------|-------------|
| EKS Control Plane | Managed | $0.10 | $2.40 | ✅ SÍ |
| EC2 (2x t3.medium) | Compute | $0.08 | $2.00 | ✅ SÍ |
| Classic LB | Networking | $0.025 | $0.60 | ✅ SÍ |
| EBS (10 GB) | Storage | $0.0003 | $0.01 | ✅ SÍ |
| ECR Storage | Registry | - | $0.50 | ✅ SÍ |
| Data Transfer | Network | $0.01/GB | $0.50 | - |
| **TOTAL** | | **~$0.21/h** | **~$5.50/día** | |

### Escenarios de Uso

1. **Prueba rápida (3 horas)**:
   - Costo: $0.63
   - Recomendado para: Primera prueba

2. **Demo académica (8 horas)**:
   - Costo: $1.68
   - Recomendado para: Presentación en clase

3. **Proyecto completo (24 horas)**:
   - Costo: $5.04
   - Recomendado para: Desarrollo y pruebas

4. **Semana completa (7 días)**:
   - Costo: $35-$38
   - ⚠️ NO recomendado (gasta casi todo el presupuesto)

---

## 🗑️ PASO 11: LIMPIAR TODO (Destruir Recursos)

**IMPORTANTE**: Hacer esto SIEMPRE al terminar para no gastar dinero

```bash
# 1. Eliminar servicios de Kubernetes (libera LoadBalancer)
kubectl delete -f k8s/aws/

# Esperar 2 minutos a que se elimine el LoadBalancer
sleep 120

# 2. Eliminar cluster EKS (TARDA 10-15 MINUTOS)
eksctl delete cluster --name news2market-cluster --region us-east-1

# 3. Eliminar imágenes de ECR (opcional, para ahorrar $0.50)
aws ecr delete-repository --repository-name news2market/api-gateway --force
aws ecr delete-repository --repository-name news2market/data-acquisition --force
aws ecr delete-repository --repository-name news2market/text-processor --force
aws ecr delete-repository --repository-name news2market/correlation-service --force
aws ecr delete-repository --repository-name news2market/frontend --force

# 4. Verificar que TODO se eliminó
aws eks list-clusters
aws ec2 describe-instances --filters "Name=tag:Name,Values=news2market*"
aws elb describe-load-balancers
```

**Tiempo**: 15-20 minutos  
**Costo ahorrado**: Todo lo que no uses

---

## 🎯 CHECKLIST FINAL

Antes de presentar tu proyecto, verifica:

- [ ] Cluster EKS creado y funcionando
- [ ] 13 pods en estado `Running`
- [ ] HPA configurado (texto-processor: 2-10 réplicas)
- [ ] Load Balancer accesible desde navegador
- [ ] Health check responde: `{"status":"healthy"}`
- [ ] HPA escala correctamente bajo carga (2→10 réplicas)
- [ ] Evidencia capturada (screenshots, logs, métricas)
- [ ] Costo total < $10 USD

**Después de presentar**:
- [ ] Cluster eliminado
- [ ] LoadBalancer eliminado
- [ ] Imágenes ECR eliminadas (opcional)
- [ ] Verificado en AWS Console: $0 recursos activos

---

## 📞 TROUBLESHOOTING

### Problema 1: "eksctl command not found"
```bash
# Reinstalar eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

### Problema 2: "Error creating cluster - insufficient quota"
**Solución**: Learner Lab tiene límites. Usar solo:
- 2 nodos (no 3)
- Instancias t3.small (no t3.medium)

### Problema 3: "Pods stuck in Pending"
```bash
# Ver eventos
kubectl describe pod <pod-name> -n news2market

# Causas comunes:
# - Insuficiente memoria/CPU en nodos → Reducir resources.requests
# - Imagen no encontrada → Verificar ECR registry
```

### Problema 4: "Can't pull image from ECR"
```bash
# Verificar permisos IAM del cluster
kubectl describe pod <pod-name> -n news2market | grep -A 5 Events

# Solución: Agregar política ECR a worker nodes
eksctl create iamidentitymapping --cluster news2market-cluster --region us-east-1 \
  --arn arn:aws:iam::<AWS_ACCOUNT_ID>:role/eksctl-news2market-cluster-nodegroup-NodeInstanceRole-XXXXX \
  --username system:node:{{EC2PrivateDNSName}} --group system:bootstrappers,system:nodes
```

### Problema 5: "HPA shows <unknown> for metrics"
```bash
# Reinstalar metrics-server
kubectl delete -f k8s/aws/metrics-server.yaml
sleep 10
kubectl apply -f k8s/aws/metrics-server.yaml

# Esperar 2 minutos y verificar
kubectl top nodes
kubectl top pods -n news2market
```

---

## 🎓 RESUMEN PARA EL PROFESOR

**Arquitectura desplegada**:
- Microservicios distribuidos (5 servicios)
- Kubernetes (EKS) con 2 nodos
- Escalado horizontal automático (HPA: 2→10 réplicas)
- Persistencia con StatefulSets (PostgreSQL + Redis)
- Load Balancing automático

**Conceptos demostrados**:
1. **Paralelismo**: Múltiples pods procesando simultáneamente
2. **Escalabilidad**: HPA ajusta réplicas según CPU
3. **Alta disponibilidad**: Múltiples réplicas de cada servicio
4. **Orquestación**: Kubernetes gestiona contenedores automáticamente
5. **Cloud Computing**: Infraestructura elástica en AWS

**Costo total**: $5-$10 USD (24 horas de uso)

---

**✅ Guía completa. Sigue los pasos en orden y tendrás tu sistema en AWS EKS.**
