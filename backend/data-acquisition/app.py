from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging
from datetime import datetime
import asyncio
import json
import os
from contextlib import asynccontextmanager

from commoncrawl_client import CommonCrawlClient
from database import SessionLocal, NewsArticle, save_articles, get_articles, get_stats
from models import FetchRequest, FetchResponse, Article

from database import init_db

# Configurar logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache en memoria (para producción usar Redis)
fetch_cache = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Iniciando Data Acquisition Service...")
    try:
        init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
    yield
    # Shutdown
    logger.info("👋 Apagando Data Acquisition Service...")

app = FastAPI(
    title="Data Acquisition Service",
    description="Servicio para adquirir datos de Common Crawl - Proyecto Infraestructuras Paralelas",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

class DateRange(BaseModel):
    start_date: str = Field(..., example="2024-01-01")
    end_date: str = Field(..., example="2024-01-15")
    limit: Optional[int] = Field(50, example=50)
    keywords: Optional[List[str]] = Field([], example=["colombia", "economía"])
    domains: Optional[List[str]] = Field([], example=[".co", "eltiempo.com"])

# ===== ENDPOINTS PRINCIPALES =====

@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "data-acquisition",
        "version": "2.0.0",
        "status": "running",
        "mode": os.getenv('USE_MOCK_MODE', 'true'),
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            {"method": "GET", "path": "/", "description": "Información del servicio"},
            {"method": "GET", "path": "/health", "description": "Verificar salud del servicio"},
            {"method": "GET", "path": "/info", "description": "Información detallada"},
            {"method": "GET", "path": "/crawls", "description": "Listar crawls disponibles"},
            {"method": "POST", "path": "/fetch", "description": "Iniciar adquisición (async)"},
            {"method": "POST", "path": "/fetch-sync", "description": "Adquisición síncrona (pruebas)"},
            {"method": "POST", "path": "/fetch-safe", "description": "Adquisición segura (con fallback)"},
            {"method": "GET", "path": "/status/{job_id}", "description": "Estado de un job"},
            {"method": "GET", "path": "/articles", "description": "Obtener artículos almacenados"},
            {"method": "GET", "path": "/db/stats", "description": "Estadísticas de la BD"},
            {"method": "GET", "path": "/test/connection", "description": "Probar conexión a Common Crawl"},
            {"method": "GET", "path": "/test/mock-data", "description": "Obtener datos mock"}
        ]
    }

@app.get("/health")
async def health_check():
    """Verificar salud del servicio"""
    # Verificar conexión a BD
    db_status = "unknown"
    try:
        session = SessionLocal()
        session.execute("SELECT 1")
        session.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Error verificación BD: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "data-acquisition",
        "database": db_status,
        "mode": os.getenv('USE_MOCK_MODE', 'true'),
        "version": "2.0.0"
    }

