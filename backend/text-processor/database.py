"""
Database Module for Text Processor - News2Market

Módulo para interacción con PostgreSQL.
Maneja el almacenamiento y recuperación de artículos procesados.

Autor: Equipo News2Market
Versión: 1.0.0
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, JSON, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Construir desde variables individuales si DATABASE_URL no existe
    user = os.getenv('DATABASE_USER', 'user')
    password = os.getenv('DATABASE_PASSWORD', 'password')
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = os.getenv('DATABASE_PORT', '5432')
    name = os.getenv('DATABASE_NAME', 'newsdb')
    DATABASE_URL = f'postgresql://{user}:{password}@{host}:{port}/{name}'

# Crear engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)

# Crear session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# ==================== MODELOS ====================

class ProcessedArticle(Base):
    """Modelo para artículos procesados"""
    __tablename__ = "processed_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, unique=True, index=True, nullable=False)
    cleaned_content = Column(Text)
    word_count = Column(Integer)
    economic_keywords = Column(JSON)  # {"keyword": count}
    sentiment_score = Column(Float)
    entities = Column(JSON)  # Lista de entidades
    processed_at = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "article_id": self.article_id,
            "cleaned_content": self.cleaned_content[:200] + "..." if self.cleaned_content else "",
            "word_count": self.word_count,
            "economic_keywords": self.economic_keywords,
            "sentiment_score": self.sentiment_score,
            "entities": self.entities,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_time_ms": self.processing_time_ms
        }

# ==================== FUNCIONES DE BASE DE DATOS ====================

def init_db():
    """Inicializar base de datos y crear tablas"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas de base de datos creadas/verificadas")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        raise

def check_db_health() -> bool:
    """Verificar conexión a base de datos"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Health check de base de datos falló: {e}")
        return False

def save_processed_article(
    article_id: int,
    cleaned_content: str,
    word_count: int,
    economic_keywords: Dict[str, int],
    sentiment_score: float,
    entities: List[str],
    processing_time_ms: Optional[float] = None
) -> Optional[ProcessedArticle]:
    """
    Guardar o actualizar artículo procesado
    
    Args:
        article_id: ID del artículo original
        cleaned_content: Contenido limpio
        word_count: Número de palabras
        economic_keywords: Dict con keywords y frecuencias
        sentiment_score: Score de sentimiento
        entities: Lista de entidades
        processing_time_ms: Tiempo de procesamiento en ms
        
    Returns:
        ProcessedArticle: Objeto guardado o None si falla
    """
    db = SessionLocal()
    try:
        # Verificar si ya existe
        existing = db.query(ProcessedArticle).filter(
            ProcessedArticle.article_id == article_id
        ).first()
        
        if existing:
            # Actualizar
            existing.cleaned_content = cleaned_content
            existing.word_count = word_count
            existing.economic_keywords = economic_keywords
            existing.sentiment_score = sentiment_score
            existing.entities = entities
            existing.processed_at = datetime.utcnow()
            existing.processing_time_ms = processing_time_ms
            logger.info(f"📝 Artículo {article_id} actualizado")
        else:
            # Crear nuevo
            new_article = ProcessedArticle(
                article_id=article_id,
                cleaned_content=cleaned_content,
                word_count=word_count,
                economic_keywords=economic_keywords,
                sentiment_score=sentiment_score,
                entities=entities,
                processing_time_ms=processing_time_ms
            )
            db.add(new_article)
            logger.info(f"✅ Artículo {article_id} guardado")
            existing = new_article
        
        db.commit()
        db.refresh(existing)
        return existing
        
    except Exception as e:
        logger.error(f"❌ Error guardando artículo {article_id}: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def get_unprocessed_articles(limit: int = 100) -> List[int]:
    """
    Obtener IDs de artículos que aún no han sido procesados
    
    Args:
        limit: Número máximo de artículos a retornar
        
    Returns:
        List[int]: Lista de IDs de artículos sin procesar
    """
    db = SessionLocal()
    try:
        # Obtener artículos que no están en processed_articles
        # (Esta query asume que existe una tabla raw_articles)
        processed_ids = db.query(ProcessedArticle.article_id).all()
        processed_ids = [row[0] for row in processed_ids]
        
        # Por ahora retornamos lista vacía
        # En implementación real, se consultaría raw_articles
        return []
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo artículos sin procesar: {e}")
        return []
    finally:
        db.close()

def get_processing_stats() -> Dict:
    """
    Obtener estadísticas de procesamiento
    
    Returns:
        Dict: Estadísticas de la base de datos
    """
    db = SessionLocal()
    try:
        total_processed = db.query(ProcessedArticle).count()
        
        if total_processed > 0:
            avg_word_count = db.query(
                func.avg(ProcessedArticle.word_count)
            ).scalar() or 0
            
            avg_sentiment = db.query(
                func.avg(ProcessedArticle.sentiment_score)
            ).scalar() or 0
        else:
            avg_word_count = 0
            avg_sentiment = 0
        
        return {
            "total_processed": total_processed,
            "avg_word_count": round(avg_word_count, 2),
            "avg_sentiment": round(avg_sentiment, 3),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return {
            "total_processed": 0,
            "error": str(e)
        }
    finally:
        db.close()

# Importar func para agregaciones
from sqlalchemy import func

if __name__ == "__main__":
    # Testing
    logging.basicConfig(level=logging.INFO)
    logger.info("Inicializando base de datos...")
    init_db()
    logger.info("✅ Base de datos inicializada correctamente")
