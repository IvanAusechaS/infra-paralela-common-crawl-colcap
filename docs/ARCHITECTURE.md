# 🏗️ Arquitectura del Sistema - News2Market

## Tabla de Contenidos
- [Visión General](#visión-general)
- [Arquitectura de Microservicios](#arquitectura-de-microservicios)
- [Flujo de Datos](#flujo-de-datos)
- [Componentes del Sistema](#componentes-del-sistema)
- [Escalabilidad y Paralelismo](#escalabilidad-y-paralelismo)
- [Tolerancia a Fallos](#tolerancia-a-fallos)
- [Stack Tecnológico](#stack-tecnológico)

---

## Visión General

**News2Market** es una plataforma distribuida y escalable diseñada para procesar información noticiosa de fuentes abiertas (Common Crawl) y correlacionarla con el índice económico COLCAP de Colombia.

### Características Principales
- ✅ **Arquitectura de microservicios** completamente desacoplada
- ✅ **Procesamiento distribuido** mediante workers escalables
- ✅ **Cola de mensajes** para distribución de tareas
- ✅ **Orquestación con Kubernetes** para alta disponibilidad
- ✅ **Despliegue en AWS EKS** con escalado automático
- ✅ **Frontend React** con visualización de resultados en tiempo real

---

## Arquitectura de Microservicios

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
       │ fetch  │ process   │ correlate  │ status                  │ health
       │        │           │            │                         │
┌──────▼────────▼───────────▼────────────▼─────────────────────────▼──┐
│                    MESSAGE QUEUE (Redis)                             │
│            Pub/Sub + Lista de tareas | Puerto: 6379                  │
└──────┬────────────────────┬───────────────────┬──────────────────────┘
       │                    │                   │
       │                    │                   │
┌──────▼──────────┐  ┌──────▼──────────┐  ┌────▼────────────────┐
│ Data Acquisition│  │ Text Processor  │  │ Correlation Service │
│   Service       │  │   Workers       │  │    Service          │
│  Puerto: 8001   │  │  (Escalables)   │  │   Puerto: 8003      │
│                 │  │  Puerto: 8002   │  │                     │
└──────┬──────────┘  └──────┬──────────┘  └────┬────────────────┘
       │                    │                   │
       │                    │                   │
       └────────────────────┼───────────────────┘
                            │
                  ┌─────────▼──────────┐
                  │   PostgreSQL DB    │
                  │   Puerto: 5432     │
                  │   newsdb           │
                  └────────────────────┘
```

---

## Flujo de Datos

### Pipeline Completo de Procesamiento

```
┌─────────────┐
│  Usuario    │
│ (Frontend)  │
└──────┬──────┘
       │ 1. Solicita análisis (fecha inicio/fin)
       ▼
┌──────────────┐
│ API Gateway  │ ──────► Valida parámetros
└──────┬───────┘         Crea job_id
       │ 2. Publica tarea en cola
       ▼
┌──────────────┐
│ Redis Queue  │ ──────► Tarea: {job_id, start_date, end_date}
└──────┬───────┘
       │ 3. Workers consumen tareas
       ▼
┌───────────────────────────────────────────────────────┐
│           FASE 1: ADQUISICIÓN DE DATOS                │
│  ┌─────────────────────────────────────────────┐      │
│  │ Data Acquisition Service                    │      │
│  │ - Consulta Common Crawl Index              │      │
│  │ - Descarga archivos WARC                   │      │
│  │ - Extrae noticias de dominios .co          │      │
│  │ - Filtra por rango de fechas               │      │
│  └──────────────────┬──────────────────────────┘      │
│                     │ Guarda en DB: raw_articles      │
└─────────────────────┼─────────────────────────────────┘
                      ▼
┌───────────────────────────────────────────────────────┐
│        FASE 2: PROCESAMIENTO DE TEXTO                 │
│  ┌─────────────────────────────────────────────┐      │
│  │ Text Processor Workers (N réplicas)         │      │
│  │ - Lee artículos sin procesar               │      │
│  │ - Limpieza HTML (BeautifulSoup)            │      │
│  │ - Normalización de texto                   │      │
│  │ - Extracción de entidades económicas       │      │
│  │ - Análisis de sentimiento (opcional)       │      │
│  │ - Tokenización y conteo                    │      │
│  └──────────────────┬──────────────────────────┘      │
│                     │ Actualiza DB: processed_articles│
└─────────────────────┼─────────────────────────────────┘
                      ▼
┌───────────────────────────────────────────────────────┐
│         FASE 3: CORRELACIÓN CON COLCAP                │
│  ┌─────────────────────────────────────────────┐      │
│  │ Correlation Service                         │      │
│  │ - Obtiene datos históricos COLCAP          │      │
│  │ - Agrupa noticias por fecha                │      │
│  │ - Calcula métricas: volumen, keywords      │      │
│  │ - Correlación de Pearson                   │      │
│  │ - Genera resultados y gráficas             │      │
│  └──────────────────┬──────────────────────────┘      │
│                     │ Guarda: correlation_results     │
└─────────────────────┼─────────────────────────────────┘
                      ▼
                ┌──────────┐
                │PostgreSQL│
                └──────┬───┘
                       │ 4. Frontend consulta resultados
                       ▼
                ┌──────────┐
                │ Frontend │ ──────► Muestra gráficos y correlaciones
                └──────────┘
```

---

## Componentes del Sistema

### 1. Frontend (React)
**Ubicación**: `/frontend`
**Puerto**: 3000
**Tecnologías**: React, Vite, SCSS, Recharts

**Responsabilidades**:
- Interfaz de usuario intuitiva y profesional
- Formulario para selección de rango de fechas
- Visualización de estado del pipeline
- Gráficos de correlación interactivos
- Dashboard con métricas en tiempo real

**Endpoints consumidos**:
- `POST /start-pipeline` - Inicia análisis
- `GET /status/{job_id}` - Consulta estado
- `GET /results/{job_id}` - Obtiene resultados
- `GET /health` - Verifica servicios

---

### 2. API Gateway
**Ubicación**: `/backend/api-gateway`
**Puerto**: 8000
**Tecnología**: FastAPI

**Responsabilidades**:
- Punto de entrada único al sistema
- Orquestación de microservicios
- Validación de peticiones
- Manejo de errores centralizado
- Autenticación (JWT - futuro)
- Rate limiting (futuro)

**Endpoints**:
- `GET /` - Información del servicio
- `POST /start-pipeline` - Inicia pipeline completo
- `GET /status/{job_id}` - Estado de job
- `GET /results/{job_id}` - Resultados de análisis
- `GET /health` - Health check
- `GET /services` - Lista de servicios activos

---

### 3. Data Acquisition Service
**Ubicación**: `/backend/data-acquisition`
**Puerto**: 8001
**Tecnología**: FastAPI, warcio, boto3

**Responsabilidades**:
- Conexión a Common Crawl (S3 o HTTP)
- Descarga y parsing de archivos WARC
- Filtrado por dominio (.co) y fechas
- Extracción de metadatos (título, fecha, URL)
- Almacenamiento en base de datos

**Endpoints**:
- `POST /fetch` - Inicia adquisición de datos
- `GET /crawls` - Lista crawls disponibles
- `GET /articles` - Obtiene artículos
- `GET /stats` - Estadísticas de datos

**Modo de operación**:
- **Modo producción**: Descarga desde Common Crawl S3
- **Modo desarrollo**: Usa datos mock para testing

---

### 4. Text Processor Workers
**Ubicación**: `/backend/text-processor`
**Puerto**: 8002 (load balanced)
**Tecnología**: FastAPI, BeautifulSoup, nltk, spaCy

**Responsabilidades**:
- Procesamiento distribuido de artículos
- Limpieza de HTML y texto
- Normalización y tokenización
- Extracción de entidades nombradas
- Identificación de keywords económicas
- Análisis de sentimiento básico

**Escalabilidad**:
- Múltiples réplicas (1-10+ workers)
- Procesamiento paralelo de artículos
- Consumo de cola Redis

**Palabras clave económicas**:
```python
ECONOMIC_KEYWORDS = [
    "colcap", "bolsa", "mercado", "acciones", "economía",
    "inflación", "dólar", "peso", "comercio", "exportación",
    "importación", "PIB", "banco", "inversión", "crisis"
]
```

---

### 5. Correlation Service
**Ubicación**: `/backend/correlation-service`
**Puerto**: 8003
**Tecnología**: FastAPI, pandas, scipy, numpy

**Responsabilidades**:
- Obtención de datos históricos COLCAP
- Agregación temporal de noticias
- Cálculo de métricas (volumen, keywords, sentimiento)
- Correlación de Pearson entre métricas y COLCAP
- Generación de insights y visualizaciones

**Métodos de correlación**:
1. **Volumen de noticias** vs COLCAP
2. **Frecuencia de keywords** vs COLCAP
3. **Sentimiento agregado** vs COLCAP
4. **Lag analysis** (correlación con retraso temporal)

**Fórmula de Pearson**:
```
r = Σ[(Xi - X̄)(Yi - Ȳ)] / √[Σ(Xi - X̄)² × Σ(Yi - Ȳ)²]
```

---

### 6. Message Queue (Redis)
**Ubicación**: Redis container
**Puerto**: 6379
**Tecnología**: Redis

**Responsabilidades**:
- Cola de tareas (lista FIFO)
- Pub/Sub para notificaciones
- Cache de resultados intermedios
- Estado de jobs
- Lock distribuido

**Estructuras de datos**:
```
tasks:pending → Lista de tareas pendientes
tasks:processing → Set de tareas en proceso
tasks:completed → Set de tareas completadas
job:{job_id}:status → Estado del job
job:{job_id}:result → Resultado del job
```

---

### 7. Base de Datos PostgreSQL
**Ubicación**: PostgreSQL container
**Puerto**: 5432
**Base de datos**: `newsdb`

**Esquema**:

```sql
-- Tabla de artículos crudos
CREATE TABLE raw_articles (
    id SERIAL PRIMARY KEY,
    url VARCHAR(2048) UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    published_date DATE,
    domain VARCHAR(255),
    crawl_id VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_published_date (published_date),
    INDEX idx_domain (domain)
);

-- Tabla de artículos procesados
CREATE TABLE processed_articles (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES raw_articles(id),
    cleaned_content TEXT,
    word_count INTEGER,
    economic_keywords JSONB,
    sentiment_score FLOAT,
    entities JSONB,
    processed_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_article_id (article_id)
);

-- Tabla de datos COLCAP
CREATE TABLE colcap_data (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    opening_price FLOAT,
    closing_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    volume BIGINT,
    INDEX idx_date (date)
);

-- Tabla de resultados de correlación
CREATE TABLE correlation_results (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    start_date DATE,
    end_date DATE,
    articles_count INTEGER,
    correlation_volume FLOAT,
    correlation_keywords FLOAT,
    correlation_sentiment FLOAT,
    p_value FLOAT,
    insights JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de jobs (estado del pipeline)
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50), -- pending, processing, completed, failed
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    error_message TEXT
);
```

---

## Escalabilidad y Paralelismo

### Escalado Horizontal

#### Text Processor Workers
Los workers de procesamiento pueden escalar de 1 a N réplicas:

```yaml
# Kubernetes HPA (Horizontal Pod Autoscaler)
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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Comportamiento**:
- Con 1 worker: Procesa ~100 artículos/min
- Con 5 workers: Procesa ~500 artículos/min
- Con 10 workers: Procesa ~1000 artículos/min

### Distribución de Carga

**Redis como cola**:
```python
# Worker consume de la cola
while True:
    task = redis.blpop('tasks:pending', timeout=5)
    if task:
        process_article(task)
        redis.lpush('tasks:completed', task)
```

**Ventajas**:
- Procesamiento asíncrono
- Tolerancia a fallos (reintento automático)
- Balance de carga automático
- Desacoplamiento de servicios

---

## Tolerancia a Fallos

### Health Checks
Todos los servicios implementan health checks:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "dependencies": {
            "database": check_db_connection(),
            "redis": check_redis_connection()
        }
    }
```

### Kubernetes Liveness y Readiness Probes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Circuit Breaker (futuro)
Implementar usando `tenacity` para reintentos:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_service(url):
    response = await client.get(url)
    return response.json()
```

### Backup y Recuperación
- Base de datos: Snapshots automáticos en AWS RDS
- Estado: Persistido en Redis con AOF habilitado
- Logs: Centralizados en CloudWatch

---

## Stack Tecnológico

### Backend
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Lenguaje | Python | 3.11+ |
| Framework Web | FastAPI | 0.104+ |
| Validación | Pydantic | 2.0+ |
| HTTP Client | httpx | 0.25+ |
| Procesamiento | pandas, numpy | Latest |
| Análisis estadístico | scipy | 1.11+ |
| Procesamiento texto | BeautifulSoup4 | 4.12+ |
| Common Crawl | warcio | 1.7+ |
| Base de datos | asyncpg, SQLAlchemy | 2.0+ |
| Cache | redis-py | 5.0+ |
| Workers | Celery (opcional) | 5.3+ |

### Frontend
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | React | 18+ |
| Build Tool | Vite | 5+ |
| Lenguaje | JavaScript/TypeScript | ES2022 |
| Estilos | SCSS | Latest |
| Gráficos | Recharts | 2.10+ |
| HTTP Client | Axios | 1.6+ |
| Router | React Router | 6+ |
| Estado | Zustand/Redux | Latest |
| UI Components | Headless UI / Radix | Latest |

### Infraestructura
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Contenedores | Docker | 24+ |
| Orquestación | Kubernetes | 1.28+ |
| Orquestación local | Docker Compose | 2.23+ |
| Cloud Provider | AWS | - |
| Kubernetes AWS | EKS | 1.28+ |
| Registry | ECR | - |
| Storage | S3 | - |
| Database | PostgreSQL | 15+ |
| Cache/Queue | Redis | 7+ |
| Monitoring | CloudWatch | - |
| Logs | CloudWatch Logs | - |

### DevOps y CI/CD
| Componente | Tecnología |
|------------|------------|
| Control de versiones | Git |
| CI/CD | GitHub Actions |
| IaC | kubectl, eksctl |
| Scripts | Bash, Python |
| Testing | pytest, Jest |
| Linting | pylint, ESLint |
| Formatting | black, prettier |

---

## Consideraciones de Seguridad

### Variables de Entorno
Todas las credenciales deben estar en variables de entorno:
```bash
# Nunca en el código
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
```

### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  database-url: <base64>
  redis-url: <base64>
```

### Network Policies
Restringir comunicación entre pods:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-gateway-policy
spec:
  podSelector:
    matchLabels:
      app: api-gateway
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

---

## Métricas y Monitoreo

### Métricas Clave
1. **Latencia de pipeline**: Tiempo total de procesamiento
2. **Throughput**: Artículos procesados por minuto
3. **Tasa de error**: Errores / total de peticiones
4. **Uso de recursos**: CPU, memoria por servicio
5. **Escalado**: Número de pods activos

### CloudWatch Dashboards
- CPU y memoria por servicio
- Latencia de API Gateway
- Throughput de workers
- Errores y warnings
- Tamaño de cola Redis

### Alertas
- CPU > 80% durante 5 minutos
- Memoria > 90%
- Tasa de error > 5%
- Cola Redis > 1000 tareas pendientes

---

## Próximos Pasos

### Fase 1 - MVP (Actual)
- ✅ Arquitectura base de microservicios
- ✅ Procesamiento distribuido básico
- ✅ Frontend con visualización
- ✅ Despliegue en Kubernetes

### Fase 2 - Mejoras
- ⬜ Autenticación JWT
- ⬜ Rate limiting en API Gateway
- ⬜ Análisis de sentimiento avanzado (transformers)
- ⬜ Caché de resultados con TTL
- ⬜ Tests de carga (Locust)

### Fase 3 - Optimización
- ⬜ ML para predicción de mercado
- ⬜ WebSockets para actualizaciones en tiempo real
- ⬜ Almacenamiento en S3 para datasets grandes
- ⬜ CI/CD completo con GitHub Actions
- ⬜ Infrastructure as Code (Terraform)

---

**Última actualización**: Diciembre 2024
**Versión**: 1.0.0
**Mantenedores**: Equipo News2Market
