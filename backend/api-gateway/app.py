from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from pydantic import BaseModel
from typing import Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración desde variables de entorno
SERVICES = {
    "data": os.getenv("DATA_SERVICE_URL", "http://localhost:8001"),
    "process": os.getenv("PROCESS_SERVICE_URL", "http://localhost:8002"),
    "correlate": os.getenv("CORRELATION_SERVICE_URL", "http://localhost:8003")
}

# Modelo para la petición
class DateRange(BaseModel):
    start_date: str
    end_date: str
    limit: Optional[int] = 100

@app.get("/")
async def root():
    return {
        "message": "API Gateway funcionando",
        "services": SERVICES,
        "endpoints": [
            "GET /",
            "GET /api/v1/health",
            "POST /api/v1/analysis",
            "GET /api/v1/correlation/results"
        ]
    }

@app.get("/api/v1/health")
async def health_check():
    """Endpoint de salud para verificar que el servicio está vivo"""
    services_health = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in SERVICES.items():
            try:
                response = await client.get(f"{url}/health")
                services_health[name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                services_health[name] = "offline"
    
    return {
        "status": "healthy",
        "service": "api-gateway",
        "services": services_health
    }

@app.get("/services")
async def list_services():
    """Listar URLs de servicios configurados"""
    return SERVICES

@app.post("/api/v1/analysis")
async def start_pipeline(date_range: DateRange):
    """
    Iniciar el pipeline completo de procesamiento
    """
    logger.info(f"Iniciando pipeline para {date_range.start_date} - {date_range.end_date}")
    
    results = {
        "data_acquisition": None,
        "text_processing": None,
        "correlation": None,
        "error": None
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Obtener datos (simulado si los servicios no están disponibles)
            try:
                data_response = await client.post(
                    f"{SERVICES['data']}/fetch",
                    json=date_range.dict()
                )
                results["data_acquisition"] = data_response.json()
                logger.info("Adquisición de datos completada")
            except Exception as e:
                logger.warning(f"Servicio de datos no disponible: {e}")
                results["data_acquisition"] = {"status": "simulated", "data": []}
            
            # 2. Procesar texto
            if results["data_acquisition"]:
                try:
                    process_response = await client.post(
                        f"{SERVICES['process']}/process",
                        json=results["data_acquisition"]
                    )
                    results["text_processing"] = process_response.json()
                    logger.info("Procesamiento de texto completado")
                except Exception as e:
                    logger.warning(f"Servicio de procesamiento no disponible: {e}")
                    results["text_processing"] = {"status": "simulated", "processed": []}
            
            # 3. Correlacionar
            if results["text_processing"]:
                try:
                    correlate_response = await client.post(
                        f"{SERVICES['correlate']}/correlate",
                        json=results["text_processing"]
                    )
                    results["correlation"] = correlate_response.json()
                    logger.info("Correlación completada")
                except Exception as e:
                    logger.warning(f"Servicio de correlación no disponible: {e}")
                    results["correlation"] = {"status": "simulated", "correlation": 0.0}
        
        return {
            "success": True,
            "pipeline_id": f"pipe_{date_range.start_date}_{date_range.end_date}",
            "results": results,
            "metadata": {
                "date_range": date_range.dict(),
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        
    except Exception as e:
        logger.error(f"Error en el pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/correlation/results")
async def get_correlation_results(limit: int = 20):
    """Obtener resultados de correlación"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SERVICES['correlate']}/results",
                params={"limit": limit}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo resultados: {e}")
        return {"results": [], "message": "No se pudieron obtener resultados"}

# Proxy routes para correlation service
@app.post("/api/v1/correlation/correlate")
async def proxy_correlate(request: dict):
    """Proxy para calcular correlaciones"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SERVICES['correlate']}/correlate",
                json=request
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error en correlación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/correlation/colcap/{start_date}/{end_date}")
async def proxy_colcap_data(start_date: str, end_date: str):
    """Proxy para datos de COLCAP"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SERVICES['correlate']}/colcap/{start_date}/{end_date}"
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo datos COLCAP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Proxy routes para text processor
@app.get("/api/v1/text-processor/articles")
async def proxy_articles(limit: int = 50):
    """Proxy para obtener artículos procesados"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SERVICES['process']}/articles",
                params={"limit": limit}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo artículos: {e}")
        return []

@app.get("/api/v1/text-processor/stats")
async def proxy_stats():
    """Proxy para estadísticas de procesamiento"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SERVICES['process']}/stats")
            return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        return {}

@app.get("/api/v1/text-processor/workers/active")
async def proxy_active_workers():
    """Proxy para obtener workers activos"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SERVICES['process']}/workers/active")
            return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo workers activos: {e}")
        return {"active_workers": 0, "workers": []}

@app.delete("/api/v1/correlation/results/{job_id}")
async def proxy_delete_result(job_id: str):
    """Proxy para eliminar un resultado de correlación"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(
                f"{SERVICES['correlate']}/results/{job_id}"
            )
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Resultado no encontrado")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Error eliminando resultado: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error eliminando resultado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)