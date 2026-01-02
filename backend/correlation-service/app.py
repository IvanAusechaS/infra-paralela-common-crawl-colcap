"""
Correlation Service - News2Market

Servicio para calcular correlaciones entre métricas noticiosas y el índice COLCAP.
Implementa análisis estadístico usando correlación de Pearson.

Características:
- Obtención de datos históricos de COLCAP
- Agregación temporal de métricas noticiosas
- Cálculo de correlación de Pearson
- Análisis de lag temporal
- Generación de insights y visualizaciones

Autor: Equipo News2Market
Versión: 1.0.0
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy import select
import logging
import os

# Importar módulos del servicio
from colcap_client import ColcapClient
from correlation_engine import CorrelationEngine
from database import (
    AsyncSessionLocal,
    CorrelationResult,
    save_correlation_result,
    get_correlation_result,
    list_correlation_results,
    init_database,
    get_db_session
)

# Configurar logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instancias globales
colcap_client = ColcapClient()
correlation_engine = CorrelationEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager"""
    logger.info("🚀 Iniciando Correlation Service...")
    
    try:
        await init_database()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
    
    yield
    
    logger.info("👋 Apagando Correlation Service...")

# Inicializar FastAPI
app = FastAPI(
    title="Correlation Service",
    description="Servicio de análisis de correlación entre noticias y COLCAP",
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

class DateRange(BaseModel):
    """Rango de fechas para análisis"""
    start_date: str = Field(..., description="Fecha inicio (YYYY-MM-DD)")
    end_date: str = Field(..., description="Fecha fin (YYYY-MM-DD)")

class CorrelationRequest(BaseModel):
    """Solicitud de análisis de correlación"""
    start_date: str
    end_date: str
    metrics: List[str] = Field(
        default=["volume", "keywords", "sentiment"],
        description="Métricas a correlacionar"
    )
    lag_days: Optional[int] = Field(
        default=0,
        description="Días de retraso para análisis temporal"
    )

class CorrelationResponse(BaseModel):
    """Respuesta con resultados de correlación"""
    job_id: str
    start_date: str
    end_date: str
    correlations: Dict[str, float]
    p_values: Dict[str, float]
    sample_size: int
    insights: List[str]
    colcap_data: List[Dict[str, Any]]
    news_metrics: List[Dict[str, Any]]

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "correlation-service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            {"method": "GET", "path": "/", "description": "Información del servicio"},
            {"method": "GET", "path": "/health", "description": "Health check"},
            {"method": "POST", "path": "/correlate", "description": "Calcular correlación"},
            {"method": "GET", "path": "/colcap/{start_date}/{end_date}", "description": "Obtener datos COLCAP"},
            {"method": "GET", "path": "/results", "description": "Listar resultados"},
            {"method": "GET", "path": "/results/{job_id}", "description": "Obtener resultado específico"}
        ]
    }

@app.get("/health")
async def health_check():
    """Health check"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "service": "correlation-service",
        "database": "healthy" if db_healthy else "unhealthy"
    }

@app.post("/correlate", response_model=CorrelationResponse)
async def calculate_correlation(request: CorrelationRequest):
    """
    Calcular correlación entre métricas noticiosas y COLCAP
    
    Args:
        request: Parámetros de la correlación
        
    Returns:
        CorrelationResponse: Resultados del análisis
    """
    try:
        logger.info(f"📊 Iniciando análisis de correlación: {request.start_date} a {request.end_date}")
        
        job_id = f"corr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 1. Obtener datos de COLCAP
        colcap_data = await colcap_client.get_historical_data(
            request.start_date,
            request.end_date
        )
        
        if not colcap_data:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron datos de COLCAP para el período especificado"
            )
        
        logger.info(f"✅ Obtenidos {len(colcap_data)} días de datos COLCAP")
        
        # 2. Obtener métricas noticiosas de la base de datos
        news_metrics = correlation_engine.get_news_metrics(
            request.start_date,
            request.end_date
        )
        
        logger.info(f"✅ Obtenidas métricas de {len(news_metrics)} días de noticias")
        
        # 3. Calcular correlaciones
        correlations = {}
        p_values = {}
        
        for metric in request.metrics:
            corr, p_value = correlation_engine.calculate_pearson_correlation(
                colcap_data=colcap_data,
                news_metrics=news_metrics,
                metric_name=metric,
                lag_days=request.lag_days
            )
            correlations[metric] = corr
            p_values[metric] = p_value
        
        logger.info(f"✅ Correlaciones calculadas: {correlations}")
        
        # 4. Generar insights
        insights = correlation_engine.generate_insights(
            correlations=correlations,
            p_values=p_values,
            sample_size=len(colcap_data)
        )
        
        # 5. Guardar resultados en base de datos
        await save_correlation_result(
            job_id=job_id,
            start_date=request.start_date,
            end_date=request.end_date,
            correlations=correlations,
            p_values=p_values,
            sample_size=len(colcap_data),
            insights=insights,
            lag_days=request.lag_days
        )
        
        logger.info(f"✅ Análisis completado: job_id={job_id}")
        
        return CorrelationResponse(
            job_id=job_id,
            start_date=request.start_date,
            end_date=request.end_date,
            correlations=correlations,
            p_values=p_values,
            sample_size=len(colcap_data),
            insights=insights,
            colcap_data=colcap_data[:10],  # Primeros 10 días para preview
            news_metrics=news_metrics[:10]
        )
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de correlación: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/colcap/{start_date}/{end_date}")
async def get_colcap_data(start_date: str, end_date: str):
    """
    Obtener datos históricos de COLCAP
    
    Args:
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        
    Returns:
        List[Dict]: Datos de COLCAP
    """
    try:
        data = await colcap_client.get_historical_data(start_date, end_date)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "data_points": len(data),
            "data": data
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos COLCAP: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/results")
async def list_results(limit: int = 10, offset: int = 0):
    """Listar resultados de correlación"""
    try:
        all_results = await list_correlation_results(limit=limit + offset)
        results = all_results[offset:]
        
        return {
            "total": len(results),
            "limit": limit,
            "offset": offset,
            "results": [r.to_dict() for r in results]
        }
        
    except Exception as e:
        logger.error(f"❌ Error listando resultados: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/results/{job_id}")
async def get_result(job_id: str):
    """Obtener resultado específico"""
    try:
        result = await get_correlation_result(job_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Resultado no encontrado")
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo resultado: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/results/{job_id}")
async def delete_result(job_id: str):
    """Eliminar resultado específico"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CorrelationResult).where(CorrelationResult.job_id == job_id)
            )
            correlation_result = result.scalar_one_or_none()
            
            if not correlation_result:
                raise HTTPException(status_code=404, detail="Resultado no encontrado")
            
            await session.delete(correlation_result)
            await session.commit()
            
            logger.info(f"✅ Resultado eliminado: {job_id}")
            return {"message": "Resultado eliminado exitosamente", "job_id": job_id}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando resultado: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv('PORT', 8003))
    host = os.getenv('HOST', '0.0.0.0')
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv('ENV', 'production') == 'development'
    )
