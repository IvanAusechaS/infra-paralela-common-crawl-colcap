import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Boolean, Float, JSON, Date, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func

ENV = os.getenv("ENV", "development")

logger = logging.getLogger(__name__)

# Configuración de base de datos PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:admin123@localhost:5432/newsdb"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Cambia a True para ver queries SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class NewsArticle(Base):
    """Modelo de tabla para artículos de noticias"""
    __tablename__ = "news_articles"
    __table_args__ = {'schema': 'commoncrawl'}
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1000), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64))
    date = Column(Date, nullable=False, index=True)
    language = Column(String(10), default='es')
    source_domain = Column(String(255), nullable=False, index=True)
    warc_file = Column(String(500))
    record_id = Column(String(500))
    keywords = Column(ARRAY(String))
    sentiment_score = Column(Float)
    processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ProcessLog(Base):
    """Logs de procesos"""
    __tablename__ = "process_logs"
    __table_args__ = {'schema': 'commoncrawl'}
    
    id = Column(Integer, primary_key=True)
    process_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    records_processed = Column(Integer, default=0)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    error_message = Column(Text)
    parameters = Column(JSON)


def init_db():
    """Inicializar base de datos de forma segura"""
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS commoncrawl"))

        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")

        if ENV == "development":
            insert_test_data()
            logger.info("Datos de prueba insertados (development)")
        else:
            logger.info("Producción: sin datos de prueba")

    except Exception:
        logger.exception("Error inicializando base de datos")
        raise


def insert_test_data():
    """Insertar datos de prueba"""
    session = SessionLocal()
    try:
        # Verificar si ya hay datos
        count = session.query(NewsArticle).count()
        
        if count == 0:
            test_articles = [
                NewsArticle(
                    url=f"https://test-domain-{i}.com/article-{i}",
                    title=f"Artículo de prueba {i} sobre economía colombiana",
                    content=f"Contenido de prueba {i}. El COLCAP muestra tendencia {'positiva' if i % 2 == 0 else 'mixta'} según análisis recientes.",
                    date=datetime(2024, 1, 10 + i).date(),
                    language='es',
                    source_domain='test-domain.com',
                    keywords=['colombia', 'economía', f"test{i}"],
                    processed=True
                )
                for i in range(5)
            ]
            
            session.add_all(test_articles)
            session.commit()
            logger.info(f"Insertados {len(test_articles)} artículos de prueba")
        else:
            logger.info(f"Ya existen {count} artículos en la base de datos")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Error insertando datos de prueba: {e}")
    finally:
        session.close()

def save_articles(articles: List[Dict]) -> int:
    """Guardar artículos en la base de datos"""
    session = SessionLocal()
    saved_count = 0
    
    try:
        for article_data in articles:
            # Verificar si ya existe por URL
            existing = session.query(NewsArticle).filter_by(
                url=article_data.get('url', '')
            ).first()
            
            if not existing:
                article = NewsArticle(
                    url=article_data.get('url', ''),
                    title=article_data.get('title', '')[:500],
                    content=article_data.get('content', ''),
                    date=datetime.strptime(article_data.get('date', '2024-01-01'), '%Y-%m-%d').date(),
                    language=article_data.get('language', 'es'),
                    source_domain=article_data.get('source_domain', ''),
                    warc_file=article_data.get('warc_file', ''),
                    record_id=article_data.get('record_id', ''),
                    keywords=article_data.get('keywords', []),
                    processed=False
                )
                session.add(article)
                saved_count += 1
        
        session.commit()
        logger.info(f"Guardados {saved_count} artículos nuevos")
        
        # Log del proceso
        log_entry = ProcessLog(
            process_name="data_acquisition",
            status="success",
            records_processed=saved_count,
            end_time=datetime.now(),
            parameters={"source": "common_crawl"}
        )
        session.add(log_entry)
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error guardando artículos: {e}")
        
        # Log de error
        try:
            log_entry = ProcessLog(
                process_name="data_acquisition",
                status="failed",
                error_message=str(e)[:500],
                end_time=datetime.now()
            )
            session.add(log_entry)
            session.commit()
        except:
            pass
        raise
    finally:
        session.close()
    
    return saved_count

def get_articles(
    limit: int = 10, 
    offset: int = 0, 
    domain: str = None, 
    keyword: str = None,
    start_date: str = None,
    end_date: str = None
):
    """Obtener artículos de la base de datos"""
    session = SessionLocal()
    
    try:
        query = session.query(NewsArticle)
        
        if domain:
            query = query.filter(NewsArticle.source_domain.ilike(f"%{domain}%"))
        
        if keyword:
            query = query.filter(
                NewsArticle.title.ilike(f"%{keyword}%") | 
                NewsArticle.content.ilike(f"%{keyword}%")
            )
        
        if start_date:
            query = query.filter(NewsArticle.date >= start_date)
        
        if end_date:
            query = query.filter(NewsArticle.date <= end_date)
        
        articles = query.order_by(NewsArticle.date.desc())\
                       .offset(offset)\
                       .limit(limit)\
                       .all()
        
        return [
            {
                "id": article.id,
                "url": article.url,
                "title": article.title,
                "content": article.content[:200] + "..." if len(article.content) > 200 else article.content,
                "date": article.date.isoformat() if article.date else None,
                "language": article.language,
                "source_domain": article.source_domain,
                "keywords": article.keywords,
                "processed": article.processed,
                "created_at": article.created_at.isoformat() if article.created_at else None
            }
            for article in articles
        ]
        
    finally:
        session.close()

def get_stats():
    """Obtener estadísticas de la base de datos"""
    session = SessionLocal()
    
    try:
        total_articles = session.query(NewsArticle).count()
        
        articles_by_domain = session.query(
            NewsArticle.source_domain,
            func.count(NewsArticle.id).label('count')
        ).group_by(NewsArticle.source_domain).all()
        
        articles_by_language = session.query(
            NewsArticle.language,
            func.count(NewsArticle.id).label('count')
        ).group_by(NewsArticle.language).all()
        
        latest_article = session.query(NewsArticle).order_by(
            NewsArticle.created_at.desc()
        ).first()
        
        return {
            "total_articles": total_articles,
            "articles_by_domain": {domain: count for domain, count in articles_by_domain},
            "articles_by_language": {lang: count for lang, count in articles_by_language},
            "latest_article_date": latest_article.created_at.isoformat() if latest_article else None,
            "database_url": DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL
        }
        
    finally:
        session.close()

def check_db_health():
    """Verificar salud de la base de datos"""
    session = SessionLocal()
    try:
        # IMPORTANTE: Usar text() para la consulta SQL
        result = session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Error verificación BD: {e}")
        return False
    finally:
        session.close()