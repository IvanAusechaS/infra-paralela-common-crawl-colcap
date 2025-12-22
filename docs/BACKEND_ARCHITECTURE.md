# Arquitectura del Backend - News2Market

## Visión General

El backend de News2Market está diseñado como una arquitectura de microservicios desplegada en contenedores Docker. La arquitectura sigue principios de separación de responsabilidades, escalabilidad horizontal y alta disponibilidad.

## Stack Tecnológico

- **Framework**: FastAPI (Python 3.11+)
- **Base de datos**: PostgreSQL 15
- **Cache**: Redis 7
- **Contenedorización**: Docker + Docker Compose
- **ORM**: SQLAlchemy (async)
- **Cliente HTTP**: aiohttp, httpx
- **Testing**: pytest

## Arquitectura de Servicios

```
┌─────────────┐
│   Frontend  │
│ (React/Vite)│
└──────┬──────┘
       │
       v
┌─────────────┐
│ API Gateway │ :8000
│   (FastAPI) │
└──────┬──────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       v              v              v              v
┌──────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ Data         │ │ Text        │ │ Correlation  │ │ Mock         │
│ Acquisition  │ │ Processor   │ │ Service      │ │ Services     │
│ :8001        │ │ :8002       │ │ :8003        │ │ :8004        │
└──────┬───────┘ └──────┬──────┘ └──────┬───────┘ └──────────────┘
       │                │               │
       v                v               v
┌──────────────────────────────────────────┐
│        PostgreSQL Database :5432          │
│  (news, correlations, processed_texts)    │
└──────────────────────────────────────────┘
       ^
       │
┌──────┴───────┐
│   Redis      │
│   :6379      │
└──────────────┘
```

## Servicios

### 1. API Gateway (:8000)

**Responsabilidad**: Punto de entrada único para todas las peticiones del frontend. Enruta solicitudes a los microservicios correspondientes.

**Endpoints principales**:
- `GET /api/v1/health` - Health check con estado de todos los servicios
- `GET /api/v1/system/status` - Estado del sistema completo
- `POST /api/v1/correlation/correlate` - Proxy a correlation-service
- `GET /api/v1/correlation/results` - Proxy a correlation-service
- `GET /api/v1/data/news` - Proxy a data-acquisition
- `POST /api/v1/text/process` - Proxy a text-processor

**Tecnologías**:
- FastAPI
- httpx (cliente HTTP asíncrono)
- CORS middleware para frontend

**Variables de entorno**:
```bash
PORT=8000
DATA_ACQUISITION_URL=http://data-acquisition:8001
TEXT_PROCESSOR_URL=http://text-processor:8002
CORRELATION_SERVICE_URL=http://correlation-service:8003
```

**Archivo**: `backend/api-gateway/app.py`

---

### 2. Data Acquisition Service (:8001)

**Responsabilidad**: Obtención de datos de Common Crawl y almacenamiento de noticias extraídas.

**Funcionalidades**:
- Búsqueda de noticias económicas en Common Crawl
- Extracción de metadatos (título, fecha, URL, contenido)
- Filtrado por keywords económicas
- Persistencia en PostgreSQL
- Paginación y búsqueda de noticias

**Endpoints principales**:
- `GET /` - Información del servicio
- `GET /health` - Health check con estado de base de datos
- `POST /search` - Buscar noticias en Common Crawl
- `GET /news` - Listar noticias almacenadas (paginado)
- `GET /news/{news_id}` - Obtener noticia específica

**Modelos de datos**:
```python
class NewsArticle(Base):
    __tablename__ = 'news_articles'
    
    id: int  # Primary key
    title: str
    url: str (unique, indexed)
    content: str
    published_date: datetime
    source: str
    keywords: List[str]  # JSON
    created_at: datetime
```

**Tecnologías**:
- FastAPI
- SQLAlchemy async
- aiohttp (cliente para Common Crawl)
- PostgreSQL

**Variables de entorno**:
```bash
PORT=8001
DATABASE_URL=postgresql+asyncpg://news2market:password@postgres:5432/news2market
COMMONCRAWL_INDEX_URL=https://index.commoncrawl.org/CC-MAIN-2024-10-index
```

**Archivo**: `backend/data-acquisition/app.py`

---

### 3. Text Processor Service (:8002)

**Responsabilidad**: Procesamiento de texto, análisis de sentimiento y extracción de keywords.

