"""
Text Processor Worker Service - News2Market

Este servicio se encarga del procesamiento distribuido de artículos de noticias.
Consume tareas desde una cola Redis, procesa el texto (limpieza, normalización,
extracción de keywords) y almacena los resultados en PostgreSQL.

Características:
- Procesamiento paralelo mediante múltiples workers
- Limpieza y normalización de HTML
- Extracción de keywords económicas
- Análisis de sentimiento básico
- Integración con Redis para distribución de tareas
- Health checks y métricas

Autor: Equipo News2Market
Versión: 1.0.0
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio
import uuid
import socket

# Importar módulos del servicio
from processor import TextProcessor
from database import (
    SessionLocal,
    ProcessedArticle,
    save_processed_article,
    get_unprocessed_articles,
    get_processing_stats,
    init_db,
    check_db_health
)
from queue_client import RedisQueue

# Configurar logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instancia global del procesador de texto
text_processor = TextProcessor()
redis_queue = None

# ID único del worker
WORKER_ID = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
WORKER_HEARTBEAT_KEY = "workers:active"
WORKER_TTL = 30  # Segundos

# Estado del worker
worker_state = {
    "worker_id": WORKER_ID,
    "is_running": False,
    "articles_processed": 0,
    "last_processed_at": None,
    "errors": 0,
    "started_at": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para inicialización y limpieza"""
    global redis_queue
    
    # Startup
    logger.info("🚀 Iniciando Text Processor Service...")
    
    try:
        # Inicializar base de datos
        init_db()
        logger.info("✅ Base de datos inicializada")
        
        # Inicializar Redis
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = os.getenv('REDIS_PORT', '6379')
        redis_url = os.getenv('REDIS_URL', f'redis://{redis_host}:{redis_port}/0')
        redis_queue = RedisQueue(redis_url)
        await redis_queue.connect()
        logger.info("✅ Conexión a Redis establecida")
        
        # Iniciar worker en background
        if os.getenv('AUTO_START_WORKER', 'true').lower() == 'true':
            asyncio.create_task(worker_loop())
            asyncio.create_task(heartbeat_loop())
            logger.info("✅ Worker iniciado automáticamente")
        
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("👋 Apagando Text Processor Service...")
    if redis_queue:
        await redis_queue.disconnect()

