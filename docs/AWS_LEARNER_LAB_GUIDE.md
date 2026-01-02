# ========================================
# AWS LEARNER LAB: GUÍA ESPECÍFICA
# ========================================
# Cómo maximizar tu crédito de $50 USD y evitar gastos innecesarios

## 🎓 Contexto de AWS Learner Lab

AWS Learner Lab es un **sandbox educacional** con:
- ✅ **Crédito**: $50 USD (NO recargable)
- ⏰ **Sesión**: 4 horas activa, luego se pausa
- 🔄 **Recursos**: Se CONSERVAN entre sesiones (pero EC2 apagados se destruyen)
- ❌ **Limitaciones**: 
  - No puedes crear usuarios IAM adicionales
  - No puedes crear VPCs custom (usas la default)
  - Algunas regiones bloqueadas
  - No puedes crear Route53 hosted zones
  - No puedes crear Certificate Manager certs

---

## 💰 ESTRATEGIA DE COSTOS PARA TU PROYECTO

### Presupuesto desglosado (1 semana de pruebas)

| Fase | Duración | Costo estimado |
|------|----------|----------------|
| **Preparación** (build de imágenes, ECR) | 2 horas | $0.20 |
| **Despliegue inicial** (crear cluster) | 1 hora | $0.30 |
| **Pruebas y ajustes** (2-3 sesiones de 2h) | 6 horas | $1.80 |
| **Demostración final** (captura de evidencias) | 3 horas | $1.00 |
| **Cluster running** (5 días x 8h/día) | 40 horas | $12.00 |
| **Buffer** (imprevistos, rebuilds) | - | $5.00 |
| **TOTAL** | - | **~$20-25 USD** |

**✅ Margen de seguridad**: Te quedan ~$25-30 USD extras.

---

## ⚠️ RECURSOS QUE SÍ PUEDES USAR (Bajo costo)

### 1. Amazon ECR (Container Registry)
- **Costo**: $0.10/GB/mes
- **Estimado**: ~100 MB de imágenes = $0.01/mes
- **Instrucción**: 
  ```bash
  aws ecr create-repository --repository-name news2market/api-gateway
  ```

### 2. Amazon EKS (Kubernetes)
- **Costo**: $0.10/hora por el control plane
- **Estimado**: 40 horas = $4.00
- **Instrucción**: 
  ```bash
  eksctl create cluster -f k8s/cluster-config.yaml
  ```

### 3. EC2 (Nodos workers)
- **Instancia recomendada**: **t3.medium** (2 vCPU, 4 GB RAM)
- **Costo**: $0.0416/hora ($0.0832 por 2 instancias)
- **Estimado**: 2 x t3.medium x 40h = $3.33
- **⚠️ IMPORTANTE**: NO usar t3.large o mayores

### 4. EBS (Storage)
- **Costo**: $0.10/GB/mes
- **Estimado**: 40 GB x $0.10 = $4.00/mes (prorrateado)
- **Instrucción**: Se crea automáticamente con los nodos

### 5. Data Transfer (salida a internet)
- **Costo**: $0.09/GB (primeros 10TB)
- **Estimado**: ~5 GB = $0.45

---

## 🚫 RECURSOS QUE DEBES EVITAR (Costosos o bloqueados)

### 1. ❌ Application Load Balancer (ALB)
- **Costo**: $0.0225/hora + $0.008/LCU
- **Por qué evitar**: ~$16/mes, consume mucho crédito
- **Alternativa**: Usar **NodePort** Services

### 2. ❌ Network Load Balancer (NLB)
- **Costo**: $0.0225/hora + $0.006/NLCU
- **Por qué evitar**: Similar al ALB
- **Alternativa**: Usar **NodePort** Services

### 3. ❌ NAT Gateway
- **Costo**: $0.045/hora + $0.045/GB procesado
- **Por qué evitar**: ~$32/mes
- **Alternativa**: Usar **subnets públicas** para los nodos

### 4. ❌ RDS (PostgreSQL administrado)
- **Costo**: db.t3.micro = $0.017/hora
- **Por qué evitar**: ~$12/mes
- **Alternativa**: Usar **StatefulSet** de PostgreSQL en Kubernetes

### 5. ❌ ElastiCache (Redis administrado)
- **Costo**: cache.t3.micro = $0.017/hora
- **Por qué evitar**: ~$12/mes
- **Alternativa**: Usar **StatefulSet** de Redis en Kubernetes

