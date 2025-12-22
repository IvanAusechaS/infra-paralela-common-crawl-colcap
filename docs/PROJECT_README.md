# 📰 News2Market - Análisis de Correlación Noticias-COLCAP

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18+-61DAFB.svg)](https://reactjs.org/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-1.28+-326CE5.svg)](https://kubernetes.io/)
[![AWS](https://img.shields.io/badge/AWS-EKS-FF9900.svg)](https://aws.amazon.com/eks/)

## 🎯 Descripción

**News2Market** es un sistema distribuido de alto rendimiento para análisis de correlación entre noticias económicas del mercado colombiano y el índice COLCAP. Desarrollado como proyecto final para la asignatura **Infraestructuras Paralelas y Distribuidas** de la Universidad del Valle.

El sistema demuestra conceptos avanzados de:
- Arquitectura de microservicios
- Procesamiento paralelo y distribuido
- Orquestación con Kubernetes
- Escalado automático horizontal (HPA)
- Despliegue en AWS EKS
- Análisis estadístico con correlación de Pearson

## 📂 Estructura del proyecto

```
infra-paralela-common-crawl-colcap/
├── README.md                          # Este archivo
├── docs/
│   ├── ARCHITECTURE.md                # Arquitectura del sistema
│   ├── INSTALLATION.md                # Guía de instalación
│   └── AWS_DEPLOYMENT.md              # Despliegue en AWS
├── backend/
│   ├── api-gateway/                   # Gateway HTTP principal
│   ├── data-acquisition/              # Adquisición desde Common Crawl
│   ├── text-processor/                # Procesamiento de texto
│   │   ├── app.py                     # API FastAPI
│   │   ├── processor.py               # Motor de procesamiento
│   │   ├── database.py                # Modelos SQLAlchemy
│   │   ├── queue_client.py            # Cliente Redis
│   │   ├── Dockerfile                 # Imagen Docker
│   │   └── requirements.txt
│   ├── correlation-service/           # Análisis de correlación
│   │   ├── app.py                     # API FastAPI
│   │   ├── colcap_client.py           # Cliente COLCAP
│   │   ├── correlation_engine.py      # Motor de correlación
│   │   ├── database.py                # Modelos SQLAlchemy
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── docker-compose.yml             # Orquestación local
├── frontend/                          # Interfaz React
│   ├── src/
│   │   ├── components/                # Componentes reutilizables
│   │   ├── pages/                     # Páginas principales
│   │   ├── services/                  # Cliente API
│   │   └── styles/                    # SCSS global
│   ├── Dockerfile                     # Build con Nginx
│   ├── nginx.conf                     # Configuración Nginx
│   └── package.json
└── k8s/                               # Manifests Kubernetes
    ├── namespace.yaml
    ├── configmap.yaml
    ├── secrets.yaml
    ├── text-processor-deployment.yaml
    ├── text-processor-hpa.yaml         # Autoescalado 2-10 replicas
    ├── correlation-service-deployment.yaml
    ├── frontend-deployment.yaml
    ├── postgres-statefulset.yaml
    ├── redis-statefulset.yaml
    ├── cluster-config.yaml             # Configuración EKS
    └── metrics-server.yaml
```

## 🚀 Inicio rápido

### Requisitos previos

- **Docker** 24+
- **Docker Compose** 2.0+
- **Node.js** 20+ (para desarrollo frontend)
- **Python** 3.11+ (para desarrollo backend)
- **kubectl** (para despliegue en Kubernetes)
- **AWS CLI** (para despliegue en EKS)
- **eksctl** (para crear cluster EKS)

### Instalación local con Docker Compose

1. **Clonar el repositorio**:
```bash
git clone <repository-url>
cd infra-paralela-common-crawl-colcap
```

2. **Configurar variables de entorno**:
```bash
# Backend services
cp backend/text-processor/.env.example backend/text-processor/.env
cp backend/correlation-service/.env.example backend/correlation-service/.env

# Frontend
cp frontend/.env.example frontend/.env
```

3. **Construir y levantar servicios**:
```bash
cd backend
docker-compose up --build
```

4. **Acceder a los servicios**:
- **API Gateway**: http://localhost:8000
- **Text Processor**: http://localhost:8002
- **Correlation Service**: http://localhost:8003
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Desarrollo del frontend

```bash
cd frontend
npm install
npm run dev
# Acceder a http://localhost:5173
```

### Build de producción frontend

```bash
cd frontend
npm run build
# Los archivos compilados estarán en frontend/dist/
```

## 🏗️ Arquitectura

### Microservicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **API Gateway** | 8000 | Punto de entrada HTTP, enrutamiento |
| **Data Acquisition** | 8001 | Extracción de Common Crawl |
| **Text Processor** | 8002 | Limpieza, keywords, sentimiento |
| **Correlation Service** | 8003 | Análisis estadístico Pearson |
| **Frontend** | 5173/80 | Interfaz React con Vite/Nginx |

### Flujo de datos

```
1. Common Crawl → Data Acquisition → PostgreSQL (raw_articles)
2. API Gateway → Redis Queue → Text Processor Workers (N pods)
3. Text Processor → PostgreSQL (processed_articles)
4. Frontend → Correlation Service → COLCAP + News → Pearson Correlation
5. Correlation Service → PostgreSQL (correlation_results)
```

### Tecnologías principales

**Backend**:
- Python 3.11+, FastAPI 0.104+, SQLAlchemy 2.0+
- PostgreSQL 15+, Redis 7+
- BeautifulSoup4, pandas, scipy, numpy

**Frontend**:
- React 18, TypeScript, Vite 5
- SCSS, Recharts 2.10+, Axios, React Router 6

**Infraestructura**:
- Docker, Kubernetes 1.28+
- AWS EKS, ECR, RDS, ElastiCache
- HPA (Horizontal Pod Autoscaler)

## 📊 Escalabilidad demostrada

### Pruebas de carga

| Workers | Throughput | Speedup |
|---------|------------|---------|
| 1 pod | 5.5 art/s | 1.0x |
| 3 pods | 15.8 art/s | 2.9x |
| 5 pods | 25.2 art/s | 4.6x |
| 10 pods | 42.3 art/s | 7.7x |

### HPA Configuration

- **Min replicas**: 2
- **Max replicas**: 10
- **Target CPU**: 70%
- **Target Memory**: 80%
- **Scale up**: +100% cada 60s
- **Scale down**: -50% cada 300s

## ☁️ Despliegue en AWS EKS

### Crear cluster

```bash
eksctl create cluster -f k8s/cluster-config.yaml
```

### Crear namespace y configuración

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
```

### Desplegar servicios

```bash
# PostgreSQL y Redis
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-statefulset.yaml

# Metrics Server (para HPA)
kubectl apply -f k8s/metrics-server.yaml

# Microservicios
kubectl apply -f k8s/text-processor-deployment.yaml
kubectl apply -f k8s/text-processor-hpa.yaml
kubectl apply -f k8s/correlation-service-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

### Verificar despliegue

```bash
kubectl get pods -n news2market
kubectl get hpa -n news2market
kubectl get svc -n news2market
```

### Obtener URL del frontend

```bash
kubectl get svc frontend-service -n news2market -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

## 📝 Documentación adicional

- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md): Diseño detallado del sistema
- [**INSTALLATION.md**](docs/INSTALLATION.md): Instalación paso a paso
- [**AWS_DEPLOYMENT.md**](docs/AWS_DEPLOYMENT.md): Guía completa de AWS EKS

## 🎓 Objetivos académicos cumplidos

- ✅ **Concurrencia y paralelismo**: Workers distribuidos con Redis queue
- ✅ **Contenedorización**: Docker multi-stage builds para todos los servicios
- ✅ **Orquestación**: Kubernetes con Deployments, StatefulSets, Services
- ✅ **Escalabilidad**: HPA con métricas de CPU y memoria
- ✅ **Cloud Computing**: Despliegue en AWS EKS con ECR
- ✅ **Análisis estadístico**: Correlación de Pearson con scipy
- ✅ **Visualización**: Frontend React con gráficos Recharts

## 👥 Equipo

**Universidad del Valle**  
Facultad de Ingeniería  
Asignatura: Infraestructuras Paralelas y Distribuidas

## 📄 Licencia

Este proyecto es académico y se distribuye bajo licencia MIT.

## 🙏 Agradecimientos

- **Common Crawl**: Por proporcionar datos abiertos de web crawling
- **Comunidad Open Source**: Por las excelentes herramientas utilizadas
- **Profesores y compañeros**: Por el apoyo durante el desarrollo

---

**¿Preguntas o sugerencias?** Abre un issue en el repositorio.