# Inicializar FastAPI
app = FastAPI(
    title="Text Processor Service",
    description="Servicio de procesamiento distribuido de texto para News2Market",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELOS ====================

class ArticleInput(BaseModel):
    """Modelo de entrada para procesamiento de un artículo"""
    article_id: int = Field(..., description="ID del artículo en la base de datos")
    content: str = Field(..., description="Contenido HTML del artículo")
    title: Optional[str] = Field(None, description="Título del artículo")
    url: Optional[str] = Field(None, description="URL del artículo")
    published_date: Optional[str] = Field(None, description="Fecha de publicación")
    domain: Optional[str] = Field(None, description="Dominio de origen")

class ArticleOutput(BaseModel):
    """Modelo de salida después del procesamiento"""
    article_id: int
    cleaned_content: str
    word_count: int
    economic_keywords: Dict[str, int]
    sentiment_score: float
    entities: List[str]
    processing_time_ms: float

class BatchProcessRequest(BaseModel):
    """Solicitud para procesamiento en lote"""
    article_ids: List[int] = Field(..., description="Lista de IDs de artículos a procesar")
    priority: Optional[int] = Field(0, description="Prioridad de procesamiento (0-10)")

class WorkerStatus(BaseModel):
    """Estado actual del worker"""
    is_running: bool
    articles_processed: int
    last_processed_at: Optional[str]
    errors: int
    uptime_seconds: float

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "text-processor",
        "version": "1.0.0",
        "status": "running",
        "worker_active": worker_state["is_running"],
        "articles_processed": worker_state["articles_processed"],
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            {"method": "GET", "path": "/", "description": "Información del servicio"},
            {"method": "GET", "path": "/health", "description": "Health check"},
            {"method": "POST", "path": "/process", "description": "Procesar un artículo"},
            {"method": "POST", "path": "/process-batch", "description": "Procesar lote de artículos"},
            {"method": "GET", "path": "/worker/status", "description": "Estado del worker"},
            {"method": "POST", "path": "/worker/start", "description": "Iniciar worker"},
            {"method": "POST", "path": "/worker/stop", "description": "Detener worker"},
            {"method": "GET", "path": "/stats", "description": "Estadísticas de procesamiento"}
        ]
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint para Kubernetes liveness/readiness probes
    """
    # Verificar conexión a base de datos
    db_healthy = check_db_health()
    
    # Verificar conexión a Redis
    redis_healthy = False
    if redis_queue:
        try:
            redis_healthy = await redis_queue.ping()
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
    
    all_healthy = db_healthy and redis_healthy
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "service": "text-processor",
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "worker": "active" if worker_state["is_running"] else "inactive"
        },
        "metrics": {
            "articles_processed": worker_state["articles_processed"],
            "errors": worker_state["errors"]
        }
    }

@app.post("/process", response_model=ArticleOutput)
async def process_article(article: ArticleInput):
    """
    Procesar un único artículo de forma síncrona
    
    Args:
        article: Datos del artículo a procesar
        
    Returns:
        ArticleOutput: Resultado del procesamiento
        
    Raises:
        HTTPException: Si ocurre un error en el procesamiento
    """
    try:
        logger.info(f"📝 Procesando artículo {article.article_id}")
        start_time = datetime.now()
        
        # Procesar el artículo
        result = text_processor.process_article(
            title=article.title,
            content=article.content,
            url=article.url
        )
        
        # Calcular tiempo de procesamiento
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Guardar en base de datos
        save_processed_article(
            article_id=article.article_id,
            cleaned_content=result['cleaned_content'],
            word_count=result['word_count'],
            economic_keywords=result['economic_keywords'],
            sentiment_score=result['sentiment_score'],
            entities=result['entities']
        )
        
        # Actualizar métricas
        worker_state["articles_processed"] += 1
        worker_state["last_processed_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ Artículo {article.article_id} procesado en {processing_time:.2f}ms")
        
        return ArticleOutput(
            article_id=article.article_id,
            cleaned_content=result['cleaned_content'][:500] + "...",  # Truncar para respuesta
            word_count=result['word_count'],
            economic_keywords=result['economic_keywords'],
            sentiment_score=result['sentiment_score'],
            entities=result['entities'],
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Error procesando artículo {article.article_id}: {e}")
        worker_state["errors"] += 1
        raise HTTPException(status_code=500, detail=f"Error procesando artículo: {str(e)}")

@app.post("/process-batch")
async def process_batch(request: BatchProcessRequest, background_tasks: BackgroundTasks):
    """
    Encolar un lote de artículos para procesamiento asíncrono
    
    Args:
        request: Solicitud con lista de IDs de artículos
        background_tasks: FastAPI background tasks
        
    Returns:
        dict: Información del lote encolado
    """
    try:
        if not redis_queue:
            raise HTTPException(status_code=503, detail="Redis no disponible")
        
        job_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Encolar cada artículo
        enqueued = 0
        for article_id in request.article_ids:
            task = {
                "job_id": job_id,
                "article_id": article_id,
                "priority": request.priority,
                "created_at": datetime.now().isoformat()
            }
            await redis_queue.enqueue_task(task)
            enqueued += 1
        
        logger.info(f"📦 Lote {job_id}: {enqueued} artículos encolados")
        
        return {
            "job_id": job_id,
            "articles_enqueued": enqueued,
            "status": "queued",
            "message": f"{enqueued} artículos encolados para procesamiento"
        }
        
    except Exception as e:
        logger.error(f"❌ Error encolando lote: {e}")
        raise HTTPException(status_code=500, detail=f"Error encolando lote: {str(e)}")

@app.get("/worker/status", response_model=WorkerStatus)
async def get_worker_status():
    """Obtener estado actual del worker"""
    return WorkerStatus(
        is_running=worker_state["is_running"],
        articles_processed=worker_state["articles_processed"],
        last_processed_at=worker_state["last_processed_at"],
        errors=worker_state["errors"],
        uptime_seconds=0.0  # TODO: Implementar tracking de uptime
    )

@app.post("/worker/start")
async def start_worker():
    """Iniciar el worker manualmente"""
    if worker_state["is_running"]:
        return {"message": "Worker ya está en ejecución", "status": "running"}
    
    asyncio.create_task(worker_loop())
    return {"message": "Worker iniciado", "status": "started"}

@app.post("/worker/stop")
async def stop_worker():
    """Detener el worker manualmente"""
    worker_state["is_running"] = False
    return {"message": "Worker detenido", "status": "stopped"}

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas de procesamiento desde la base de datos"""
    try:
        stats = get_processing_stats()
        return {
            "database_stats": stats,
            "worker_stats": {
                "articles_processed_session": worker_state["articles_processed"],
                "errors_session": worker_state["errors"],
                "last_processed_at": worker_state["last_processed_at"]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.get("/workers/active")
async def get_active_workers():
    """
    Obtener lista de workers activos
    """
    try:
        if not redis_queue or not redis_queue.client:
            return {"active_workers": 0, "workers": []}
        
        import json
        # Obtener todos los workers activos del hash
        workers_data = await redis_queue.client.hgetall(WORKER_HEARTBEAT_KEY)
        
        active_workers = []
        for worker_id, data_json in workers_data.items():
            try:
                worker_info = json.loads(data_json)
                active_workers.append(worker_info)
            except:
                continue
        
        return {
            "active_workers": len(active_workers),
            "workers": active_workers,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo workers activos: {e}")
        return {"active_workers": 0, "workers": []}

# ==================== WORKER LOOP ====================

async def heartbeat_loop():
    """
    Loop para enviar heartbeat a Redis y registrar este worker como activo
    """
    logger.info(f"💓 Heartbeat loop iniciado para worker {WORKER_ID}")
    
    while worker_state["is_running"] or True:  # Siempre activo mientras el servicio corra
        try:
            if redis_queue and redis_queue.client:
                import json
                worker_info = {
                    "worker_id": WORKER_ID,
                    "hostname": socket.gethostname(),
                    "articles_processed": worker_state["articles_processed"],
                    "last_heartbeat": datetime.now().isoformat(),
                    "started_at": worker_state.get("started_at") or datetime.now().isoformat(),
                    "is_running": worker_state["is_running"],
                    "errors": worker_state["errors"]
                }
                
                # Registrar en Redis con TTL
                await redis_queue.client.hset(
                    WORKER_HEARTBEAT_KEY,
                    WORKER_ID,
                    json.dumps(worker_info)
                )
                
                # Establecer TTL en el campo del worker
                await redis_queue.client.expire(WORKER_HEARTBEAT_KEY, WORKER_TTL + 10)
                
                logger.debug(f"💓 Heartbeat enviado: {WORKER_ID}")
        except Exception as e:
            logger.error(f"Error en heartbeat: {e}")
        
        # Enviar heartbeat cada 10 segundos
        await asyncio.sleep(10)

async def worker_loop():
    """
    Loop principal del worker que consume tareas de la cola Redis
    y procesa artículos de forma continua
    """
    worker_state["is_running"] = True
    worker_state["started_at"] = datetime.now().isoformat()
    logger.info(f"🔄 Worker loop iniciado: {WORKER_ID}")
    
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while worker_state["is_running"]:
        try:
            # Intentar obtener tarea de la cola
            task = await redis_queue.dequeue_task(timeout=5)
            
            if task:
                consecutive_errors = 0  # Resetear contador de errores
                
                article_id = task.get('article_id')
                logger.info(f"🔍 Worker procesando artículo {article_id}")
                
                try:
                    # Obtener artículo de la base de datos
                    db = SessionLocal()
                    article = db.query(ProcessedArticle).filter(
                        ProcessedArticle.article_id == article_id
                    ).first()
                    
                    if article and not article.processed_at:
                        # Procesar artículo
                        # (Aquí se debería obtener el contenido original de raw_articles)
                        # Por ahora simulamos procesamiento
                        result = text_processor.process_article(
                            title="Sample",
                            content="Sample content",
                            url="http://example.com"
                        )
                        
                        # Guardar resultado
                        save_processed_article(
                            article_id=article_id,
                            cleaned_content=result['cleaned_content'],
                            word_count=result['word_count'],
                            economic_keywords=result['economic_keywords'],
                            sentiment_score=result['sentiment_score'],
                            entities=result['entities']
                        )
                        
                        worker_state["articles_processed"] += 1
                        worker_state["last_processed_at"] = datetime.now().isoformat()
                        
                        logger.info(f"✅ Artículo {article_id} procesado correctamente")
                    
                    db.close()
                    
                except Exception as e:
                    logger.error(f"❌ Error procesando tarea: {e}")
                    worker_state["errors"] += 1
                    # Reencolar la tarea con prioridad menor
                    task['retry_count'] = task.get('retry_count', 0) + 1
                    if task['retry_count'] < 3:
                        await redis_queue.enqueue_task(task)
            else:
                # No hay tareas, esperar un poco
                await asyncio.sleep(1)
                
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ Error en worker loop: {e}")
            worker_state["errors"] += 1
            
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"⚠️ Demasiados errores consecutivos ({consecutive_errors}). Pausando worker...")
                await asyncio.sleep(10)
                consecutive_errors = 0
            else:
                await asyncio.sleep(2)
    
    logger.info("🛑 Worker loop detenido")

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv('PORT', 8002))
    host = os.getenv('HOST', '0.0.0.0')
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv('ENV', 'production') == 'development'
    )
