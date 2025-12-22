# Guía de Despliegue en AWS EKS

## Índice
1. [Pre-requisitos](#pre-requisitos)
2. [Configuración de AWS](#configuración-de-aws)
3. [Creación del cluster EKS](#creación-del-cluster-eks)
4. [Configuración de servicios administrados](#configuración-de-servicios-administrados)
5. [Construcción y publicación de imágenes Docker](#construcción-y-publicación-de-imágenes-docker)
6. [Despliegue de aplicaciones](#despliegue-de-aplicaciones)
7. [Configuración de autoescalado](#configuración-de-autoescalado)
8. [Monitoreo y logs](#monitoreo-y-logs)
9. [Optimización de costos](#optimización-de-costos)
10. [Troubleshooting](#troubleshooting)

---

## Pre-requisitos

### Software requerido

Instalar las siguientes herramientas en tu máquina local:

#### 1. AWS CLI v2
```bash
# Windows (PowerShell como administrador)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# macOS
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verificar instalación
aws --version  # Debe mostrar aws-cli/2.x.x
```

#### 2. kubectl
```bash
# Windows (con chocolatey)
choco install kubernetes-cli

# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verificar instalación
kubectl version --client
```

#### 3. eksctl
```bash
# Windows (con chocolatey)
choco install eksctl

# macOS
brew tap weaveworks/tap
brew install weaveworks/tap/eksctl

# Linux
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Verificar instalación
eksctl version
```

#### 4. Docker Desktop
```bash
# Descargar desde: https://www.docker.com/products/docker-desktop/
# Verificar instalación
docker --version
docker-compose --version
```

#### 5. Helm (opcional, para charts avanzados)
```bash
# Windows
choco install kubernetes-helm

# macOS
brew install helm

# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verificar instalación
helm version
```

### Cuenta AWS

Requisitos mínimos:
- Cuenta AWS con permisos de administrador (o permisos específicos para EKS, EC2, VPC, IAM, ECR, RDS, ElastiCache)
- Tarjeta de crédito válida
- Verificación de identidad completada
- Límite de servicio suficiente para instancias EC2 (al menos 10 vCPUs en la región seleccionada)

---

## Configuración de AWS

### 1. Configurar credenciales AWS CLI

```bash
# Crear usuario IAM con permisos necesarios
# En AWS Console → IAM → Users → Add User
# Adjuntar políticas:
# - AmazonEKSClusterPolicy
# - AmazonEKSServicePolicy
# - AmazonEC2ContainerRegistryFullAccess
# - AmazonRDSFullAccess
# - AmazonElastiCacheFullAccess

# Configurar AWS CLI con las credenciales
aws configure

# Ingresar:
# AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name: us-east-1
# Default output format: json

# Verificar configuración
aws sts get-caller-identity
```

Output esperado:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/news2market-admin"
}
```

### 2. Seleccionar región AWS

Recomendaciones por latencia desde Colombia:

| Región | Latencia aproximada | Costo relativo |
|--------|---------------------|----------------|
| **us-east-1** (N. Virginia) | ~70ms | Bajo |
| **us-east-2** (Ohio) | ~85ms | Bajo |
| **sa-east-1** (São Paulo) | ~60ms | **Alto (+30%)** |

**Recomendación**: `us-east-1` (mejor balance costo/latencia)

```bash
# Configurar región por defecto
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1

# Agregar a ~/.bashrc o ~/.zshrc para persistencia
echo 'export AWS_REGION=us-east-1' >> ~/.bashrc
```

---

## Creación del cluster EKS

### Opción 1: Con archivo de configuración (Recomendado)

El archivo `k8s/cluster-config.yaml` ya contiene la configuración óptima:

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: news2market-cluster
  region: us-east-1
  version: "1.28"

# VPC networking
vpc:
  cidr: 10.0.0.0/16
  nat:
    gateway: Single  # Reducir costo (usa 1 NAT Gateway en lugar de 3)

# Managed node group
managedNodeGroups:
  - name: news2market-workers
    instanceType: t3.medium  # 2 vCPU, 4 GiB RAM
    desiredCapacity: 3
    minSize: 2
    maxSize: 10
    volumeSize: 30  # GB EBS volume
    volumeType: gp3
    iam:
      withAddonPolicies:
        imageBuilder: true
        autoScaler: true
        externalDNS: true
        certManager: true
        albIngress: true
        ebs: true
    tags:
      nodegroup-name: news2market-workers
      Environment: production
    labels:
      role: worker
      app: news2market

# CloudWatch logging
cloudWatch:
  clusterLogging:
    enableTypes:
      - api
      - audit
      - authenticator
```

**Crear el cluster**:
```bash
cd k8s/
eksctl create cluster -f cluster-config.yaml
```

Tiempo estimado: **15-20 minutos**

### Opción 2: Con comando directo

```bash
eksctl create cluster \
  --name news2market-cluster \
  --region us-east-1 \
  --version 1.28 \
  --nodegroup-name news2market-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --managed
```

### Verificar creación del cluster

```bash
# Ver clusters EKS
aws eks list-clusters --region us-east-1

# Configurar kubectl para usar el cluster
aws eks update-kubeconfig --region us-east-1 --name news2market-cluster

# Verificar conectividad
kubectl get nodes

# Output esperado:
# NAME                            STATUS   ROLES    AGE   VERSION
# ip-10-0-1-123.ec2.internal      Ready    <none>   5m    v1.28.x
# ip-10-0-2-234.ec2.internal      Ready    <none>   5m    v1.28.x
# ip-10-0-3-345.ec2.internal      Ready    <none>   5m    v1.28.x

# Ver recursos del cluster
kubectl get all --all-namespaces
```

---

## Configuración de servicios administrados

### 1. Amazon RDS para PostgreSQL

#### Crear subnet group
```bash
# Obtener VPC ID y subnet IDs del cluster EKS
VPC_ID=$(aws eks describe-cluster --name news2market-cluster --query "cluster.resourcesVpcConfig.vpcId" --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[?MapPublicIpOnLaunch==\`false\`].SubnetId" --output text)

# Crear DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name news2market-db-subnet \
  --db-subnet-group-description "Subnet group for News2Market RDS" \
  --subnet-ids $SUBNET_IDS \
  --tags "Key=Project,Value=News2Market"
```

#### Crear security group para RDS
```bash
# Crear security group
RDS_SG_ID=$(aws ec2 create-security-group \
  --group-name news2market-rds-sg \
  --description "Security group for News2Market RDS" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

# Permitir tráfico PostgreSQL desde nodes del EKS
NODE_SG_ID=$(aws eks describe-cluster --name news2market-cluster --query "cluster.resourcesVpcConfig.clusterSecurityGroupId" --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $NODE_SG_ID
```

#### Crear instancia RDS PostgreSQL
```bash
aws rds create-db-instance \
  --db-instance-identifier news2market-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.5 \
  --master-username news2market_admin \
  --master-user-password 'ChangeMeToSecurePassword123!' \
  --allocated-storage 50 \
  --storage-type gp3 \
  --iops 3000 \
  --db-subnet-group-name news2market-db-subnet \
  --vpc-security-group-ids $RDS_SG_ID \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00" \
  --multi-az \
  --publicly-accessible false \
  --storage-encrypted \
  --tags "Key=Project,Value=News2Market"
```

Tiempo de creación: **10-15 minutos**

#### Obtener endpoint de RDS
```bash
# Esperar a que esté disponible
aws rds wait db-instance-available --db-instance-identifier news2market-postgres

# Obtener endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier news2market-postgres \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"
# Ejemplo: news2market-postgres.c9akciq32.us-east-1.rds.amazonaws.com
```

#### Crear base de datos y tablas
```bash
# Desde un pod temporal en el cluster
kubectl run postgres-client --rm -it --image=postgres:15 -- psql \
  "postgresql://news2market_admin:ChangeMeToSecurePassword123!@$RDS_ENDPOINT:5432/postgres"

# Una vez conectado, ejecutar:
CREATE DATABASE news2market;
\c news2market;

-- Copiar y pegar todo el schema de backend/init-db.sql
```

### 2. Amazon ElastiCache para Redis

#### Crear subnet group para ElastiCache
```bash
ELASTICACHE_SUBNET_IDS=$(echo $SUBNET_IDS | tr '\t' ',')

aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name news2market-redis-subnet \
  --cache-subnet-group-description "Subnet group for News2Market Redis" \
  --subnet-ids $(echo $SUBNET_IDS | tr '\t' ' ')
```

#### Crear security group para Redis
```bash
REDIS_SG_ID=$(aws ec2 create-security-group \
  --group-name news2market-redis-sg \
  --description "Security group for News2Market Redis" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG_ID \
  --protocol tcp \
  --port 6379 \
  --source-group $NODE_SG_ID
```

#### Crear cluster Redis
```bash
aws elasticache create-replication-group \
  --replication-group-id news2market-redis \
  --replication-group-description "Redis cluster for News2Market" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.medium \
  --num-cache-clusters 2 \
  --cache-subnet-group-name news2market-redis-subnet \
  --security-group-ids $REDIS_SG_ID \
  --automatic-failover-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled false \
  --snapshot-retention-limit 5 \
  --snapshot-window "03:00-05:00" \
  --tags "Key=Project,Value=News2Market"
```

Tiempo de creación: **10-15 minutos**

#### Obtener endpoint de Redis
```bash
# Esperar a que esté disponible
aws elasticache wait replication-group-available --replication-group-id news2market-redis

# Obtener endpoint primario
REDIS_ENDPOINT=$(aws elasticache describe-replication-groups \
  --replication-group-id news2market-redis \
  --query 'ReplicationGroups[0].NodeGroups[0].PrimaryEndpoint.Address' \
  --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"
# Ejemplo: news2market-redis.abc123.ng.0001.use1.cache.amazonaws.com
```

---

## Construcción y publicación de imágenes Docker

### 1. Crear repositorios ECR

```bash
# Crear repositorios para cada microservicio
aws ecr create-repository --repository-name news2market/api-gateway
aws ecr create-repository --repository-name news2market/data-acquisition
aws ecr create-repository --repository-name news2market/text-processor
aws ecr create-repository --repository-name news2market/correlation-service
aws ecr create-repository --repository-name news2market/frontend

# Obtener registry URL
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "ECR Registry: $ECR_REGISTRY"
```

### 2. Autenticación Docker con ECR

```bash
# Login a ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
```

### 3. Build y push de imágenes

```bash
cd infra-paralela-common-crawl-colcap/

# API Gateway
cd backend/api-gateway
docker build -t news2market/api-gateway:latest .
docker tag news2market/api-gateway:latest $ECR_REGISTRY/news2market/api-gateway:latest
docker push $ECR_REGISTRY/news2market/api-gateway:latest
cd ../..

# Data Acquisition
cd backend/data-acquisition
docker build -t news2market/data-acquisition:latest .
docker tag news2market/data-acquisition:latest $ECR_REGISTRY/news2market/data-acquisition:latest
docker push $ECR_REGISTRY/news2market/data-acquisition:latest
cd ../..

# Text Processor
cd backend/text-processor
docker build -t news2market/text-processor:latest .
docker tag news2market/text-processor:latest $ECR_REGISTRY/news2market/text-processor:latest
docker push $ECR_REGISTRY/news2market/text-processor:latest
cd ../..

# Correlation Service
cd backend/correlation-service
docker build -t news2market/correlation-service:latest .
docker tag news2market/correlation-service:latest $ECR_REGISTRY/news2market/correlation-service:latest
docker push $ECR_REGISTRY/news2market/correlation-service:latest
cd ../..

# Frontend
cd frontend
docker build -t news2market/frontend:latest .
docker tag news2market/frontend:latest $ECR_REGISTRY/news2market/frontend:latest
docker push $ECR_REGISTRY/news2market/frontend:latest
cd ..

# Verificar imágenes en ECR
aws ecr list-images --repository-name news2market/frontend
```

### Script automatizado (build_and_push.sh)

```bash
#!/bin/bash

set -e

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Login
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

SERVICES=("api-gateway" "data-acquisition" "text-processor" "correlation-service")

for service in "${SERVICES[@]}"; do
  echo "Building $service..."
  cd backend/$service
  docker build -t news2market/$service:latest .
  docker tag news2market/$service:latest $ECR_REGISTRY/news2market/$service:latest
  docker push $ECR_REGISTRY/news2market/$service:latest
  cd ../..
done

echo "Building frontend..."
cd frontend
docker build -t news2market/frontend:latest .
docker tag news2market/frontend:latest $ECR_REGISTRY/news2market/frontend:latest
docker push $ECR_REGISTRY/news2market/frontend:latest
cd ..

echo "All images pushed successfully!"
```

---

## Despliegue de aplicaciones

### 1. Crear namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

Contenido de `k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: news2market
  labels:
    name: news2market
    environment: production
```

### 2. Crear secrets

```bash
# Crear secret para credenciales de base de datos
kubectl create secret generic db-credentials \
  --from-literal=postgres-user=news2market_admin \
  --from-literal=postgres-password='ChangeMeToSecurePassword123!' \
  --from-literal=postgres-host=$RDS_ENDPOINT \
  --from-literal=postgres-port=5432 \
  --from-literal=postgres-db=news2market \
  -n news2market

# Crear secret para Redis
kubectl create secret generic redis-credentials \
  --from-literal=redis-host=$REDIS_ENDPOINT \
  --from-literal=redis-port=6379 \
  -n news2market

# Verificar secrets
kubectl get secrets -n news2market
```

### 3. Crear ConfigMap

Editar `k8s/configmap.yaml` con los endpoints reales:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: news2market-config
  namespace: news2market
data:
  API_GATEWAY_URL: "http://api-gateway-service:8000"
  DATA_SERVICE_URL: "http://data-acquisition-service:8001"
  PROCESS_SERVICE_URL: "http://text-processor-service:8002"
  CORRELATION_SERVICE_URL: "http://correlation-service:8003"
```

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Instalar Metrics Server (para HPA)

```bash
kubectl apply -f k8s/metrics-server.yaml

# Verificar instalación
kubectl get deployment metrics-server -n kube-system
kubectl top nodes  # Debe mostrar uso de CPU/memoria
```

### 5. Desplegar microservicios

**IMPORTANTE**: Editar cada deployment YAML para usar las imágenes de ECR:

```bash
# Ejemplo para text-processor-deployment.yaml
# Reemplazar:
#   image: text-processor:latest
# Por:
#   image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/news2market/text-processor:latest
```

Script para actualizar automáticamente:
```bash
#!/bin/bash

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

cd k8s/

for file in *-deployment.yaml; do
  sed -i.bak "s|image: \([^:]*\):latest|image: $ECR_REGISTRY/news2market/\1:latest|g" $file
done

cd ..
```

Desplegar servicios:
```bash
# Text Processor (con HPA)
kubectl apply -f k8s/text-processor-deployment.yaml
kubectl apply -f k8s/text-processor-hpa.yaml

# Correlation Service
kubectl apply -f k8s/correlation-service-deployment.yaml

# Frontend
kubectl apply -f k8s/frontend-deployment.yaml

# Verificar pods
kubectl get pods -n news2market -w

# Verificar servicios
kubectl get svc -n news2market
```

Output esperado:
```
NAME                        TYPE           CLUSTER-IP       EXTERNAL-IP
frontend-service            LoadBalancer   10.100.123.45    a1b2c3d4-....us-east-1.elb.amazonaws.com
text-processor-service      ClusterIP      10.100.67.89     <none>
correlation-service         ClusterIP      10.100.91.23     <none>
```

### 6. Obtener URL del frontend

```bash
FRONTEND_URL=$(kubectl get svc frontend-service -n news2market -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "Frontend URL: http://$FRONTEND_URL"
```

**Nota**: El DNS del LoadBalancer puede tardar 2-3 minutos en propagarse.

---

## Configuración de autoescalado

### HPA para Text Processor

El archivo `k8s/text-processor-hpa.yaml` ya está configurado:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: text-processor-hpa
  namespace: news2market
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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

Verificar HPA:
```bash
# Ver estado del HPA
kubectl get hpa -n news2market

# Ver detalles
kubectl describe hpa text-processor-hpa -n news2market

# Simular carga para ver autoscaling
kubectl run -it --rm load-generator --image=busybox -n news2market -- /bin/sh
# Dentro del pod:
while true; do wget -q -O- http://text-processor-service:8002/health; done
```

### Cluster Autoscaler (opcional)

Para que el cluster escale nodos automáticamente:

```bash
# Crear IAM policy
cat > cluster-autoscaler-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:DescribeTags",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:GetInstanceTypesFromInstanceRequirements",
        "eks:DescribeNodegroup"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:SetDesiredCapacity",
        "autoscaling:TerminateInstanceInAutoScalingGroup"
      ],
      "Resource": ["*"]
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name AmazonEKSClusterAutoscalerPolicy \
  --policy-document file://cluster-autoscaler-policy.json

# Crear service account con IAM role
eksctl create iamserviceaccount \
  --cluster=news2market-cluster \
  --namespace=kube-system \
  --name=cluster-autoscaler \
  --attach-policy-arn=arn:aws:iam::$AWS_ACCOUNT_ID:policy/AmazonEKSClusterAutoscalerPolicy \
  --override-existing-serviceaccounts \
  --approve

# Desplegar cluster autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Editar deployment para agregar cluster name
kubectl -n kube-system edit deployment cluster-autoscaler
# Agregar --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/news2market-cluster
```

---

## Monitoreo y logs

### CloudWatch Logs

Los logs del cluster ya están configurados en `cluster-config.yaml`. Ver logs:

```bash
# Listar log groups
aws logs describe-log-groups --log-group-name-prefix /aws/eks/news2market-cluster

# Ver logs de API server
aws logs tail /aws/eks/news2market-cluster/cluster --follow

# Ver logs de audit
aws logs tail /aws/eks/news2market-cluster/cluster/audit --follow
```

### CloudWatch Container Insights

Instalar Container Insights para métricas avanzadas:

```bash
# Crear namespace
kubectl create namespace amazon-cloudwatch

# Crear ConfigMap
ClusterName=news2market-cluster
RegionName=$AWS_REGION
FluentBitHttpPort='2020'
FluentBitReadFromHead='Off'

kubectl create configmap fluent-bit-cluster-info \
  --from-literal=cluster.name=${ClusterName} \
  --from-literal=http.server='On' \
  --from-literal=http.port=${FluentBitHttpPort} \
  --from-literal=read.head=${FluentBitReadFromHead} \
  --from-literal=logs.region=${RegionName} \
  -n amazon-cloudwatch

# Desplegar Fluent Bit
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml

# Verificar pods
kubectl get pods -n amazon-cloudwatch
```

Ver métricas en CloudWatch:
1. AWS Console → CloudWatch → Container Insights
2. Seleccionar cluster `news2market-cluster`
3. Ver dashboards: Performance Monitoring, Resources

### Logs de aplicación

```bash
# Ver logs de un pod específico
kubectl logs -f <pod-name> -n news2market

# Ver logs de todos los pods de un deployment
kubectl logs -f deployment/text-processor -n news2market --all-containers=true

# Ver logs con timestamps
kubectl logs --timestamps=true <pod-name> -n news2market

# Ver últimas 100 líneas
kubectl logs --tail=100 <pod-name> -n news2market
```

### Prometheus y Grafana (opcional)

Para monitoreo avanzado con Prometheus:

```bash
# Agregar Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Instalar kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Port forward Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Acceder a Grafana: http://localhost:3000
# Usuario: admin
# Password: prom-operator
```

---

## Optimización de costos

### Cálculo de costos mensuales estimados

| Recurso | Especificación | Costo/hora | Costo/mes |
|---------|---------------|------------|-----------|
| **EKS Control Plane** | 1 cluster | $0.10 | $73 |
| **EC2 Instances** | 3x t3.medium | $0.0416 x 3 | $90 |
| **EBS Volumes** | 3x 30GB gp3 | $0.08/GB-mes | $7.20 |
| **RDS PostgreSQL** | db.t3.medium (Multi-AZ) | $0.136 x 2 | $196 |
| **RDS Storage** | 50GB gp3 | $0.23/GB-mes | $11.50 |
| **ElastiCache Redis** | cache.t3.medium (2 nodes) | $0.068 x 2 | $98 |
| **NAT Gateway** | 1 gateway + data transfer | $0.045 + data | $33 + data |
| **Load Balancer** | Application LB | $0.0225 | $16.50 |
| **ECR Storage** | ~5GB images | $0.10/GB-mes | $0.50 |
| **CloudWatch Logs** | ~10GB/mes | $0.50/GB | $5 |
| **Data Transfer** | ~50GB out/mes | $0.09/GB | $4.50 |
| **TOTAL** | | | **~$535/mes** |

### Estrategias de ahorro

#### 1. Usar instancias Spot para workers

```yaml
# En cluster-config.yaml
managedNodeGroups:
  - name: news2market-spot-workers
    instanceType: t3.medium
    desiredCapacity: 3
    minSize: 2
    maxSize: 10
    spot: true  # Ahorra hasta 70%
```

**Ahorro**: ~$60/mes (70% de $90)

#### 2. Apagar cluster en horario no productivo

```bash
# Script para apagar/encender cluster
#!/bin/bash

# Apagar (conserva estado pero detiene nodos)
eksctl scale nodegroup --cluster=news2market-cluster --name=news2market-workers --nodes=0

# Encender
eksctl scale nodegroup --cluster=news2market-cluster --name=news2market-workers --nodes=3
```

Con cron para automatizar:
```bash
# Apagar a las 6 PM
0 18 * * * eksctl scale nodegroup --cluster=news2market-cluster --name=news2market-workers --nodes=0

# Encender a las 8 AM
0 8 * * 1-5 eksctl scale nodegroup --cluster=news2market-cluster --name=news2market-workers --nodes=3
```

**Ahorro**: ~$50/mes (aprox. 50% del tiempo apagado)

#### 3. Usar RDS con Single-AZ (no producción)

```bash
# Reemplazar --multi-az con --no-multi-az en comando de creación RDS
```

**Ahorro**: ~$98/mes (50% del costo RDS)

#### 4. Consolidar en single region

- Evitar cross-region data transfer
- Usar S3 y CloudFront para assets estáticos
- Implementar caching agresivo

#### 5. Reservar instancias (1 año)

Para uso constante, comprar Reserved Instances:
- **1 año, pago adelantado**: 40% descuento
- **3 años, pago adelantado**: 60% descuento

**Ahorro potencial**: ~$200/mes con Reserved Instances

### Configuración mínima para desarrollo/testing

```yaml
# cluster-config-dev.yaml
metadata:
  name: news2market-dev
  region: us-east-1

managedNodeGroups:
  - name: dev-workers
    instanceType: t3.small  # 2 vCPU, 2 GiB (en lugar de medium)
    desiredCapacity: 2
    minSize: 1
    maxSize: 3
    spot: true

# Usar PostgreSQL local en lugar de RDS
# Usar Redis local en lugar de ElastiCache
```

**Costo estimado dev**: ~$100/mes

---

## Troubleshooting

### Problemas comunes

#### 1. Pods en estado Pending

```bash
# Ver eventos del pod
kubectl describe pod <pod-name> -n news2market

# Causas comunes:
# - Insufficient CPU/memory → Aumentar recursos del node group
# - ImagePullBackOff → Verificar que la imagen existe en ECR
# - Volume mounting issues → Verificar PVC y StorageClass
```

Solución para insufficient resources:
```bash
eksctl scale nodegroup --cluster=news2market-cluster --name=news2market-workers --nodes=5
```

#### 2. ImagePullBackOff

```bash
# Verificar imagen en ECR
aws ecr describe-images --repository-name news2market/text-processor

# Verificar permisos del node
kubectl describe pod <pod-name> -n news2market | grep -A 5 "Failed to pull image"

# Re-autenticar Docker
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY

# Re-push imagen
docker push $ECR_REGISTRY/news2market/text-processor:latest
```

#### 3. CrashLoopBackOff

```bash
# Ver logs del pod
kubectl logs <pod-name> -n news2market --previous

# Causas comunes:
# - Error de configuración en variables de entorno
# - No puede conectar a base de datos
# - Puerto ya en uso
```

Verificar conectividad a RDS:
```bash
kubectl run -it --rm debug --image=postgres:15 -n news2market -- psql \
  "postgresql://news2market_admin:password@$RDS_ENDPOINT:5432/news2market"
```

#### 4. HPA no escala

```bash
# Verificar metrics-server
kubectl get deployment metrics-server -n kube-system

# Ver métricas actuales
kubectl top pods -n news2market

# Ver eventos del HPA
kubectl describe hpa text-processor-hpa -n news2market
```

Si metrics-server falla:
```bash
# Reinstalar metrics-server con flag --kubelet-insecure-tls
kubectl delete -f k8s/metrics-server.yaml
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/args/-",
    "value": "--kubelet-insecure-tls"
  }
]'
```

#### 5. LoadBalancer no obtiene EXTERNAL-IP

```bash
# Verificar eventos del servicio
kubectl describe svc frontend-service -n news2market

# Verificar IAM permissions del node group
aws iam list-attached-role-policies --role-name eksctl-news2market-cluster-nodegro-NodeInstanceRole-XXXXX

# Debe tener: AmazonEKS_CNI_Policy, AmazonEC2ContainerRegistryReadOnly
```

#### 6. No se puede conectar a RDS/ElastiCache

```bash
# Verificar security groups
aws ec2 describe-security-groups --group-ids $RDS_SG_ID $REDIS_SG_ID

# Verificar que el cluster SG está autorizado
# Debe aparecer el source-group del EKS

# Verificar conectividad desde pod
kubectl run -it --rm netcat --image=busybox -n news2market -- nc -zv $RDS_ENDPOINT 5432
```

### Comandos útiles de diagnóstico

```bash
# Ver todos los recursos en el namespace
kubectl get all -n news2market

# Ver eventos recientes
kubectl get events -n news2market --sort-by='.lastTimestamp'

# Ver configuración de un pod
kubectl get pod <pod-name> -n news2market -o yaml

# Ejecutar shell en un pod
kubectl exec -it <pod-name> -n news2market -- /bin/bash

# Port forward para debugging
kubectl port-forward svc/correlation-service 8003:8003 -n news2market
# Acceder a http://localhost:8003

# Copiar archivos desde/hacia pod
kubectl cp <pod-name>:/path/to/file ./local-file -n news2market

# Ver uso de recursos en tiempo real
watch kubectl top pods -n news2market

# Ver logs de múltiples pods
kubectl logs -l app=text-processor -n news2market --all-containers=true --follow
```

### Limpieza y eliminación

Para evitar costos continuos, eliminar todos los recursos:

```bash
# 1. Eliminar deployments
kubectl delete namespace news2market

# 2. Eliminar RDS
aws rds delete-db-instance \
  --db-instance-identifier news2market-postgres \
  --skip-final-snapshot

# 3. Eliminar ElastiCache
aws elasticache delete-replication-group \
  --replication-group-id news2market-redis

# 4. Eliminar cluster EKS (y todos los recursos asociados)
eksctl delete cluster --name news2market-cluster --wait

# 5. Eliminar repositorios ECR
for repo in api-gateway data-acquisition text-processor correlation-service frontend; do
  aws ecr delete-repository --repository-name news2market/$repo --force
done

# 6. Eliminar security groups (esperar a que se eliminen recursos)
aws ec2 delete-security-group --group-id $RDS_SG_ID
aws ec2 delete-security-group --group-id $REDIS_SG_ID

# Verificar que no queden recursos
aws eks list-clusters
aws rds describe-db-instances
aws elasticache describe-replication-groups
```

---

## Conclusión

Has completado el despliegue de **News2Market** en AWS EKS. El sistema ahora está:

✅ Ejecutándose en un cluster Kubernetes managed  
✅ Con PostgreSQL y Redis como servicios administrados  
✅ Con autoescalado horizontal (2-10 pods)  
✅ Con monitoreo via CloudWatch  
✅ Con alta disponibilidad (Multi-AZ)  
✅ Listo para producción

**Próximos pasos recomendados**:
- Configurar CI/CD con GitHub Actions o GitLab CI
- Implementar Ingress Controller con certificados SSL
- Configurar backups automáticos de RDS y Redis
- Implementar alertas de CloudWatch
- Documentar procedimientos de recuperación ante desastres

Para soporte y preguntas: [Abrir issue en GitHub](#)
