"""
Database Module - Correlation Service

Modelos de SQLAlchemy y operaciones de base de datos para el servicio de correlación.

Autor: Equipo News2Market
Versión: 1.0.0
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, JSON, Float, Integer, select
import os

logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+asyncpg://news2market:password@localhost:5432/news2market'
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    """Clase base para modelos"""
    pass

class CorrelationResult(Base):
    """
    Modelo para resultados de análisis de correlación
    
    Almacena los resultados del análisis de correlación entre métricas
    noticiosas y el índice COLCAP.
    """
    __tablename__ = 'correlation_results'
    
    # Clave primaria
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identificador del job
    job_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # Periodo de análisis
    start_date: Mapped[str] = mapped_column(String(10))
    end_date: Mapped[str] = mapped_column(String(10))
    
    # Días de lag aplicado
    lag_days: Mapped[int] = mapped_column(Integer, default=0)
    
    # Resultados de correlación
    correlations: Mapped[Dict] = mapped_column(JSON)  # {"volume": 0.75, "keywords": 0.82, ...}
    p_values: Mapped[Dict] = mapped_column(JSON)  # {"volume": 0.001, "keywords": 0.0003, ...}
    
    # Insights generados
    insights: Mapped[List] = mapped_column(JSON)  # ["insight 1", "insight 2", ...]
    
    # Tamaño de muestra
    sample_size: Mapped[int] = mapped_column(Integer)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<CorrelationResult(id={self.id}, job_id='{self.job_id}', dates={self.start_date} to {self.end_date})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir a diccionario para respuestas JSON
        
        Returns:
            Dict: Representación del resultado
        """
        return {
            'job_id': self.job_id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'lag_days': self.lag_days,
            'correlations': self.correlations,
            'p_values': self.p_values,
            'insights': self.insights,
            'sample_size': self.sample_size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ========================
# Database Operations
# ========================

async def init_database():
    """
    Inicializar tablas de base de datos
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Tablas de base de datos inicializadas")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        raise

async def get_db_session() -> AsyncSession:
    """
    Obtener sesión de base de datos
    
    Yields:
        AsyncSession: Sesión de SQLAlchemy
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def save_correlation_result(
    job_id: str,
    start_date: str,
    end_date: str,
    lag_days: int,
    correlations: Dict[str, float],
    p_values: Dict[str, float],
    insights: List[str],
    sample_size: int
) -> CorrelationResult:
    """
    Guardar resultado de análisis de correlación
    
    Args:
        job_id: Identificador único del job
        start_date: Fecha de inicio del análisis
        end_date: Fecha de fin del análisis
        lag_days: Días de retraso aplicados
        correlations: Diccionario con correlaciones por métrica
        p_values: Diccionario con p-values por métrica
        insights: Lista de insights generados
        sample_size: Tamaño de la muestra
        
    Returns:
        CorrelationResult: Objeto guardado
    """
    async with AsyncSessionLocal() as session:
        try:
            result = CorrelationResult(
                job_id=job_id,
                start_date=start_date,
                end_date=end_date,
                lag_days=lag_days,
                correlations=correlations,
                p_values=p_values,
                insights=insights,
                sample_size=sample_size
            )
            
            session.add(result)
            await session.commit()
            await session.refresh(result)
            
            logger.info(f"✅ Resultado de correlación guardado: {job_id}")
            return result
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error guardando resultado: {e}")
            raise

async def get_correlation_result(job_id: str) -> Optional[CorrelationResult]:
    """
    Obtener resultado de correlación por job_id
    
    Args:
        job_id: Identificador del job
        
    Returns:
        Optional[CorrelationResult]: Resultado o None si no existe
    """
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(CorrelationResult).where(CorrelationResult.job_id == job_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resultado: {e}")
            return None

async def list_correlation_results(limit: int = 50) -> List[CorrelationResult]:
    """
    Listar resultados de correlación recientes
    
    Args:
        limit: Número máximo de resultados
        
    Returns:
        List[CorrelationResult]: Lista de resultados
    """
    async with AsyncSessionLocal() as session:
        try:
            stmt = (
                select(CorrelationResult)
                .order_by(CorrelationResult.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"❌ Error listando resultados: {e}")
            return []
