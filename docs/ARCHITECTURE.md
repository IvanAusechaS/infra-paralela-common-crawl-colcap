# Arquitectura del Sistema News2Market

## Índice
1. [Visión general](#visión-general)
2. [Diagrama de arquitectura](#diagrama-de-arquitectura)
3. [Componentes del sistema](#componentes-del-sistema)
4. [Flujo de datos](#flujo-de-datos)
5. [Estrategias de escalabilidad](#estrategias-de-escalabilidad)
6. [Base de datos](#base-de-datos)
7. [Paralelismo y concurrencia](#paralelismo-y-concurrencia)
8. [Tolerancia a fallos](#tolerancia-a-fallos)

---

## Visión general

**News2Market** es un sistema distribuido diseñado para analizar la correlación entre noticias económicas y el índice COLCAP (Colombia Capital Index). El sistema implementa una arquitectura de microservicios orquestada con Kubernetes, demostrando conceptos clave de infraestructuras paralelas y distribuidas.

### Principios de diseño

- **Microservicios**: Cada componente es independiente y escalable
- **Contenedorización**: Todo el sistema se ejecuta en contenedores Docker
- **Procesamiento paralelo**: Uso de workers distribuidos para análisis de texto
- **Escalabilidad horizontal**: HPA (Horizontal Pod Autoscaler) automático
- **Desacoplamiento**: Comunicación asíncrona mediante colas Redis
- **Persistencia**: PostgreSQL con modelo relacional normalizado

---

## Diagrama de arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE WEB                             │
│                      (Navegador/Browser)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                           │
│  ┌─────────────┬──────────────┬────────────────┐              │
│  │  HomePage   │ AnalysisPage │  ResultsPage   │              │
│  │  (Stats)    │  (Config)    │  (Viz + PDF)   │              │
│  └─────────────┴──────────────┴────────────────┘              │
│               Nginx (Producción) / Vite (Dev)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP :5173/:80
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API GATEWAY (FastAPI)                         │
│  Puerto: 8000                                                   │
│  ┌──────────────────────────────────────────────────┐          │
│  │ • Enrutamiento HTTP                              │          │
│  │ • Proxy a microservicios                         │          │
│  │ • Validación de requests                         │          │
│  │ • Health checks consolidados                     │          │
│  └──────────────────────────────────────────────────┘          │
└────────────┬──────────────┬──────────────┬──────────────────────┘
             │              │              │
    ┌────────┘              │              └────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────────┐   ┌──────────────────┐   ┌──────────────────┐
│DATA         │   │TEXT PROCESSOR    │   │CORRELATION       │
│ACQUISITION  │   │Puerto: 8002      │   │SERVICE           │
│Puerto: 8001 │   │                  │   │Puerto: 8003      │
│             │   │Workers: 2-10     │   │                  │
│Common Crawl │   │HPA Enabled       │   │Pearson Engine    │
│Connector    │   │                  │   │COLCAP Client     │
└──────┬──────┘   └────────┬─────────┘   └────────┬─────────┘
       │                   │                      │
       │                   │                      │
       │                   │ ┌────────────────┐  │
       │                   └─┤   REDIS QUEUE  │──┘
       │                     │   Puerto: 6379 │
       │                     │   Key-Value    │
       │                     │   Pub/Sub      │
       │                     └────────────────┘
       │                              │
       │                              │
       └──────────────┬───────────────┘
                      │
                      ▼
          ┌────────────────────────┐
          │   POSTGRESQL DATABASE  │
          │   Puerto: 5432         │
          │                        │
          │   Tables:              │
          │   • raw_articles       │
          │   • processed_articles │
          │   • correlation_results│
          │   • colcap_data        │
          └────────────────────────┘
```

---

## Componentes del sistema

### 1. Frontend (React + TypeScript)

**Propósito**: Interfaz de usuario para configurar análisis y visualizar resultados

**Tecnologías**:
- React 18 con TypeScript
- Vite 5 (dev server y build)
- SCSS para estilos
- Recharts para gráficos
- jsPDF para exportación PDF
- react-toastify para notificaciones

**Páginas principales**:
- **HomePage**: Dashboard con estadísticas en tiempo real
- **AnalysisPage**: Configuración de análisis (fechas, métricas, keywords)
- **ResultsPage**: Visualización de correlaciones, gráficos, insights, descarga PDF

**Deployment**:
- Desarrollo: Vite dev server (puerto 5173)
- Producción: Nginx sirviendo archivos estáticos (puerto 80)

### 2. API Gateway (FastAPI)

**Propósito**: Punto de entrada único para todas las peticiones del cliente

**Responsabilidades**:
- Enrutamiento de requests a microservicios backend
- Validación de parámetros
- Consolidación de health checks
- Proxy transparente con httpx.AsyncClient
- Manejo centralizado de errores HTTP

**Endpoints principales**:
```python
GET  /                                    # Info del gateway
GET  /api/v1/health                       # Estado de servicios
POST /api/v1/analysis                     # Pipeline completo
GET  /api/v1/correlation/results          # Lista de resultados
POST /api/v1/correlation/correlate        # Calcular correlación
DELETE /api/v1/correlation/results/{id}   # Eliminar resultado
```

**Puerto**: 8000

### 3. Data Acquisition Service

**Propósito**: Obtener artículos de Common Crawl basados en rango de fechas

**Funcionalidades**:
- Conexión a Common Crawl Index API
- Filtrado por dominio colombiano (.co)
- Extracción de contenido HTML
- Almacenamiento en tabla `raw_articles`

**Modelo de datos** (`raw_articles`):
```sql
CREATE TABLE raw_articles (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    crawled_at TIMESTAMP,
    source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Puerto**: 8001

### 4. Text Processor Service (Worker Pool)

**Propósito**: Procesamiento paralelo de artículos con análisis de sentimiento

**Procesamiento de cada artículo**:
1. **Limpieza**: Eliminación de HTML tags, scripts, estilos
2. **Extracción de keywords**: Top 10 palabras clave económicas
3. **Análisis de sentimiento**: Positivo/Negativo/Neutral
4. **Cálculo de scores**: Sentiment score (-1 a +1)

**Arquitectura de workers**:
- **Mínimo**: 2 réplicas (Kubernetes HPA)
- **Máximo**: 10 réplicas
- **Cola Redis**: Desacoplamiento entre producer y consumers
- **Task distribution**: Redis List (LPUSH/RPOP) para FIFO

**Modelo de datos** (`processed_articles`):
```sql
CREATE TABLE processed_articles (
    id SERIAL PRIMARY KEY,
    raw_article_id INTEGER REFERENCES raw_articles(id),
    keywords TEXT[],
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    processed_at TIMESTAMP DEFAULT NOW()
);
```

**HPA Configuration**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
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

**Puerto**: 8002

### 5. Correlation Service

**Propósito**: Calcular correlación de Pearson entre sentimiento de noticias y COLCAP

**Componentes internos**:

#### a. COLCAP Client (`colcap_client.py`)
- Obtención de datos históricos del índice COLCAP
- Normalización de fechas
- Cálculo de variaciones diarias
- Cache en base de datos

#### b. Correlation Engine (`correlation_engine.py`)
- Agregación de artículos por fecha
- Cálculo de sentimiento promedio diario
- Correlación de Pearson (scipy.stats.pearsonr)
- Cálculo de p-value para significancia estadística

**Fórmula de correlación de Pearson**:
```
r = Σ[(xi - x̄)(yi - ȳ)] / √[Σ(xi - x̄)² * Σ(yi - ȳ)²]

Donde:
- xi = sentimiento promedio día i
- yi = variación COLCAP día i
- x̄, ȳ = promedios
- r ∈ [-1, 1]
```

**Modelo de datos** (`correlation_results`):
```sql
CREATE TABLE correlation_results (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(64) UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    correlations JSONB,  -- {metric1: value, metric2: value}
    insights TEXT[],
    sample_size INTEGER,
    p_value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Puerto**: 8003

### 6. PostgreSQL Database

**Propósito**: Persistencia de todos los datos del sistema

**Características**:
- PostgreSQL 15+
- StatefulSet en Kubernetes
- Persistent Volume Claims (PVC) para durabilidad
- Conexiones async con SQLAlchemy

**Schema completo**:
```sql
-- Artículos crudos de Common Crawl
CREATE TABLE raw_articles (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    crawled_at TIMESTAMP,
    source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Artículos procesados
CREATE TABLE processed_articles (
    id SERIAL PRIMARY KEY,
    raw_article_id INTEGER REFERENCES raw_articles(id),
    keywords TEXT[],
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Resultados de correlación
CREATE TABLE correlation_results (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(64) UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    correlations JSONB,
    insights TEXT[],
    sample_size INTEGER,
    p_value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Datos históricos de COLCAP
CREATE TABLE colcap_data (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    close_price FLOAT,
    variation FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Puerto**: 5432

### 7. Redis

**Propósito**: Cola de mensajes y cache

**Uso en el sistema**:
- **Queue**: Lista Redis para tasks de procesamiento de texto
- **Pub/Sub**: Notificaciones entre servicios (futuro)
- **Cache**: Resultados intermedios y sesiones

**Comandos principales usados**:
```python
# Producer (API Gateway)
redis.lpush('text_processing_queue', json.dumps(article))

# Consumer (Text Processor Worker)
task = redis.brpop('text_processing_queue', timeout=5)
```

**Puerto**: 6379

---

## Flujo de datos

### Flujo completo de análisis

```
1. Usuario configura análisis en AnalysisPage
   ↓
2. Frontend envía POST /api/v1/correlation/correlate
   {
     start_date: "2024-01-01",
     end_date: "2024-01-31",
     metrics: ["colcap_variation", "colcap_close"],
     keywords: ["inflación", "dólar", "petróleo"]
   }
   ↓
3. API Gateway proxy → Correlation Service
   ↓
4. Correlation Service:
   a. Obtiene artículos procesados (SELECT * FROM processed_articles WHERE ...)
   b. Obtiene datos COLCAP (SELECT * FROM colcap_data WHERE date BETWEEN ...)
   c. Agrupa artículos por fecha
   d. Calcula correlación de Pearson
   e. Genera insights automáticos
   f. Guarda resultado (INSERT INTO correlation_results)
   ↓
5. Frontend recibe job_id
   ↓
6. Polling cada 2 segundos (GET /api/v1/correlation/results/{job_id})
   ↓
7. Cuando status='completed', muestra resultados
   ↓
8. Usuario descarga PDF con gráficos y tabla
```

### Flujo de procesamiento de texto paralelo

```
1. Data Acquisition obtiene N artículos de Common Crawl
   ↓
2. Inserta en raw_articles (batch INSERT)
   ↓
3. Para cada artículo:
   Redis LPUSH('text_processing_queue', article_data)
   ↓
4. Workers de Text Processor (2-10 pods) compiten por tasks:
   Worker 1 → BRPOP → Procesa artículo A → Inserta processed_article
   Worker 2 → BRPOP → Procesa artículo B → Inserta processed_article
   Worker N → BRPOP → Procesa artículo N → Inserta processed_article
   ↓
5. Procesamiento paralelo real con N workers
   ↓
6. Resultados disponibles en processed_articles
```

**Ejemplo de speedup**:
```
1 worker:  100 artículos en 100 segundos (1 art/s)
5 workers: 100 artículos en 22 segundos (4.5 art/s) → Speedup: 4.5x
10 workers: 100 artículos en 12 segundos (8.3 art/s) → Speedup: 8.3x
```

---

## Estrategias de escalabilidad

### 1. Escalabilidad horizontal (HPA)

**Text Processor Autoscaling**:
```yaml
Métricas:
- CPU > 70% → Scale up (+100% pods cada 60s)
- Memory > 80% → Scale up
- CPU < 50% → Scale down (-50% pods cada 300s)

Ejemplo:
2 pods → 70% CPU → 4 pods (después de 60s)
4 pods → 75% CPU → 8 pods (después de 60s)
8 pods → 30% CPU → 4 pods (después de 300s)
```

### 2. Recursos Kubernetes

**Requests y Limits**:
```yaml
text-processor:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

correlation-service:
  requests:
    cpu: 300m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

### 3. Load Balancing

- **Kubernetes Service**: ClusterIP con round-robin interno
- **AWS ELB**: Load Balancer externo para frontend
- **Redis Queue**: Distribución natural de tareas entre workers

---

## Base de datos

### Modelo ER

```
┌──────────────────┐
│  raw_articles    │
│──────────────────│
│ id (PK)          │
│ url              │
│ title            │
│ content          │
│ crawled_at       │
│ source           │
└────────┬─────────┘
         │ 1
         │
         │ N
┌────────▼─────────────┐
│  processed_articles  │
│──────────────────────│
│ id (PK)              │
│ raw_article_id (FK)  │
│ keywords             │
│ sentiment            │
│ sentiment_score      │
└──────────────────────┘

┌──────────────────────┐
│  correlation_results │
│──────────────────────│
│ id (PK)              │
│ job_id (UNIQUE)      │
│ start_date           │
│ end_date             │
│ correlations (JSONB) │
│ insights             │
│ sample_size          │
│ p_value              │
└──────────────────────┘

┌──────────────┐
│  colcap_data │
│──────────────│
│ id (PK)      │
│ date (UNIQUE)│
│ close_price  │
│ variation    │
└──────────────┘
```

### Optimizaciones

**Índices**:
```sql
CREATE INDEX idx_raw_articles_crawled_at ON raw_articles(crawled_at);
CREATE INDEX idx_processed_articles_processed_at ON processed_articles(processed_at);
CREATE INDEX idx_correlation_results_job_id ON correlation_results(job_id);
CREATE INDEX idx_colcap_data_date ON colcap_data(date);
```

**Connection pooling** (SQLAlchemy):
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

---

## Paralelismo y concurrencia

### 1. Paralelismo de datos

**Text Processor Workers**:
- Cada worker es un proceso Python independiente
- Comparten cola Redis pero procesan artículos diferentes
- No hay estado compartido (stateless workers)
- Escalado horizontal con Kubernetes HPA

### 2. Concurrencia asíncrona

**FastAPI async/await**:
```python
@app.post("/correlate")
async def calculate_correlation(request: CorrelationRequest):
    async with AsyncSessionLocal() as session:
        # I/O-bound operations son non-blocking
        articles = await session.execute(select(ProcessedArticle))
        colcap = await session.execute(select(ColcapData))
    
    # CPU-bound correlation en executor separado
    correlation = await run_in_executor(compute_pearson, articles, colcap)
    return correlation
```

### 3. Modelo de workers

```
Master (API Gateway)
   │
   ├─► Worker 1 (Text Processor Pod 1)
   ├─► Worker 2 (Text Processor Pod 2)
   ├─► Worker 3 (Text Processor Pod 3)
   └─► Worker N (Text Processor Pod N)
   
Cada worker:
- Consume de Redis Queue (BRPOP blocking)
- Procesa artículo de forma independiente
- Escribe resultado a PostgreSQL
- Vuelve a pedir siguiente task
```

---

## Tolerancia a fallos

### 1. Health checks

**Liveness Probes**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8002
  initialDelaySeconds: 10
  periodSeconds: 30
```

**Readiness Probes**:
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8002
  initialDelaySeconds: 5
  periodSeconds: 10
```

### 2. Retry logic

**Redis connection**:
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def connect_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
```

### 3. StatefulSets para bases de datos

- PostgreSQL StatefulSet con PVC persistente
- Redis StatefulSet con configuración RDB/AOF
- Reinicio automático de pods fallidos
- Volúmenes persistentes independientes del ciclo de vida del pod

### 4. Graceful shutdown

```python
@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()
    redis_client.close()
```

---

## Conclusión

La arquitectura de **News2Market** cumple con todos los requisitos de un sistema distribuido moderno:

✅ **Escalabilidad**: HPA automático basado en métricas  
✅ **Paralelismo**: Workers distribuidos con Redis queue  
✅ **Contenedorización**: Docker multi-stage builds  
✅ **Orquestación**: Kubernetes con Deployments y StatefulSets  
✅ **Persistencia**: PostgreSQL con modelo normalizado  
✅ **Tolerancia a fallos**: Health checks, retries, StatefulSets  
✅ **Análisis estadístico**: Correlación de Pearson con scipy  
✅ **Interfaz moderna**: React con TypeScript y visualizaciones

El sistema demuestra la aplicación práctica de conceptos de **Infraestructuras Paralelas y Distribuidas** en un caso de uso real de análisis de datos.