### 6. ❌ Elastic IP sin asociar
- **Costo**: $0.005/hora por IP no usada
- **Por qué evitar**: Cargos ocultos
- **Alternativa**: Asociar IPs inmediatamente o no crear

### 7. ❌ CloudWatch Logs detallados
- **Costo**: $0.50/GB ingerido
- **Por qué evitar**: Puede acumular costos
- **Alternativa**: Usar `kubectl logs` directamente

---

## ✅ CONFIGURACIÓN ÓPTIMA PARA LEARNER LAB

### Archivo: `k8s/cluster-config-learner-lab.yaml`

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: news2market-cluster
  region: us-east-1  # Región más barata
  version: "1.28"

# NO crear VPC custom, usar la default
# vpc:
#   id: vpc-xxxxxxxx  # La VPC default del Learner Lab

# Nodos workers MÍNIMOS
managedNodeGroups:
  - name: main-nodes
    instanceType: t3.medium  # 🔥 NO usar t3.large
    desiredCapacity: 2       # 🔥 Solo 2 nodos
    minSize: 2
    maxSize: 3               # Máximo 3 (para HPA)
    volumeSize: 20           # 🔥 Solo 20GB por nodo
    privateNetworking: false # 🔥 Usar subnets públicas (evita NAT Gateway)
    labels:
      role: worker
    tags:
      Project: news2market
      Environment: learner-lab
      Cost-Center: education
    # IAM policies mínimas
    iam:
      withAddonPolicies:
        autoScaler: true       # Para HPA
        ebs: true              # Para volumes
        cloudWatch: false      # 🔥 Desactivar CloudWatch logging

# CloudWatch logging DESACTIVADO (ahorra costos)
cloudWatch:
  clusterLogging:
    enableTypes: []  # 🔥 Sin logs

# Addons mínimos
addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
```

---

## 📝 AJUSTES EN LOS MANIFESTS

### 1. Services: Usar NodePort en lugar de LoadBalancer

**❌ NO usar**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  type: LoadBalancer  # ❌ Crea NLB/ALB ($$$)
  ports:
  - port: 80
```

**✅ SÍ usar**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  type: NodePort  # ✅ Gratis, usa puertos de los nodos
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080  # Puerto en el nodo (30000-32767)
```

### 2. ConfigMap: Ajustar para desarrollo

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: news2market-config
  namespace: news2market
data:
  # Usar servicios internos (StatefulSets)
  DATABASE_HOST: postgres-service  # ✅ No RDS
  REDIS_HOST: redis-service        # ✅ No ElastiCache
  
  # Modo mock para datos externos
  USE_MOCK_COLCAP: "true"         # ✅ No llamar APIs externas
  LOG_LEVEL: WARNING               # ✅ Menos logs
```

### 3. Deployments: Recursos mínimos

```yaml
resources:
  requests:
    memory: "256Mi"  # ✅ Reducir de 512Mi
    cpu: "100m"      # ✅ Reducir de 250m
  limits:
    memory: "512Mi"  # ✅ Reducir de 1Gi
    cpu: "250m"      # ✅ Reducir de 500m
```

---

## 🔧 COMANDOS PARA LEARNER LAB

### 1. Iniciar sesión en Learner Lab

1. Ir a: https://awsacademy.instructure.com/
2. Acceder a tu curso
3. Click en "Modules" → "Learner Lab"
4. Click en "Start Lab" (⏱️ Inicia el timer de 4 horas)
5. Esperar a que el círculo esté 🟢 verde
6. Click en "AWS Details" → Copiar credenciales

### 2. Configurar AWS CLI con credenciales temporales

```bash
# Opción 1: Archivo de credenciales
nano ~/.aws/credentials

# Pegar (reemplazar con tus valores del Learner Lab):
[default]
aws_access_key_id = ASIAV...
aws_secret_access_key = abc123...
aws_session_token = IQoJb3JpZ2luX2VjEH...

# Opción 2: Variables de entorno (más rápido)
export AWS_ACCESS_KEY_ID="ASIAV..."
export AWS_SECRET_ACCESS_KEY="abc123..."
export AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEH..."
export AWS_DEFAULT_REGION="us-east-1"

# Verificar
aws sts get-caller-identity
```

**⚠️ IMPORTANTE**: Las credenciales del Learner Lab **caducan después de 4 horas**. Debes copiarlas de nuevo en cada sesión.

### 3. Verificar límites de servicio

