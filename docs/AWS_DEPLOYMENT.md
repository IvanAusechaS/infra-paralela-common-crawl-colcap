# ☁️ Guía de Despliegue en AWS - News2Market

## Tabla de Contenidos
- [Prerequisitos](#prerequisitos)
- [Arquitectura en AWS](#arquitectura-en-aws)
- [Configuración Inicial](#configuración-inicial)
- [Creación del Clúster EKS](#creación-del-clúster-eks)
- [Configuración de ECR](#configuración-de-ecr)
- [Build y Push de Imágenes](#build-y-push-de-imágenes)
- [Despliegue en Kubernetes](#despliegue-en-kubernetes)
- [Configuración de Base de Datos](#configuración-de-base-de-datos)
- [Escalado y Monitoreo](#escalado-y-monitoreo)
- [Pruebas de Escalabilidad](#pruebas-de-escalabilidad)
- [Costos Estimados](#costos-estimados)
- [Eliminación de Recursos](#eliminación-de-recursos)

---

## Prerequisitos

### Herramientas Necesarias
- ✅ AWS CLI v2 instalado y configurado
- ✅ kubectl instalado (v1.28+)
- ✅ eksctl instalado
- ✅ Docker instalado y corriendo
- ✅ Cuenta de AWS con permisos de administrador
- ✅ Tarjeta de crédito válida en AWS

### Verificar Instalación
```bash
# Verificar todas las herramientas
aws --version
kubectl version --client
eksctl version
docker --version

# Verificar credenciales de AWS
aws sts get-caller-identity
```

**Salida esperada**:
```json
{
    "UserId": "AIDAXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/tu-usuario"
}
```

---

## Arquitectura en AWS

### Componentes de Infraestructura

```
┌────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD                              │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    VPC (10.0.0.0/16)                     │ │
│  │                                                          │ │
│  │  ┌─────────────────┐         ┌─────────────────┐       │ │
│  │  │  Public Subnet  │         │  Public Subnet  │       │ │
│  │  │  10.0.1.0/24    │         │  10.0.2.0/24    │       │ │
│  │  │  (AZ us-east-1a)│         │  (AZ us-east-1b)│       │ │
│  │  └────────┬────────┘         └────────┬────────┘       │ │
│  │           │                           │                │ │
│  │  ┌────────▼──────────────────────────▼────────┐       │ │
│  │  │          Load Balancer (ALB)               │       │ │
│  │  └────────┬──────────────────────────┬────────┘       │ │
│  │           │                           │                │ │
│  │  ┌────────▼────────┐       ┌────────▼────────┐       │ │
│  │  │  EKS Node       │       │  EKS Node       │       │ │
│  │  │  t3.medium      │       │  t3.medium      │       │ │
│  │  │  (Worker Node 1)│       │  (Worker Node 2)│       │ │
│  │  │                 │       │                 │       │ │
│  │  │  ┌──────────┐   │       │  ┌──────────┐   │       │ │
│  │  │  │API Gateway│   │       │  │Text Proc│   │       │ │
│  │  │  │   Pod    │   │       │  │  Worker │   │       │ │
│  │  │  └──────────┘   │       │  └──────────┘   │       │ │
│  │  │  ┌──────────┐   │       │  ┌──────────┐   │       │ │
│  │  │  │Data Acq. │   │       │  │Text Proc│   │       │ │
│  │  │  │   Pod    │   │       │  │  Worker │   │       │ │
│  │  │  └──────────┘   │       │  └──────────┘   │       │ │
│  │  └─────────────────┘       └─────────────────┘       │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────┐    │ │
│  │  │     Private Subnet (10.0.3.0/24)            │    │ │
│  │  │  ┌────────────┐       ┌──────────────┐      │    │ │
│  │  │  │ RDS        │       │  ElastiCache │      │    │ │
│  │  │  │ PostgreSQL │       │  Redis       │      │    │ │
│  │  │  └────────────┘       └──────────────┘      │    │ │
│  │  └──────────────────────────────────────────────┘    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌────────────────────┐    ┌────────────────────┐        │
│  │       ECR          │    │        S3          │        │
│  │  (Docker Images)   │    │  (Logs, Backups)   │        │
│  └────────────────────┘    └────────────────────┘        │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │              CloudWatch                            │  │
│  │        (Logs, Metrics, Dashboards)                 │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### Servicios AWS Utilizados

| Servicio | Propósito | Costo Aproximado |
|----------|-----------|------------------|
| **EKS** | Orquestación de contenedores | $0.10/hora (~$73/mes) |
| **EC2** | Nodos del clúster (2x t3.medium) | $0.0416/hora c/u (~$60/mes) |
| **ECR** | Registro de imágenes Docker | $0.10/GB/mes |
| **RDS** | Base de datos PostgreSQL | $0.017/hora (~$12/mes) |
| **ElastiCache** | Redis para colas | $0.017/hora (~$12/mes) |
| **ALB** | Load Balancer | $0.0225/hora (~$16/mes) |
| **CloudWatch** | Logs y métricas | ~$5/mes |
| **S3** | Almacenamiento opcional | $0.023/GB/mes |

**Total estimado**: ~$180-200/mes (ambiente de desarrollo)

---

## Configuración Inicial

### 1. Configurar AWS CLI

```bash
# Configurar credenciales
aws configure

# Se solicitará:
# AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name: us-east-1
# Default output format: json
```

**Obtener credenciales**:
1. Ir a AWS Console → IAM → Users
2. Seleccionar tu usuario
3. Security credentials → Create access key
4. Guardar Access Key ID y Secret Access Key

### 2. Configurar Variables de Entorno

```bash
# Crear archivo de variables para el proyecto
cat > aws-config.sh << 'EOF'
# Configuración del proyecto
export AWS_REGION="us-east-1"
export CLUSTER_NAME="news2market-cluster"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
export PROJECT_NAME="news2market"

# Tags para recursos
export TAG_PROJECT="News2Market"
export TAG_ENVIRONMENT="production"
export TAG_OWNER="tu-nombre"

echo "✅ Variables configuradas:"
echo "  Region: $AWS_REGION"
echo "  Cluster: $CLUSTER_NAME"
echo "  Account ID: $AWS_ACCOUNT_ID"
echo "  ECR Registry: $ECR_REGISTRY"
EOF

# Cargar variables
source aws-config.sh
```

### 3. Crear Rol IAM para EKS

```bash
# Crear rol para EKS cluster
aws iam create-role \
  --role-name ${CLUSTER_NAME}-cluster-role \
  --assume-role-policy-document file://eks-cluster-role-trust-policy.json

# Adjuntar políticas necesarias
aws iam attach-role-policy \
  --role-name ${CLUSTER_NAME}-cluster-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Crear rol para nodos
aws iam create-role \
  --role-name ${CLUSTER_NAME}-node-role \
  --assume-role-policy-document file://eks-node-role-trust-policy.json

# Adjuntar políticas para nodos
aws iam attach-role-policy \
  --role-name ${CLUSTER_NAME}-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

aws iam attach-role-policy \
  --role-name ${CLUSTER_NAME}-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

aws iam attach-role-policy \
  --role-name ${CLUSTER_NAME}-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
```

---

## Creación del Clúster EKS

### Opción 1: Con eksctl (Recomendado - Más Fácil)

```bash
# Crear archivo de configuración del clúster
cat > cluster-config.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: ${CLUSTER_NAME}
  region: ${AWS_REGION}
  version: "1.28"
  tags:
    Project: ${TAG_PROJECT}
    Environment: ${TAG_ENVIRONMENT}
    Owner: ${TAG_OWNER}

# VPC Configuration
vpc:
  cidr: 10.0.0.0/16
  nat:
    gateway: Single

# Nodos del clúster
managedNodeGroups:
  - name: news2market-workers
    instanceType: t3.medium
    minSize: 2
    maxSize: 5
    desiredCapacity: 2
    volumeSize: 20
    volumeType: gp3
    labels:
      role: worker
      environment: production
    tags:
      Project: ${TAG_PROJECT}
      NodeGroup: workers
    ssh:
      allow: false
    iam:
      withAddonPolicies:
        autoScaler: true
        cloudWatch: true
        ebs: true
        efs: true

# Addons
addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest

# CloudWatch Logging
cloudWatch:
  clusterLogging:
    enableTypes:
      - api
      - audit
      - authenticator
      - controllerManager
      - scheduler
EOF

# Crear el clúster (toma ~15-20 minutos)
eksctl create cluster -f cluster-config.yaml

# Verificar creación
eksctl get cluster --name ${CLUSTER_NAME} --region ${AWS_REGION}
```

### Opción 2: Con AWS CLI (Manual)

```bash
# 1. Crear VPC para el clúster
aws cloudformation create-stack \
  --stack-name ${CLUSTER_NAME}-vpc \
  --template-url https://amazon-eks.s3.us-west-2.amazonaws.com/cloudformation/2020-10-29/amazon-eks-vpc-private-subnets.yaml \
  --region ${AWS_REGION}

# Esperar a que se complete
aws cloudformation wait stack-create-complete \
  --stack-name ${CLUSTER_NAME}-vpc \
  --region ${AWS_REGION}

# 2. Obtener IDs de subnets y security groups
VPC_ID=$(aws cloudformation describe-stacks \
  --stack-name ${CLUSTER_NAME}-vpc \
  --query 'Stacks[0].Outputs[?OutputKey==`VpcId`].OutputValue' \
  --output text)

SUBNET_IDS=$(aws cloudformation describe-stacks \
  --stack-name ${CLUSTER_NAME}-vpc \
  --query 'Stacks[0].Outputs[?OutputKey==`SubnetIds`].OutputValue' \
  --output text)

SECURITY_GROUP=$(aws cloudformation describe-stacks \
  --stack-name ${CLUSTER_NAME}-vpc \
  --query 'Stacks[0].Outputs[?OutputKey==`SecurityGroups`].OutputValue' \
  --output text)

# 3. Crear clúster EKS
aws eks create-cluster \
  --name ${CLUSTER_NAME} \
  --role-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/${CLUSTER_NAME}-cluster-role \
  --resources-vpc-config subnetIds=${SUBNET_IDS},securityGroupIds=${SECURITY_GROUP} \
  --region ${AWS_REGION}

# Esperar a que esté activo (~10 minutos)
aws eks wait cluster-active \
  --name ${CLUSTER_NAME} \
  --region ${AWS_REGION}

# 4. Crear node group
aws eks create-nodegroup \
  --cluster-name ${CLUSTER_NAME} \
  --nodegroup-name ${CLUSTER_NAME}-workers \
  --node-role arn:aws:iam::${AWS_ACCOUNT_ID}:role/${CLUSTER_NAME}-node-role \
  --subnets $(echo $SUBNET_IDS | tr ',' ' ') \
  --instance-types t3.medium \
  --scaling-config minSize=2,maxSize=5,desiredSize=2 \
  --region ${AWS_REGION}
```

### Configurar kubectl

```bash
# Actualizar kubeconfig para conectarse al clúster
aws eks update-kubeconfig \
  --name ${CLUSTER_NAME} \
  --region ${AWS_REGION}

# Verificar conexión
kubectl cluster-info
kubectl get nodes

# Deberías ver algo como:
# NAME                         STATUS   ROLES    AGE   VERSION
# ip-10-0-1-123.ec2.internal   Ready    <none>   5m    v1.28.0
# ip-10-0-2-456.ec2.internal   Ready    <none>   5m    v1.28.0
```

---

## Configuración de ECR

### 1. Crear Repositorios en ECR

```bash
# Función para crear repositorio
create_ecr_repo() {
  local repo_name=$1
  echo "📦 Creando repositorio: $repo_name"
  
  aws ecr create-repository \
    --repository-name ${PROJECT_NAME}/${repo_name} \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true \
    --tags Key=Project,Value=${TAG_PROJECT} \
    2>/dev/null || echo "  ℹ️  Repositorio ya existe"
}

# Crear repositorios para cada servicio
create_ecr_repo "api-gateway"
create_ecr_repo "data-acquisition"
create_ecr_repo "text-processor"
create_ecr_repo "correlation-service"
create_ecr_repo "frontend"

# Listar repositorios creados
aws ecr describe-repositories \
  --region ${AWS_REGION} \
  --query 'repositories[?starts_with(repositoryName, `'${PROJECT_NAME}'`)].repositoryUri' \
  --output table
```

### 2. Configurar Política de Ciclo de Vida

```bash
# Crear política para limpiar imágenes antiguas
cat > ecr-lifecycle-policy.json << 'EOF'
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF

# Aplicar a cada repositorio
for repo in api-gateway data-acquisition text-processor correlation-service frontend; do
  aws ecr put-lifecycle-policy \
    --repository-name ${PROJECT_NAME}/${repo} \
    --lifecycle-policy-text file://ecr-lifecycle-policy.json \
    --region ${AWS_REGION}
done
```

---

## Build y Push de Imágenes

### Script Automatizado

Crear script `scripts/build-and-push.sh`:

```bash
#!/bin/bash
set -e

# Cargar configuración
source aws-config.sh

# Autenticar Docker con ECR
echo "🔐 Autenticando con ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Función para build y push
build_and_push() {
  local service=$1
  local dockerfile_path=$2
  local context_path=$3
  
  echo ""
  echo "🔨 Building ${service}..."
  
  # Build
  docker build \
    -t ${PROJECT_NAME}/${service}:latest \
    -t ${ECR_REGISTRY}/${PROJECT_NAME}/${service}:latest \
    -t ${ECR_REGISTRY}/${PROJECT_NAME}/${service}:$(date +%Y%m%d-%H%M%S) \
    -f ${dockerfile_path} \
    ${context_path}
  
  echo "📤 Pushing ${service} to ECR..."
  
  # Push latest
  docker push ${ECR_REGISTRY}/${PROJECT_NAME}/${service}:latest
  
  # Push timestamped
  docker push ${ECR_REGISTRY}/${PROJECT_NAME}/${service}:$(date +%Y%m%d-%H%M%S)
  
  echo "✅ ${service} pushed successfully"
}

# Build y push cada servicio
build_and_push "api-gateway" "./backend/api-gateway/Dockerfile" "./backend/api-gateway"
build_and_push "data-acquisition" "./backend/data-acquisition/Dockerfile" "./backend/data-acquisition"
build_and_push "text-processor" "./backend/text-processor/Dockerfile" "./backend/text-processor"
build_and_push "correlation-service" "./backend/correlation-service/Dockerfile" "./backend/correlation-service"

# Frontend (con build de producción)
echo ""
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

build_and_push "frontend" "./frontend/Dockerfile" "./frontend"

echo ""
echo "🎉 Todas las imágenes construidas y subidas exitosamente!"
echo ""
echo "📋 Imágenes disponibles:"
aws ecr list-images \
  --repository-name ${PROJECT_NAME}/api-gateway \
  --region ${AWS_REGION} \
  --query 'imageIds[*].imageTag' \
  --output table
```

```bash
# Hacer ejecutable
chmod +x scripts/build-and-push.sh

# Ejecutar
./scripts/build-and-push.sh
```

### Build Manual (individual)

```bash
# 1. Autenticar con ECR
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# 2. Build API Gateway
cd backend/api-gateway
docker build -t ${ECR_REGISTRY}/${PROJECT_NAME}/api-gateway:latest .
docker push ${ECR_REGISTRY}/${PROJECT_NAME}/api-gateway:latest
cd ../..

# 3. Build Data Acquisition
cd backend/data-acquisition
docker build -t ${ECR_REGISTRY}/${PROJECT_NAME}/data-acquisition:latest .
docker push ${ECR_REGISTRY}/${PROJECT_NAME}/data-acquisition:latest
cd ../..

# 4. Build Text Processor
cd backend/text-processor
docker build -t ${ECR_REGISTRY}/${PROJECT_NAME}/text-processor:latest .
docker push ${ECR_REGISTRY}/${PROJECT_NAME}/text-processor:latest
cd ../..

# 5. Build Correlation Service
cd backend/correlation-service
docker build -t ${ECR_REGISTRY}/${PROJECT_NAME}/correlation-service:latest .
docker push ${ECR_REGISTRY}/${PROJECT_NAME}/correlation-service:latest
cd ../..

# 6. Build Frontend
cd frontend
npm run build
docker build -t ${ECR_REGISTRY}/${PROJECT_NAME}/frontend:latest .
docker push ${ECR_REGISTRY}/${PROJECT_NAME}/frontend:latest
cd ..
```

---

## Despliegue en Kubernetes

### 1. Crear Namespace

```bash
# Crear namespace para el proyecto
kubectl create namespace news2market

# Establecer como namespace por defecto
kubectl config set-context --current --namespace=news2market
```

### 2. Crear Secrets

```bash
# Secrets para base de datos
kubectl create secret generic postgres-secret \
  --from-literal=username=news2market_user \
  --from-literal=password=$(openssl rand -base64 32) \
  --from-literal=database=newsdb \
  -n news2market

# Secrets para Redis
kubectl create secret generic redis-secret \
  --from-literal=password=$(openssl rand -base64 32) \
  -n news2market

# Secrets para AWS (si se necesita acceso a S3)
kubectl create secret generic aws-secret \
  --from-literal=access-key-id=${AWS_ACCESS_KEY_ID} \
  --from-literal=secret-access-key=${AWS_SECRET_ACCESS_KEY} \
  -n news2market

# Verificar secrets
kubectl get secrets -n news2market
```

### 3. Desplegar PostgreSQL

```bash
# Aplicar manifiestos
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

# Esperar a que esté listo
kubectl wait --for=condition=ready pod -l app=postgres -n news2market --timeout=300s

# Verificar
kubectl get pods -l app=postgres -n news2market
kubectl logs -l app=postgres -n news2market --tail=50
```

### 4. Desplegar Redis

```bash
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# Esperar
kubectl wait --for=condition=ready pod -l app=redis -n news2market --timeout=300s
```

### 5. Desplegar Servicios Backend

```bash
# ConfigMap con variables de entorno
kubectl apply -f k8s/configmap.yaml

# API Gateway
kubectl apply -f k8s/api-gateway-deployment.yaml
kubectl apply -f k8s/api-gateway-service.yaml

# Data Acquisition
kubectl apply -f k8s/data-acquisition-deployment.yaml
kubectl apply -f k8s/data-acquisition-service.yaml

# Text Processor (workers escalables)
kubectl apply -f k8s/text-processor-deployment.yaml
kubectl apply -f k8s/text-processor-service.yaml
kubectl apply -f k8s/text-processor-hpa.yaml

# Correlation Service
kubectl apply -f k8s/correlation-service-deployment.yaml
kubectl apply -f k8s/correlation-service-service.yaml

# Verificar deployments
kubectl get deployments -n news2market
kubectl get pods -n news2market -o wide
```

### 6. Desplegar Frontend

```bash
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# Esperar a que estén todos listos
kubectl wait --for=condition=ready pod --all -n news2market --timeout=600s
```

### 7. Configurar Ingress/Load Balancer

```bash
# Instalar AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

eksctl create iamserviceaccount \
  --cluster=${CLUSTER_NAME} \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Aplicar ingress
kubectl apply -f k8s/ingress.yaml

# Obtener URL del Load Balancer
kubectl get ingress -n news2market

# Esperar a que se asigne el DNS
sleep 60
LOADBALANCER_URL=$(kubectl get ingress news2market-ingress -n news2market -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo ""
echo "🎉 Aplicación desplegada!"
echo "🌐 Frontend: http://${LOADBALANCER_URL}"
echo "📡 API: http://${LOADBALANCER_URL}/api"
echo "📚 Docs: http://${LOADBALANCER_URL}/api/docs"
```

---

## Configuración de Base de Datos

### Inicializar Schema

```bash
# Obtener nombre del pod de PostgreSQL
POSTGRES_POD=$(kubectl get pods -n news2market -l app=postgres -o jsonpath='{.items[0].metadata.name}')

# Copiar script de inicialización
kubectl cp backend/init-db.sql ${POSTGRES_POD}:/tmp/init-db.sql -n news2market

# Ejecutar script
kubectl exec -it ${POSTGRES_POD} -n news2market -- psql -U news2market_user -d newsdb -f /tmp/init-db.sql

# Verificar tablas
kubectl exec -it ${POSTGRES_POD} -n news2market -- psql -U news2market_user -d newsdb -c "\dt"
```

---

## Escalado y Monitoreo

### Escalar Workers Manualmente

```bash
# Escalar text processors a 5 réplicas
kubectl scale deployment text-processor --replicas=5 -n news2market

# Verificar escalado
kubectl get pods -l app=text-processor -n news2market

# Ver uso de recursos
kubectl top pods -n news2market
kubectl top nodes
```

### Configurar Auto-Scaling

```bash
# HPA ya aplicado, verificar estado
kubectl get hpa -n news2market

# Ver eventos de escalado
kubectl describe hpa text-processor-hpa -n news2market

# Metrics server (si no está instalado)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### CloudWatch Logs

```bash
# Instalar Fluent Bit para logs
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml

# Ver logs en CloudWatch
aws logs tail /aws/eks/${CLUSTER_NAME}/cluster --follow
```

### Crear Dashboard en CloudWatch

```bash
# Script para crear dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ${CLUSTER_NAME}-metrics \
  --dashboard-body file://cloudwatch-dashboard.json
```

---

## Pruebas de Escalabilidad

### Script de Prueba de Carga

Crear `scripts/load-test.sh`:

```bash
#!/bin/bash

API_URL="http://your-loadbalancer-url/api"

echo "🧪 Iniciando pruebas de escalabilidad..."

# Test con 1 worker
echo ""
echo "📊 Test 1: 1 worker"
kubectl scale deployment text-processor --replicas=1 -n news2market
sleep 30

START=$(date +%s)
curl -X POST ${API_URL}/start-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "limit": 1000
  }'
END=$(date +%s)
TIME_1_WORKER=$((END - START))
echo "Tiempo con 1 worker: ${TIME_1_WORKER}s"

# Test con 3 workers
echo ""
echo "📊 Test 2: 3 workers"
kubectl scale deployment text-processor --replicas=3 -n news2market
sleep 30

START=$(date +%s)
curl -X POST ${API_URL}/start-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "limit": 1000
  }'
END=$(date +%s)
TIME_3_WORKERS=$((END - START))
echo "Tiempo con 3 workers: ${TIME_3_WORKERS}s"

# Test con 5 workers
echo ""
echo "📊 Test 3: 5 workers"
kubectl scale deployment text-processor --replicas=5 -n news2market
sleep 30

START=$(date +%s)
curl -X POST ${API_URL}/start-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "limit": 1000
  }'
END=$(date +%s)
TIME_5_WORKERS=$((END - START))
echo "Tiempo con 5 workers: ${TIME_5_WORKERS}s"

# Resultados
echo ""
echo "═══════════════════════════════════════"
echo "📈 RESULTADOS DE ESCALABILIDAD"
echo "═══════════════════════════════════════"
echo "1 worker:  ${TIME_1_WORKER}s"
echo "3 workers: ${TIME_3_WORKERS}s ($(echo "scale=2; ${TIME_1_WORKER}/${TIME_3_WORKERS}" | bc)x más rápido)"
echo "5 workers: ${TIME_5_WORKERS}s ($(echo "scale=2; ${TIME_1_WORKER}/${TIME_5_WORKERS}" | bc)x más rápido)"
echo "═══════════════════════════════════════"
```

---

## Costos Estimados

### Calculadora de Costos

| Recurso | Tipo | Cantidad | Costo/hora | Costo/mes |
|---------|------|----------|------------|-----------|
| EKS Cluster | - | 1 | $0.10 | $73 |
| EC2 Nodes | t3.medium | 2 | $0.0416 x 2 | $60 |
| RDS PostgreSQL | db.t3.micro | 1 | $0.017 | $12 |
| ElastiCache Redis | cache.t3.micro | 1 | $0.017 | $12 |
| ALB | - | 1 | $0.0225 | $16 |
| ECR | Storage | 10 GB | - | $1 |
| CloudWatch | Logs | - | - | $5 |
| **TOTAL** | | | | **~$179/mes** |

### Optimización de Costos

**Para ambiente de desarrollo/pruebas**:
- Usar nodos Spot instances (hasta 70% de descuento)
- Detener el clúster fuera de horario de trabajo
- Usar t3.small en lugar de t3.medium

**Script para detener clúster**:
```bash
# Reducir nodos a 0 (fuera de horario)
eksctl scale nodegroup --cluster=${CLUSTER_NAME} --name=news2market-workers --nodes=0

# Restaurar
eksctl scale nodegroup --cluster=${CLUSTER_NAME} --name=news2market-workers --nodes=2
```

---

## Eliminación de Recursos

### ⚠️ IMPORTANTE: Limpiar Todo al Terminar

```bash
# Script de limpieza completa
cat > scripts/cleanup-aws.sh << 'EOF'
#!/bin/bash
set -e

source aws-config.sh

echo "⚠️  ADVERTENCIA: Esto eliminará TODOS los recursos del proyecto"
echo "Cluster: ${CLUSTER_NAME}"
echo "Region: ${AWS_REGION}"
read -p "¿Continuar? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Cancelado"
  exit 0
fi

echo ""
echo "🗑️  Eliminando recursos..."

# 1. Eliminar servicios LoadBalancer primero
echo "1/6 Eliminando servicios con LoadBalancer..."
kubectl delete svc -n news2market --all --timeout=120s

# 2. Eliminar todos los recursos de Kubernetes
echo "2/6 Eliminando recursos de Kubernetes..."
kubectl delete namespace news2market --timeout=180s

# 3. Eliminar clúster EKS
echo "3/6 Eliminando clúster EKS (esto toma ~10 minutos)..."
eksctl delete cluster --name ${CLUSTER_NAME} --region ${AWS_REGION} --wait

# 4. Eliminar imágenes en ECR
echo "4/6 Eliminando imágenes en ECR..."
for repo in api-gateway data-acquisition text-processor correlation-service frontend; do
  aws ecr delete-repository \
    --repository-name ${PROJECT_NAME}/${repo} \
    --force \
    --region ${AWS_REGION} 2>/dev/null || true
done

# 5. Eliminar roles IAM
echo "5/6 Eliminando roles IAM..."
aws iam detach-role-policy \
  --role-name ${CLUSTER_NAME}-cluster-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy 2>/dev/null || true
aws iam delete-role --role-name ${CLUSTER_NAME}-cluster-role 2>/dev/null || true

aws iam detach-role-policy \
  --role-name ${CLUSTER_NAME}-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy 2>/dev/null || true
aws iam detach-role-policy \
  --role-name ${CLUSTER_NAME}-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly 2>/dev/null || true
aws iam detach-role-policy \
  --role-name ${CLUSTER_NAME}-node-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy 2>/dev/null || true
aws iam delete-role --role-name ${CLUSTER_NAME}-node-role 2>/dev/null || true

# 6. Verificar costos restantes
echo "6/6 Verificando recursos restantes..."
echo ""
echo "✅ Limpieza completada"
echo ""
echo "📋 Verificar manualmente en AWS Console:"
echo "  - EC2 → Load Balancers"
echo "  - EC2 → Security Groups"
echo "  - CloudWatch → Log Groups"
echo "  - S3 → Buckets"
echo ""
echo "💰 Para verificar costos: https://console.aws.amazon.com/billing/"
EOF

chmod +x scripts/cleanup-aws.sh

# Ejecutar limpieza
./scripts/cleanup-aws.sh
```

### Verificar Eliminación

```bash
# Verificar que no quedan recursos
aws eks list-clusters --region ${AWS_REGION}
aws ec2 describe-instances --region ${AWS_REGION} --filters "Name=tag:Project,Values=${TAG_PROJECT}"
aws ecr describe-repositories --region ${AWS_REGION}
aws elb describe-load-balancers --region ${AWS_REGION}

# Si encuentras recursos huérfanos, eliminar manualmente
```

---

## Troubleshooting

### Problema: Pods no inician

```bash
# Ver eventos
kubectl describe pod <pod-name> -n news2market

# Ver logs
kubectl logs <pod-name> -n news2market

# Problemas comunes:
# - ImagePullBackOff: Verificar que las imágenes existen en ECR
# - CrashLoopBackOff: Ver logs de aplicación
# - Pending: Verificar recursos del nodo
```

### Problema: No se puede conectar a la base de datos

```bash
# Verificar que PostgreSQL está corriendo
kubectl get pods -l app=postgres -n news2market

# Probar conexión desde otro pod
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h postgres-service -U news2market_user -d newsdb

# Verificar secret
kubectl get secret postgres-secret -n news2market -o yaml
```

### Problema: Load Balancer no se crea

```bash
# Verificar AWS Load Balancer Controller
kubectl get pods -n kube-system | grep aws-load-balancer-controller

# Ver logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Verificar IAM roles
aws iam get-role --role-name AmazonEKSLoadBalancerControllerRole
```

---

## Recursos Adicionales

### Comandos Útiles

```bash
# Ver todos los recursos
kubectl get all -n news2market

# Ver uso de recursos en tiempo real
kubectl top pods -n news2market --watch

# Port-forward para debugging
kubectl port-forward svc/api-gateway 8000:8000 -n news2market

# Ejecutar shell en pod
kubectl exec -it <pod-name> -n news2market -- /bin/bash

# Ver logs de múltiples pods
kubectl logs -f -l app=text-processor -n news2market --max-log-requests=10

# Reiniciar deployment
kubectl rollout restart deployment/text-processor -n news2market

# Ver historial de cambios
kubectl rollout history deployment/text-processor -n news2market

# Rollback
kubectl rollout undo deployment/text-processor -n news2market
```

### Enlaces Útiles

- [Documentación AWS EKS](https://docs.aws.amazon.com/eks/)
- [Documentación eksctl](https://eksctl.io/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Calculadora de costos AWS](https://calculator.aws/)
- [AWS Free Tier](https://aws.amazon.com/free/)

---

**Última actualización**: Diciembre 2024  
**Versión**: 1.0.0  
**Autor**: Equipo News2Market

**⚠️ Recordatorio**: Siempre eliminar recursos de AWS cuando no se estén usando para evitar cargos inesperados.