**Funcionalidades**:
- Limpieza y normalización de texto
- Análisis de sentimiento (positivo, neutral, negativo)
- Extracción de keywords económicas
- Resumen de contenido
- Procesamiento en batch desde cola Redis

**Endpoints principales**:
- `GET /` - Información del servicio
- `GET /health` - Health check con estado de base de datos y Redis
- `POST /process` - Procesar texto individual
- `POST /process/batch` - Procesar múltiples textos
- `GET /processed/{text_id}` - Obtener texto procesado

**Modelos de datos**:
```python
class ProcessedText(Base):
    __tablename__ = 'processed_texts'
    
    id: int  # Primary key
    news_article_id: int  # Foreign key
    sentiment_score: float  # -1.0 a 1.0
    sentiment_label: str  # 'positive', 'neutral', 'negative'
    keywords_extracted: List[str]  # JSON
    summary: str
    processed_at: datetime
```

**Tecnologías**:
- FastAPI
- SQLAlchemy async
- Redis (cola de procesamiento)
- NLTK / spaCy (procesamiento de lenguaje natural)
- PostgreSQL

**Variables de entorno**:
```bash
PORT=8002
DATABASE_URL=postgresql+asyncpg://news2market:password@postgres:5432/news2market
REDIS_URL=redis://redis:6379/0
```

**Archivo**: `backend/text-processor/app.py`

---

### 4. Correlation Service (:8003)

**Responsabilidad**: Cálculo de correlaciones estadísticas entre métricas noticiosas y el índice COLCAP.

**Funcionalidades**:
- Obtención de datos históricos de COLCAP
- Agregación temporal de métricas (volumen, keywords, sentimiento)
- Cálculo de correlación de Pearson
- Análisis de lag temporal (retraso entre noticias y efecto en mercado)
- Generación de insights estadísticos
- Persistencia de resultados de análisis

**Endpoints principales**:
- `GET /` - Información del servicio
- `GET /health` - Health check con estado de base de datos
- `POST /correlate` - Calcular correlación
- `GET /results` - Listar resultados históricos (paginado)
- `GET /results/{job_id}` - Obtener resultado específico
- `GET /colcap/{start_date}/{end_date}` - Obtener datos de COLCAP

**Modelos de datos**:
```python
class CorrelationResult(Base):
    __tablename__ = 'correlation_results'
    
    id: int  # Primary key
    job_id: str  # Unique identifier (e.g., "corr_20240115_143022")
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    lag_days: int  # Días de retraso aplicados
    correlations: Dict[str, float]  # {"volume": 0.75, "keywords": 0.82, ...}
    p_values: Dict[str, float]  # Significancia estadística
    insights: List[str]  # Insights generados
    sample_size: int  # Número de días analizados
    created_at: datetime
```

**Request model**:
```python
class CorrelationRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    metrics: List[str]  # ["volume", "keywords", "sentiment"]
    lag_days: int = 0  # 0-30 días
```

**Response model**:
```python
class CorrelationResponse(BaseModel):
    job_id: str
    start_date: str
    end_date: str
    correlations: Dict[str, float]
    p_values: Dict[str, float]
    sample_size: int
    insights: List[str]
    colcap_data: List[Dict]  # Preview (primeros 10 días)
    news_metrics: List[Dict]  # Preview
```

**Tecnologías**:
- FastAPI
- SQLAlchemy async
- NumPy, SciPy (cálculo estadístico)
- pandas (manipulación de datos)
- PostgreSQL

**Variables de entorno**:
```bash
PORT=8003
DATABASE_URL=postgresql+asyncpg://news2market:password@postgres:5432/news2market
COLCAP_API_URL=https://api.example.com/colcap  # Placeholder
```

**Archivos**:
- `backend/correlation-service/app.py` - API endpoints
- `backend/correlation-service/database.py` - Modelos y operaciones DB
- `backend/correlation-service/correlation_engine.py` - Lógica de correlación
- `backend/correlation-service/colcap_client.py` - Cliente para datos COLCAP

---

### 5. Mock Services (:8004)

**Responsabilidad**: Servicios mock para desarrollo y testing.

**Funcionalidades**:
- Mock de API de COLCAP con datos sintéticos
- Mock de Common Crawl para pruebas
- Datos de ejemplo para demos

**Endpoint**: `GET /colcap/mock`

**Archivo**: `backend/mock-services/app.py`

---

## Base de Datos (PostgreSQL)