```bash
# Ver cuántas instancias EC2 puedes crear
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --region us-east-1

# Ver límite de vCPUs
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --region us-east-1

# Nota: Si el límite es menor a 8 vCPUs, solo podrás crear 2 t3.medium
```

---

## 🚀 FLUJO OPTIMIZADO PARA LEARNER LAB

### Día 1: Preparación (SIN crear cluster aún)

```bash
# 1. Validar localmente con Minikube
./scripts/validate-system.sh
./scripts/prepare-local-manifests.sh
minikube start
# Desplegar y probar en Minikube...

# 2. Build de imágenes (pero NO push aún)
docker build -t news2market/api-gateway:latest ./backend/api-gateway
docker build -t news2market/data-acquisition:latest ./backend/data-acquisition
docker build -t news2market/text-processor:latest ./backend/text-processor
docker build -t news2market/correlation-service:latest ./backend/correlation-service
docker build -t news2market/frontend:latest ./frontend

# Total gastado: $0
```

---

### Día 2-3: Despliegue en AWS (Sesión 1 - 4 horas)

```bash
# 1. Iniciar Learner Lab y configurar CLI
# (Ver sección anterior)

# 2. Push de imágenes a ECR (~30 min)
./scripts/build-and-push.sh

# 3. Crear cluster EKS (~15 min)
eksctl create cluster -f k8s/cluster-config-learner-lab.yaml

# 4. Desplegar aplicación (~10 min)
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-statefulset.yaml
kubectl apply -f k8s/*-deployment.yaml
kubectl apply -f k8s/text-processor-hpa.yaml

# 5. Verificar que todo funciona (~30 min)
kubectl get pods -n news2market
kubectl get hpa -n news2market

# 6. Acceder con NodePort
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
NODE_PORT=$(kubectl get svc api-gateway-service -n news2market -o jsonpath='{.spec.ports[0].nodePort}')
curl http://$NODE_IP:$NODE_PORT/health

# 7. Antes de que termine la sesión (3:50h):
#    - Captura screenshots
#    - Descarga logs
#    - Deja el cluster corriendo

# Total gastado: ~$0.30 (solo 4 horas)
```

---

### Día 4-5: Pruebas de carga (Sesión 2 - 4 horas)

```bash
# 1. Iniciar Learner Lab (renovar credenciales)
# 2. Actualizar kubeconfig
aws eks update-kubeconfig --region us-east-1 --name news2market-cluster

# 3. Verificar que todo sigue funcionando
kubectl get pods -n news2market

# 4. Ejecutar pruebas de escalabilidad
./scripts/load-test.sh

# 5. Capturar evidencias:
#    - kubectl get hpa --watch (durante la carga)
#    - kubectl top pods
#    - Screenshots de AWS Console (EC2, EKS)
#    - Logs de workers

# Total gastado acumulado: ~$2.00
```

---

### Día 6-7: Limpieza y documentación

```bash
# 1. Capturar TODAS las evidencias finales
# 2. Exportar logs y métricas
kubectl logs -n news2market -l app=text-processor > logs.txt
kubectl get hpa -n news2market -o yaml > hpa-final.yaml

# 3. DESTRUIR TODO (IMPORTANTE)
kubectl delete namespace news2market
eksctl delete cluster --name news2market-cluster --region us-east-1

# 4. Verificar que NO quedan recursos
aws ec2 describe-instances
aws ec2 describe-volumes

# 5. Eliminar imágenes de ECR (opcional)
aws ecr delete-repository --repository-name news2market/api-gateway --force
# ... repetir para cada repositorio

# Total gastado final: ~$6-8 USD (muy por debajo del límite)
```

---

## 📊 DEMOSTRACIÓN DE PARALELISMO SIN ALB

### Opción 1: NodePort + IP pública del nodo

```bash
# Obtener IP pública de un nodo
NODE_IP=$(kubectl get nodes -o wide | awk 'NR==2 {print $7}')

# Obtener NodePort del servicio
API_PORT=$(kubectl get svc api-gateway-service -n news2market -o jsonpath='{.spec.ports[0].nodePort}')

# Acceder directamente
curl http://$NODE_IP:$API_PORT/health

# Generar carga para demostrar HPA
for i in {1..100}; do
  curl -X POST http://$NODE_IP:$API_PORT/api/v1/text/process \
    -H "Content-Type: application/json" \
    -d '{"text":"Test"}' &
done
```

