from fastapi import FastAPI, HTTPException
import httpx
import os
from pydantic import BaseModel
from typing import Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway", version="1.0.0")

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
            "POST /start-pipeline",
            "GET /health",
            "GET /services"
        ]
    }

@app.get("/health")
async def health_check():
    """Endpoint de salud para verificar que el servicio está vivo"""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/services")
async def list_services():
    """Listar URLs de servicios configurados"""
    return SERVICES

@app.post("/start-pipeline")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)