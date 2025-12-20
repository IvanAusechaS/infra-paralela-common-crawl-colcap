from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Article(BaseModel):
    """Modelo de artículo de noticias"""
    url: str
    title: str
    content: str
    date: str
    language: str = "es"
    source_domain: str
    warc_file: Optional[str] = None
    record_id: Optional[str] = None
    keywords: List[str] = []
    sentiment: Optional[float] = None
    
    class Config:
        from_attributes = True

class FetchRequest(BaseModel):
    """Solicitud de adquisición de datos"""
    start_date: str = Field(..., example="2024-01-01")
    end_date: str = Field(..., example="2024-01-15")
    limit: int = Field(50, example=50)
    keywords: List[str] = []
    domains: List[str] = []

class FetchResponse(BaseModel):
    """Respuesta de adquisición de datos"""
    job_id: str
    status: str
    message: str
    request: Dict
    timestamp: datetime
    
    class Config:
        from_attributes = True