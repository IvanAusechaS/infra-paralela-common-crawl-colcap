# 📊 News2Market

> Plataforma distribuida para el análisis y correlación de eventos noticiosos con mercados financieros

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28+-326CE5.svg)](https://kubernetes.io/)
[![AWS](https://img.shields.io/badge/AWS-EKS-FF9900.svg)](https://aws.amazon.com/eks/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Descripción del Proyecto

**News2Market** es un prototipo funcional de software distribuido y escalable que procesa información noticiosa de fuentes abiertas (Common Crawl) para identificar correlaciones entre hechos mediáticos y el índice económico COLCAP de Colombia.

Este proyecto fue desarrollado como trabajo final para la asignatura **Infraestructuras Paralelas y Distribuidas**, demostrando la aplicación práctica de:

- ✅ **Arquitectura de microservicios** completamente distribuida
- ✅ **Procesamiento paralelo** mediante workers escalables
- ✅ **Contenedorización** con Docker
- ✅ **Orquestación** con Kubernetes en AWS EKS
- ✅ **Escalabilidad horizontal** con métricas de rendimiento
- ✅ **Tolerancia a fallos** y alta disponibilidad

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                             │
│                   Puerto: 3000 | Vite + SCSS                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                           │
│         Puerto: 8000 | Orquestación de servicios                    │
└──────┬────────┬───────────┬────────────┬─────────────────────────┬──┘
       │        │           │            │                         │
       │ fetch  │ process   │ correlate  │ status                  │
       │        │           │            │                         │
┌──────▼────────▼───────────▼────────────▼─────────────────────────▼──┐
│                    MESSAGE QUEUE (Redis)                             │
│            Pub/Sub + Lista de tareas | Puerto: 6379                  │
└──────┬────────────────────┬───────────────────┬──────────────────────┘
       │                    │                   │
┌──────▼──────────┐  ┌──────▼──────────┐  ┌────▼────────────────┐
│ Data Acquisition│  │ Text Processor  │  │ Correlation Service │
│   Service       │  │   Workers       │  │    Service          │
│  Puerto: 8001   │  │  (Escalables)   │  │   Puerto: 8003      │
└──────┬──────────┘  └──────┬──────────┘  └────┬────────────────┘
       │                    │                   │
       └────────────────────┼───────────────────┘
                            │
                  ┌─────────▼──────────┐
                  │   PostgreSQL DB    │
                  │   Puerto: 5432     │
                  └────────────────────┘
```

**Ver documentación completa**: [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🚀 Inicio Rápido

### Prerequisitos

- **Docker** 24+ y Docker Compose 2.20+
- **Node.js** 18+ y npm
- **Python** 3.11+
- **kubectl** 1.28+ (para despliegue en K8s)
- **AWS CLI** v2 (para despliegue en AWS)

**Ver guía completa de instalación**: [INSTALLATION.md](docs/INSTALLATION.md)

### Ejecución Local con Docker Compose

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/infra-paralela-common-crawl-colcap.git
cd infra-paralela-common-crawl-colcap

# 2. Configurar variables de entorno
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Levantar servicios backend con Docker Compose
cd backend
docker-compose up -d --build

# 4. Iniciar frontend (en otra terminal)
cd frontend
npm install
npm run dev

# 5. Acceder a la aplicación
# Frontend: http://localhost:3000
# API Gateway: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Ver más opciones de ejecución**: [INSTALLATION.md](docs/INSTALLATION.md)

---

## ☁️ Despliegue en AWS EKS

### Resumen de Pasos

```bash
# 1. Configurar AWS CLI
aws configure

# 2. Cargar variables de entorno
source scripts/aws-config.sh

# 3. Crear clúster EKS
eksctl create cluster -f k8s/cluster-config.yaml

# 4. Crear repositorios ECR y construir imágenes
./scripts/build-and-push.sh

# 5. Desplegar en Kubernetes
kubectl apply -f k8s/

# 6. Obtener URL del Load Balancer
kubectl get ingress -n news2market
```

**Ver guía detallada de despliegue**: [AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md)

---

## 📊 Pipeline de Procesamiento

El sistema implementa un pipeline de 4 etapas:

### 1️⃣ Adquisición de Datos
- Lectura de Common Crawl o scraping de medios colombianos
- Filtrado por dominio (.co) y rango de fechas
- Almacenamiento de artículos crudos en PostgreSQL

### 2️⃣ Limpieza y Transformación
- Eliminación de HTML y normalización de texto
- Extracción de metadatos (título, fecha, fuente)
- Tokenización y limpieza de stopwords

### 3️⃣ Análisis de Texto
- Identificación de palabras clave económicas
- Conteo de frecuencias y métricas temporales
- Análisis de sentimiento (opcional)

### 4️⃣ Correlación con COLCAP
- Obtención de datos históricos del índice COLCAP
- Agregación de métricas noticiosas por fecha
- Cálculo de correlación de Pearson
- Generación de visualizaciones

---

## 🔥 Características Principales

### Paralelismo y Escalabilidad
- **Workers distribuidos**: Procesamiento paralelo de artículos
- **Escalado horizontal**: De 1 a N pods dinámicamente
- **Cola de mensajes**: Distribución eficiente de tareas con Redis
- **Auto-scaling**: HPA basado en CPU y memoria

### Demostración de Rendimiento

| Configuración | Artículos | Tiempo | Throughput |
|---------------|-----------|--------|------------|
| 1 worker | 1000 | ~180s | 5.5 art/s |
| 3 workers | 1000 | ~65s | 15.4 art/s |
| 5 workers | 1000 | ~40s | 25 art/s |

**Mejora de rendimiento**: Hasta **4.5x** más rápido con escalado horizontal

### Tolerancia a Fallos
- Health checks en todos los servicios
- Reintentos automáticos en caso de fallo
- Liveness y Readiness probes en Kubernetes
- Persistencia de estado en PostgreSQL

---

## 🛠️ Stack Tecnológico

### Backend
- **Lenguaje**: Python 3.11+
- **Framework**: FastAPI
- **Procesamiento**: pandas, numpy, scipy
- **Análisis de texto**: BeautifulSoup4, warcio
- **Base de datos**: PostgreSQL 15+ (asyncpg, SQLAlchemy)
- **Cache/Queue**: Redis 7+

### Frontend
- **Framework**: React 18+
- **Build tool**: Vite 5+
- **Estilos**: SCSS
- **Gráficos**: Recharts
- **HTTP Client**: Axios
- **Routing**: React Router v6

### Infraestructura
- **Contenedores**: Docker 24+
- **Orquestación**: Kubernetes 1.28+
- **Cloud**: AWS (EKS, ECR, EC2, RDS, ElastiCache)
- **Desarrollo local**: Docker Compose
- **Monitoreo**: CloudWatch

---

## 📁 Estructura del Proyecto

```
infra-paralela-common-crawl-colcap/
├── backend/
│   ├── api-gateway/              # API Gateway (FastAPI)
│   ├── data-acquisition/         # Servicio de adquisición
│   ├── text-processor/           # Workers de procesamiento
│   ├── correlation-service/      # Servicio de correlación
│   ├── docker-compose.yml        # Orquestación local
│   └── init-db.sql               # Schema de base de datos
├── frontend/                     # Aplicación React
│   ├── src/
│   │   ├── components/           # Componentes React
│   │   ├── pages/                # Páginas/Vistas
│   │   ├── services/             # Cliente API
│   │   └── styles/               # SCSS global
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── k8s/                          # Manifiestos Kubernetes
│   ├── namespace.yaml
│   ├── deployments/
│   ├── services/
│   ├── ingress.yaml
│   └── cluster-config.yaml
├── scripts/                      # Scripts de automatización
│   ├── build-and-push.sh         # Build y push a ECR
│   ├── deploy-k8s.sh             # Despliegue en K8s
│   ├── load-test.sh              # Pruebas de carga
│   └── cleanup-aws.sh            # Limpieza de recursos
├── docs/                         # Documentación
│   ├── ARCHITECTURE.md           # Arquitectura del sistema
│   ├── INSTALLATION.md           # Guía de instalación
│   └── AWS_DEPLOYMENT.md         # Despliegue en AWS
└── README.md                     # Este archivo
```

---

## 🧪 Pruebas y Validación

### Health Checks

```bash
# Verificar todos los servicios
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # Data Acquisition
curl http://localhost:8002/health  # Text Processor
curl http://localhost:8003/health  # Correlation Service
```

### Ejecutar Pipeline Completo

```bash
# Mediante API
curl -X POST http://localhost:8000/start-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "limit": 100
  }'

# Mediante Frontend
# Ir a http://localhost:3000 y usar la interfaz gráfica
```

---

## 📈 Métricas y Monitoreo

### Métricas Clave

- **Latencia del pipeline**: Tiempo total desde ingesta hasta correlación
- **Throughput**: Artículos procesados por minuto
- **Tasa de error**: Porcentaje de peticiones fallidas
- **Uso de recursos**: CPU y memoria por servicio
- **Escalado automático**: Número de réplicas activas

---

## 🎓 Objetivos Académicos Cumplidos

✅ **Ejecución concurrente**: Workers procesando artículos en paralelo  
✅ **Contenedores Docker**: Todos los servicios contenedorizados  
✅ **Orquestación Kubernetes**: Desplegado en AWS EKS  
✅ **Escalabilidad**: Demostración de mejora de rendimiento con réplicas  
✅ **Datos reales**: Procesamiento de Common Crawl  
✅ **Pipeline completo**: Ingesta → Limpieza → Análisis → Correlación  
✅ **Análisis estadístico**: Correlación de Pearson con COLCAP  
✅ **Infraestructura en la nube**: AWS (EKS, ECR, RDS, ElastiCache)

---

## 📚 Documentación Adicional

- **[Arquitectura del Sistema](docs/ARCHITECTURE.md)**: Diseño detallado de microservicios, flujo de datos, esquema de base de datos
- **[Guía de Instalación](docs/INSTALLATION.md)**: Instalación de herramientas, configuración de entornos, ejecución local
- **[Despliegue en AWS](docs/AWS_DEPLOYMENT.md)**: Creación de clúster EKS, ECR, despliegue completo en AWS
- **[Documentación de API](http://localhost:8000/docs)**: Swagger UI con todos los endpoints

---

## 🔧 Comandos Útiles

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Escalar workers (local)
docker-compose up -d --scale text-processor=3

# Ver estado de pods (K8s)
kubectl get pods -n news2market -o wide

# Escalar workers (K8s)
kubectl scale deployment text-processor --replicas=5 -n news2market

# Ver métricas de recursos
kubectl top pods -n news2market
```

---

## ⚠️ Consideraciones Importantes

### Costos en AWS
- El despliegue en AWS genera costos (~$180-200/mes)
- **IMPORTANTE**: Eliminar recursos cuando no se usen: `./scripts/cleanup-aws.sh`

### Limitaciones del Prototipo
- Este es un prototipo académico, no un sistema de producción
- El análisis estadístico es básico (correlación de Pearson)
- Los datos de Common Crawl tienen latencia de 4-8 semanas

---

## 🌟 Referencias

- [Common Crawl](https://commoncrawl.org/) - Datos web abiertos
- [Kubernetes](https://kubernetes.io/) - Orquestación de contenedores
- [AWS EKS](https://aws.amazon.com/eks/) - Kubernetes gestionado
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [React](https://react.dev/) - Biblioteca para interfaces de usuario

---

<div align="center">

**News2Market** - Infraestructuras Paralelas y Distribuidas  
Universidad del Valle - 2024

</div>