@app.get("/info")
async def service_info():
    """Información detallada del servicio"""
    use_mock = os.getenv('USE_MOCK_MODE', 'true').lower() == 'true'
    
    # Probar conexión a Common Crawl
    connection_test = {"status": "not_tested"}
    if not use_mock:
        try:
            async with CommonCrawlClient(use_s3_direct=False, mode="auto") as client:
                connection_test = await client.test_connection()
        except Exception as e:
            connection_test = {"error": str(e)}
    
    return {
        "service": "data-acquisition",
        "version": "2.0.0",
        "environment": os.getenv('ENV', 'development'),
        "mode": "MOCK" if use_mock else "REAL",
        "database_url": os.getenv('DATABASE_URL', 'not_set').split('@')[-1] if '@' in os.getenv('DATABASE_URL', '') else 'not_set',
        "common_crawl_config": {
            "bucket": os.getenv('COMMON_CRAWL_BUCKET', 'commoncrawl'),
            "region": os.getenv('COMMON_CRAWL_REGION', 'us-east-1'),
            "use_s3_direct": os.getenv('COMMON_CRAWL_USE_S3', 'false'),
            "base_url": "https://data.commoncrawl.org"  # Usamos este por defecto ahora
        },
        "limits": {
            "max_records": os.getenv('MAX_TOTAL_RECORDS', '50'),
            "max_warc_files": os.getenv('MAX_WARC_FILES', '3')
        },
        "connection_test": connection_test,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/crawls")
async def list_crawls():
    """Listar crawls disponibles de Common Crawl"""
    use_mock = os.getenv('USE_MOCK_MODE', 'true').lower() == 'true'
    
    if use_mock:
        # Datos mock para desarrollo
        crawls = [
            {"id": "CC-MAIN-2024-10", "date": "2024-05-2024-06", "size": "280TB", "status": "mock"},
            {"id": "CC-MAIN-2024-05", "date": "2024-03-2024-04", "size": "250TB", "status": "mock"},
            {"id": "CC-MAIN-2023-50", "date": "2023-12-2024-01", "size": "270TB", "status": "mock"}
        ]
    else:
        # Datos reales
        async with CommonCrawlClient(use_s3_direct=False, mode="auto") as client:
            crawls = client.get_available_crawls()
    
    return {
        "crawls": crawls,
        "count": len(crawls),
        "mode": "MOCK" if use_mock else "REAL",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/fetch", response_model=FetchResponse)
async def fetch_news(
    request: DateRange,
    background_tasks: BackgroundTasks
):
    """
    Iniciar proceso de adquisición de noticias (asíncrono)
    """
    job_id = f"fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"🚀 Iniciando job {job_id} para {request.start_date} - {request.end_date}")
    
    # Iniciar en background
    background_tasks.add_task(
        process_fetch_request,
        job_id=job_id,
        request=request
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Proceso de adquisición iniciado. ID: {job_id}",
        "request": request.dict(),
        "timestamp": datetime.now().isoformat(),
        "mode": os.getenv('USE_MOCK_MODE', 'true')
    }

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Obtener estado de un job de adquisición"""
    if job_id in fetch_cache:
        return {
            "job_id": job_id,
            **fetch_cache[job_id]
        }
    else:
        raise HTTPException(
            status_code=404, 
            detail=f"Job {job_id} no encontrado. Puede haber expirado (se mantienen por 1 hora)."
        )

@app.post("/fetch-sync")
async def fetch_news_sync(request: DateRange):
    """
    Versión síncrona para pruebas (no usar en producción para grandes volúmenes)
    """
    logger.info(f"🔍 Fetch síncrono para {request.start_date} - {request.end_date}")
    
    use_mock = os.getenv('USE_MOCK_MODE', 'true').lower() == 'true'
    
    try:
        if use_mock:
            logger.info("📋 Usando modo MOCK para fetch-sync")
            async with CommonCrawlClient() as client:
                articles = client._get_mock_news_data(
                    request.start_date,
                    request.end_date,
                    request.limit
                )
        else:
            logger.info("🌐 Usando modo REAL para fetch-sync")
            async with CommonCrawlClient(use_s3_direct=False, mode="auto") as client:
                articles = await client.search_news_by_date(
                    start_date=request.start_date,
                    end_date=request.end_date,
                    max_records=min(request.limit, 100)  # Límite seguro
                )
        
        # Guardar en base de datos
        saved_count = save_articles(articles) if articles else 0
        
        return {
            "status": "success",
            "mode": "MOCK" if use_mock else "REAL",
            "articles_found": len(articles) if articles else 0,
            "articles_saved": saved_count,
            "sample": articles[:3] if articles else [],
            "request": request.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en fetch síncrono: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "message": "Intenta usar /fetch-safe para modo con fallback automático"
            }
        )

@app.post("/fetch-safe")
async def fetch_safe(request: DateRange):
    """
    Versión segura que usa mock si falla la conexión real
    """
    use_mock_env = os.getenv('USE_MOCK_MODE', 'true').lower() == 'true'
    actual_mode = "MOCK"
    
    if use_mock_env:
        logger.info("🛠️  Usando modo MOCK (configurado por variable)")
        
        # Generar datos mock
        async with CommonCrawlClient() as client:
            articles = client._get_mock_news_data(
                request.start_date, 
                request.end_date, 
                min(request.limit, 50)
            )
    else:
        # Intentar con conexión real
        try:
            logger.info("🌐 Intentando conexión REAL a Common Crawl...")
            async with CommonCrawlClient(use_s3_direct=False, mode="auto") as client:
                articles = await client.search_news_by_date(
                    start_date=request.start_date,
                    end_date=request.end_date,
                    max_records=min(request.limit, 50)
                )
                
                actual_mode = "REAL"
                logger.info(f"✅ Modo REAL: {len(articles) if articles else 0} artículos encontrados")
                
                if not articles or len(articles) == 0:
                    logger.warning("⚠️  No se obtuvieron artículos en modo REAL, usando MOCK")
                    articles = client._get_mock_news_data(
                        request.start_date, 
                        request.end_date, 
                        min(request.limit, 50)
                    )
                    actual_mode = "MOCK (fallback)"
                    
        except Exception as e:
            logger.error(f"❌ Error en modo REAL: {e}, usando MOCK")
            async with CommonCrawlClient() as client:
                articles = client._get_mock_news_data(
                    request.start_date, 
                    request.end_date, 
                    min(request.limit, 50)
                )
            actual_mode = "MOCK (error fallback)"
    
    # Guardar en BD
    saved_count = save_articles(articles) if articles else 0
    
    return {
        "status": "success",
        "mode": actual_mode,
        "articles_found": len(articles) if articles else 0,
        "articles_saved": saved_count,
        "sample": articles[:3] if articles else [],
        "request": request.dict(),
        "timestamp": datetime.now().isoformat(),
        "recommendation": "Usa /fetch-sync para solo REAL o /fetch para async"
    }

@app.get("/articles")
async def get_articles_endpoint(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    domain: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Obtener artículos almacenados de la base de datos"""
    try:
        articles = get_articles(
            limit=limit, 
            offset=offset, 
            domain=domain, 
            keyword=keyword,
            start_date=start_date,
            end_date=end_date
        )
        
        # Obtener estadísticas
        from database import SessionLocal, func
        session = SessionLocal()
        total_count = session.query(func.count(NewsArticle.id)).scalar()
        session.close()
        
        return {
            "articles": articles,
            "metadata": {
                "count": len(articles),
                "total_in_db": total_count,
                "limit": limit,
                "offset": offset,
                "filters": {
                    "domain": domain,
                    "keyword": keyword,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo artículos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/stats")
async def get_database_stats():
    """Obtener estadísticas de la base de datos"""
    try:
        stats = get_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/test-connection")
async def test_database_connection():
    """Probar conexión a la base de datos"""
    from sqlalchemy import text
    from database import SessionLocal
    
    session = SessionLocal()
    try:
        # Ejecutar query simple
        result = session.execute(text("SELECT 1 as test, current_timestamp as timestamp, version() as version"))
        row = result.fetchone()
        
        # Verificar tablas
        table_count = session.execute(
            text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'commoncrawl'
            """)
        ).scalar()
        
        # Verificar tablas específicas
        tables = session.execute(
            text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'commoncrawl'
            ORDER BY table_name
            """)
        ).fetchall()
        
        return {
            "status": "connected",
            "database": "postgresql",
            "test_query": "success",
            "server_time": str(row.timestamp),
            "postgres_version": row.version.split(',')[0],
            "tables_in_schema": table_count,
            "table_list": [t[0] for t in tables],
            "connection_url": os.getenv("DATABASE_URL", "not set").split('@')[-1] if '@' in os.getenv("DATABASE_URL", "") else "not set"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "connection_url": os.getenv("DATABASE_URL", "not set")
        }
    finally:
        session.close()

# ===== ENDPOINTS DE PRUEBA Y DIAGNÓSTICO =====

@app.get("/test/connection")
async def test_commoncrawl_connection():
    """Probar conexión a Common Crawl"""
    use_mock = os.getenv('USE_MOCK_MODE', 'true').lower() == 'true'
    
    if use_mock:
        return {
            "status": "mock_mode",
            "message": "Servicio en modo MOCK. Cambia USE_MOCK_MODE=false para probar conexión real.",
            "accessible": True,
            "mode": "MOCK"
        }
    
    try:
        async with CommonCrawlClient(use_s3_direct=False, mode="auto") as client:
            results = await client.test_connection()
            
            # Determinar el mejor método
            best_method = None
            best_url = None
            for url, data in results.items():
                if data.get('accessible'):
                    best_method = url.split('/')[2]  # Extraer dominio
                    best_url = url
                    break
            
            return {
                "status": "tested",
                "results": results,
                "best_method": best_method,
                "best_url": best_url,
                "recommendation": f"Usar {best_method}" if best_method else "Usar modo MOCK",
                "mode": "REAL"
            }
            
    except Exception as e:
        logger.error(f"Error en test de conexión: {e}")
        return {
            "status": "error",
            "error": str(e),
            "recommendation": "Usar modo MOCK (USE_MOCK_MODE=true)",
            "mode": "ERROR"
        }

@app.get("/test/mock-data")
async def get_mock_data(
    limit: int = Query(5, ge=1, le=20),
    start_date: Optional[str] = "2024-01-01",
    end_date: Optional[str] = "2024-01-10"
):
    """Endpoint para obtener datos mock de prueba"""
    async with CommonCrawlClient() as client:
        articles = client._get_mock_news_data(
            start_date or "2024-01-01",
            end_date or "2024-01-10",
            limit
        )
    
    return {
        "status": "success",
        "source": "mock",
        "count": len(articles),
        "data": articles,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test/all-methods")
async def test_all_methods():
    """Probar todos los métodos de acceso a Common Crawl"""
    methods = [
        {"name": "data.commoncrawl.org", "url": "https://data.commoncrawl.org/crawl-data/CC-MAIN-2024-10/warc.paths.gz"},
        {"name": "S3 Direct", "url": "https://commoncrawl.s3.amazonaws.com/crawl-data/CC-MAIN-2024-10/warc.paths.gz"},
        {"name": "CloudFront", "url": "https://ds5q9oxwqwsfj.cloudfront.net/crawl-data/CC-MAIN-2024-10/warc.paths.gz"}
    ]
    
    import requests
    results = []
    
    for method in methods:
        try:
            response = requests.head(method["url"], timeout=10)
            results.append({
                "method": method["name"],
                "url": method["url"],
                "status": response.status_code,
                "accessible": response.status_code == 200
            })
        except Exception as e:
            results.append({
                "method": method["name"],
                "url": method["url"],
                "status": "error",
                "accessible": False,
                "error": str(e)
            })
    
    # Determinar recomendación
    accessible_methods = [r for r in results if r["accessible"]]
    
    return {
        "results": results,
        "summary": {
            "total_tested": len(results),
            "accessible": len(accessible_methods),
            "recommended_method": accessible_methods[0]["method"] if accessible_methods else "MOCK"
        }
    }

# ===== FUNCIONES DE BACKGROUND =====

async def process_fetch_request(job_id: str, request: DateRange):
    """Procesar solicitud de adquisición en background"""
    
    fetch_cache[job_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Iniciando descarga...",
        "articles_found": 0,
        "articles_saved": 0,
        "start_time": datetime.now().isoformat(),
        "last_update": datetime.now().isoformat(),
        "mode": os.getenv('USE_MOCK_MODE', 'true')
    }
    
    try:
        use_mock = os.getenv('USE_MOCK_MODE', 'true').lower() == 'true'
        
        if use_mock:
            fetch_cache[job_id].update({
                "progress": 30,
                "message": "Modo MOCK: Generando datos de prueba...",
                "mode": "MOCK"
            })
            
            async with CommonCrawlClient() as client:
                articles = client._get_mock_news_data(
                    request.start_date,
                    request.end_date,
                    request.limit
                )
        else:
            fetch_cache[job_id].update({
                "progress": 20,
                "message": "Conectando a Common Crawl...",
                "mode": "REAL"
            })
            
            async with CommonCrawlClient(use_s3_direct=False, mode="auto") as client:
                fetch_cache[job_id].update({
                    "progress": 40,
                    "message": "Buscando archivos WARC..."
                })
                
                articles = await client.search_news_by_date(
                    start_date=request.start_date,
                    end_date=request.end_date,
                    max_records=request.limit
                )
        
        fetch_cache[job_id].update({
            "progress": 60,
            "message": f"Encontrados {len(articles) if articles else 0} artículos. Guardando...",
            "articles_found": len(articles) if articles else 0
        })
        
        # Guardar en base de datos
        saved_count = save_articles(articles) if articles else 0
        
        fetch_cache[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Completado. Guardados {saved_count} artículos.",
            "articles_saved": saved_count,
            "end_time": datetime.now().isoformat(),
            "sample_articles": articles[:3] if articles else []
        })
        
        # Limpiar cache antiguo (mantener solo últimos 10 jobs por 1 hora)
        cleanup_old_jobs()
            
    except Exception as e:
        logger.error(f"❌ Error procesando job {job_id}: {e}")
        fetch_cache[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Error: {str(e)[:200]}",
            "end_time": datetime.now().isoformat()
        })

def cleanup_old_jobs():
    """Limpiar jobs antiguos del cache"""
    try:
        current_time = datetime.now()
        jobs_to_delete = []
        
        for job_id, job_data in fetch_cache.items():
            if 'start_time' in job_data:
                start_time = datetime.fromisoformat(job_data['start_time'].replace('Z', '+00:00'))
                # Eliminar jobs con más de 1 hora
                if (current_time - start_time).total_seconds() > 3600:
                    jobs_to_delete.append(job_id)
        
        for job_id in jobs_to_delete:
            del fetch_cache[job_id]
            
        if jobs_to_delete:
            logger.info(f"🧹 Limpiados {len(jobs_to_delete)} jobs antiguos del cache")
            
    except Exception as e:
        logger.debug(f"Error limpiando cache: {e}")

# ===== ENDPOINT PARA LISTAR JOBS ACTIVOS =====

@app.get("/jobs")
async def list_active_jobs():
    """Listar jobs activos en el cache"""
    active_jobs = []
    
    for job_id, job_data in fetch_cache.items():
        if job_data.get('status') in ['processing', 'started']:
            # Calcular tiempo transcurrido
            if 'start_time' in job_data:
                start_time = datetime.fromisoformat(job_data['start_time'].replace('Z', '+00:00'))
                elapsed = (datetime.now() - start_time).total_seconds()
                job_data['elapsed_seconds'] = round(elapsed, 1)
            
            active_jobs.append({
                "job_id": job_id,
                **job_data
            })
    
    return {
        "active_jobs": active_jobs,
        "total_active": len(active_jobs),
        "total_in_cache": len(fetch_cache),
        "timestamp": datetime.now().isoformat()
    }

# ===== MANEJO DE ERRORES GLOBAL =====

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Error no manejado en {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "message": str(exc),
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8001))
    
    logger.info(f"🚀 Iniciando servidor en {host}:{port}")
    logger.info(f"🔧 Modo: {os.getenv('USE_MOCK_MODE', 'true')}")
    logger.info(f"🌐 Entorno: {os.getenv('ENV', 'development')}")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info"
    )