### Opción 2: kubectl port-forward (para pruebas locales)

```bash
# Port forward desde tu máquina al cluster
kubectl port-forward -n news2market svc/api-gateway-service 8000:8000 &

# Ahora puedes usar localhost
curl http://localhost:8000/health

# Generar carga
./scripts/load-test.sh  # Este script usa localhost:8000
```

### Opción 3: Exec directo en un pod

```bash
# Entrar a un pod
kubectl exec -it -n news2market $(kubectl get pod -n news2market -l app=api-gateway -o name | head -1) -- bash

# Desde dentro del cluster, los servicios son accesibles por DNS
curl http://text-processor-service:8002/health
```

---

## 🎓 EVIDENCIAS ACADÉMICAS A CAPTURAR

### 1. Arquitectura distribuida

```bash
# Diagrama de la arquitectura
kubectl get all -n news2market -o wide

# Capturar output en un archivo
kubectl get all -n news2market -o wide > arquitectura.txt
```

### 2. Paralelismo

```bash
# Ver múltiples workers procesando simultáneamente
kubectl logs -f -n news2market -l app=text-processor --all-containers --max-log-requests=5

# Distribución de carga
for pod in $(kubectl get pods -n news2market -l app=text-processor -o name); do
  echo "=== $pod ==="
  kubectl logs $pod -n news2market | grep -c "Processing"
done
```

### 3. Escalabilidad (HPA)

```bash
# Capturar HPA escalando
watch -n 5 'kubectl get hpa,pods -n news2market'

# Exportar métricas
kubectl get hpa text-processor-hpa -n news2market -o json > hpa-metrics.json

# Ver eventos de escalado
kubectl describe hpa text-processor-hpa -n news2market
```

### 4. Métricas de recursos

```bash
# CPU y memoria de todos los pods
kubectl top pods -n news2market

# Métricas de nodos
kubectl top nodes

# Ver en dashboard de Kubernetes (opcional)
kubectl proxy &
# Abrir: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

---

## 💡 CONSEJOS FINALES PARA LEARNER LAB

1. **Trabaja en horarios específicos**: El timer de 4h no es pausable. Planifica bien.

2. **Guarda credenciales**: Cópialas a un archivo cada vez que inicies sesión.

3. **Documenta costos**: 
   ```bash
   aws ce get-cost-and-usage \
     --time-period Start=2025-01-01,End=2025-01-31 \
     --granularity DAILY \
     --metrics UnblendedCost
   ```

4. **No dejes correr de noche**: Apaga el cluster si no lo usas.
   ```bash
   # Opción 1: Detener nodos (no funciona en Learner Lab)
   # Opción 2: Reducir replicas a 0
   kubectl scale deployment --all --replicas=0 -n news2market
   
   # Restaurar
   kubectl scale deployment api-gateway --replicas=2 -n news2market
   # ... etc
   ```

5. **Ten un plan B**: Si te quedas sin crédito, usa Minikube para la demo final.

---

## 🆘 TROUBLESHOOTING COMÚN EN LEARNER LAB

### Problema 1: "UnauthorizedOperation" al crear cluster

**Causa**: Credenciales expiradas (4 horas)

**Solución**:
```bash
# Renovar credenciales desde Learner Lab
# Copiar nuevamente a ~/.aws/credentials
aws sts get-caller-identity  # Verificar
```

---

### Problema 2: No puedo crear más de 2 instancias EC2

**Causa**: Límite de vCPUs en Learner Lab

**Solución**:
```yaml
# Usar solo 2 nodos en cluster-config.yaml
managedNodeGroups:
  - name: main-nodes
    desiredCapacity: 2  # ✅ Máximo 2
    maxSize: 2          # ✅ No escalar más
```

---

### Problema 3: Cluster tarda mucho en crear

**Causa**: Normal, toma 15-20 minutos

**Solución**: Paciencia. Mientras tanto, revisar documentación.

---

### Problema 4: "InsufficientFreeAddressesInSubnet"

**Causa**: VPC default llena

**Solución**:
```bash
# Eliminar recursos viejos
aws ec2 describe-instances --filters "Name=instance-state-name,Values=terminated"
aws ec2 terminate-instances --instance-ids i-xxxxx
```

---

**Última actualización**: Diciembre 2025  
**Crédito estimado necesario**: $20-25 USD de $50 USD disponibles  
**Duración recomendada**: 5-7 días de pruebas intermitentes