**Puerto**: 5432  
**Nombre**: `news2market`  
**Usuario**: `news2market`

### Schema

**Tablas principales**:

1. **news_articles** - Noticias extraídas de Common Crawl
2. **processed_texts** - Textos procesados con análisis de sentimiento
3. **correlation_results** - Resultados de análisis de correlación

**Relaciones**:
- `processed_texts.news_article_id` → `news_articles.id` (One-to-One)

**Indices**:
- `news_articles.url` (unique)
- `news_articles.published_date` (btree)
- `correlation_results.job_id` (unique)
- `correlation_results.created_at` (btree, desc)

**Script de inicialización**: `backend/init-db.sql`

---

## Cache (Redis)

**Puerto**: 6379

**Uso**:
- Cola de procesamiento de textos (text-processor)
- Cache de resultados de correlación
- Rate limiting

**Claves**:
- `text_queue:*` - Cola de procesamiento
- `correlation_cache:{job_id}` - Cache de resultados
- `rate_limit:{ip}` - Control de tasa

---

## Docker Compose

**Archivo**: `backend/docker-compose.yml`

**Servicios definidos**:
- `api-gateway` - Puerto 8000
- `data-acquisition` - Puerto 8001
- `text-processor` - Puerto 8002
- `correlation-service` - Puerto 8003
- `postgres` - Puerto 5432
- `redis` - Puerto 6379
- `mock-services` - Puerto 8004 (opcional)

**Red**: `news2market-network` (bridge)

**Volúmenes**:
- `postgres-data` - Persistencia de PostgreSQL
- `redis-data` - Persistencia de Redis

**Comandos útiles**:
```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f [service-name]

# Reiniciar un servicio
docker-compose restart [service-name]

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

---

## Patrones de Diseño

### 1. API Gateway Pattern
- Punto de entrada único
- Enrutamiento a microservicios
- Agregación de respuestas
- Autenticación centralizada (futuro)

### 2. Database per Service (parcial)
- Cada servicio tiene sus propias tablas
- Base de datos compartida por simplicidad
- Migración futura a DBs separadas

### 3. Circuit Breaker
- Manejo de fallos en comunicación entre servicios
- Timeouts configurables
- Retry logic

### 4. Health Check Pattern
- Endpoint `/health` en cada servicio
- Monitoreo de dependencias (DB, Redis)
- Estado agregado en API Gateway

---

## Seguridad

### CORS
- Configurado en todos los servicios
- `allow_origins=["*"]` (desarrollo)
- Restrictivo en producción

### Variables de entorno
- Credenciales de DB nunca en código
- `.env` files para desarrollo
- Secrets management en producción

### Validación de entrada
- Pydantic models en todos los endpoints
- Validación de tipos y rangos
- Sanitización de SQL queries (SQLAlchemy)

---

## Monitoreo y Logging

### Logging
- Formato estructurado (JSON)
- Niveles: DEBUG, INFO, WARNING, ERROR
- Timestamps UTC

**Ejemplo**:
```python
logger.info(f"✅ Análisis completado: job_id={job_id}")
logger.error(f"❌ Error en análisis: {error}")
```

### Métricas
- Tiempo de respuesta por endpoint
- Tasa de errores
- Uso de recursos (CPU, memoria)

---

## Escalabilidad

### Horizontal
- Todos los servicios son stateless
- Escalado con Docker replicas
- Load balancing con Nginx (producción)

### Vertical
- PostgreSQL con conexiones pool
- Redis para cache y colas
- Async/await en Python (FastAPI)

---

## Testing

### Unit Tests
- pytest para cada servicio
- Mock de dependencias externas
- Coverage > 80%

### Integration Tests
- Tests de endpoints con TestClient
- Mock de base de datos (SQLite en memoria)

### End-to-End Tests
- Postman collections
- Automated smoke tests

**Comando**:
```bash
pytest backend/tests/ -v --cov
```

---

## Roadmap

- [ ] Autenticación JWT
- [ ] Rate limiting global
- [ ] Logs centralizados (ELK stack)
- [ ] Métricas con Prometheus + Grafana
- [ ] CI/CD con GitHub Actions
- [ ] Deploy en AWS ECS / Kubernetes
- [ ] WebSocket para notificaciones en tiempo real

---

## Contacto

Para preguntas sobre la arquitectura del backend, contactar al equipo de desarrollo.

**Última actualización**: Enero 2025
