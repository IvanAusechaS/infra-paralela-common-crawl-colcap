"""
Redis Queue Client - News2Market

Cliente para interacción con Redis como sistema de colas
para distribución de tareas de procesamiento.

Autor: Equipo News2Market
Versión: 1.0.0
"""

import redis.asyncio as redis
from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RedisQueue:
    """Cliente de cola Redis para distribución de tareas"""
    
    # Nombres de las colas
    TASK_QUEUE = "tasks:text_processor"
    PROCESSING_QUEUE = "tasks:text_processor:processing"
    COMPLETED_QUEUE = "tasks:text_processor:completed"
    FAILED_QUEUE = "tasks:text_processor:failed"
    
    def __init__(self, redis_url: str):
        """
        Inicializar cliente Redis
        
        Args:
            redis_url: URL de conexión a Redis (ej: redis://localhost:6379/0)
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        logger.info(f"RedisQueue configurado con URL: {redis_url}")
    
    async def connect(self):
        """Establecer conexión con Redis"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Verificar conexión
            await self.client.ping()
            logger.info("✅ Conexión a Redis establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            raise
    
    async def disconnect(self):
        """Cerrar conexión con Redis"""
        if self.client:
            await self.client.close()
            logger.info("👋 Conexión a Redis cerrada")
    
    async def ping(self) -> bool:
        """
        Verificar que Redis está respondiendo
        
        Returns:
            bool: True si Redis responde, False en caso contrario
        """
        try:
            if self.client:
                await self.client.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"Redis ping falló: {e}")
            return False
    
    async def enqueue_task(self, task: Dict[str, Any], priority: int = 0):
        """
        Encolar una tarea para procesamiento
        
        Args:
            task: Diccionario con datos de la tarea
            priority: Prioridad de la tarea (mayor = más prioritario)
        """
        try:
            if not self.client:
                raise Exception("Redis no conectado")
            
            # Agregar metadata
            task['enqueued_at'] = datetime.utcnow().isoformat()
            task['priority'] = priority
            
            # Serializar tarea
            task_json = json.dumps(task)
            
            # Agregar a la cola (usar RPUSH para FIFO o ZADD para prioridad)
            if priority > 0:
                # Con prioridad (sorted set)
                await self.client.zadd(self.TASK_QUEUE, {task_json: -priority})
            else:
                # Sin prioridad (lista FIFO)
                await self.client.rpush(self.TASK_QUEUE, task_json)
            
            logger.debug(f"✅ Tarea encolada: article_id={task.get('article_id')}, priority={priority}")
            
        except Exception as e:
            logger.error(f"❌ Error encolando tarea: {e}")
            raise
    
    async def dequeue_task(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Obtener una tarea de la cola
        
        Args:
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Optional[Dict[str, Any]]: Tarea o None si no hay tareas
        """
        try:
            if not self.client:
                raise Exception("Redis no conectado")
            
            # Intentar obtener de cola con prioridad primero
            result = await self.client.zpopmin(self.TASK_QUEUE, count=1)
            
            if result:
                task_json, _ = result[0]
                task = json.loads(task_json)
                
                # Marcar como en procesamiento
                await self.client.hset(
                    self.PROCESSING_QUEUE,
                    task.get('article_id', 'unknown'),
                    json.dumps({
                        **task,
                        'started_at': datetime.utcnow().isoformat()
                    })
                )
                
                logger.debug(f"📥 Tarea obtenida: article_id={task.get('article_id')}")
                return task
            
            # Si no hay en cola con prioridad, intentar en cola normal
            result = await self.client.blpop(self.TASK_QUEUE, timeout=timeout)
            
            if result:
                _, task_json = result
                task = json.loads(task_json)
                
                # Marcar como en procesamiento
                await self.client.hset(
                    self.PROCESSING_QUEUE,
                    task.get('article_id', 'unknown'),
                    json.dumps({
                        **task,
                        'started_at': datetime.utcnow().isoformat()
                    })
                )
                
                logger.debug(f"📥 Tarea obtenida: article_id={task.get('article_id')}")
                return task
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo tarea: {e}")
            return None
    
    async def mark_completed(self, article_id: int, result: Dict[str, Any]):
        """
        Marcar una tarea como completada
        
        Args:
            article_id: ID del artículo procesado
            result: Resultado del procesamiento
        """
        try:
            if not self.client:
                return
            
            # Remover de procesamiento
            await self.client.hdel(self.PROCESSING_QUEUE, str(article_id))
            
            # Agregar a completados con TTL de 1 hora
            await self.client.hset(
                self.COMPLETED_QUEUE,
                str(article_id),
                json.dumps({
                    **result,
                    'completed_at': datetime.utcnow().isoformat()
                })
            )
            await self.client.expire(self.COMPLETED_QUEUE, 3600)
            
            logger.debug(f"✅ Tarea marcada como completada: article_id={article_id}")
            
        except Exception as e:
            logger.error(f"❌ Error marcando tarea como completada: {e}")
    
    async def mark_failed(self, article_id: int, error: str):
        """
        Marcar una tarea como fallida
        
        Args:
            article_id: ID del artículo
            error: Mensaje de error
        """
        try:
            if not self.client:
                return
            
            # Remover de procesamiento
            await self.client.hdel(self.PROCESSING_QUEUE, str(article_id))
            
            # Agregar a fallidos
            await self.client.hset(
                self.FAILED_QUEUE,
                str(article_id),
                json.dumps({
                    'article_id': article_id,
                    'error': error,
                    'failed_at': datetime.utcnow().isoformat()
                })
            )
            
            logger.debug(f"❌ Tarea marcada como fallida: article_id={article_id}")
            
        except Exception as e:
            logger.error(f"❌ Error marcando tarea como fallida: {e}")
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """
        Obtener estadísticas de las colas
        
        Returns:
            Dict[str, int]: Estadísticas de tareas
        """
        try:
            if not self.client:
                return {}
            
            pending = await self.client.llen(self.TASK_QUEUE)
            processing = await self.client.hlen(self.PROCESSING_QUEUE)
            completed = await self.client.hlen(self.COMPLETED_QUEUE)
            failed = await self.client.hlen(self.FAILED_QUEUE)
            
            return {
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "total": pending + processing + completed + failed
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    async def clear_queue(self, queue_name: Optional[str] = None):
        """
        Limpiar una cola específica o todas
        
        Args:
            queue_name: Nombre de la cola a limpiar (None = todas)
        """
        try:
            if not self.client:
                return
            
            if queue_name:
                await self.client.delete(queue_name)
                logger.info(f"🗑️ Cola {queue_name} limpiada")
            else:
                await self.client.delete(
                    self.TASK_QUEUE,
                    self.PROCESSING_QUEUE,
                    self.COMPLETED_QUEUE,
                    self.FAILED_QUEUE
                )
                logger.info("🗑️ Todas las colas limpiadas")
                
        except Exception as e:
            logger.error(f"❌ Error limpiando cola: {e}")

# ==================== TESTING ====================

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def test_redis():
        """Test básico de funcionalidad Redis"""
        queue = RedisQueue("redis://localhost:6379/0")
        
        try:
            # Conectar
            await queue.connect()
            
            # Encolar tarea
            await queue.enqueue_task({
                "article_id": 1,
                "title": "Test Article"
            })
            
            # Obtener estadísticas
            stats = await queue.get_queue_stats()
            print(f"Estadísticas: {stats}")
            
            # Obtener tarea
            task = await queue.dequeue_task()
            print(f"Tarea obtenida: {task}")
            
            if task:
                # Marcar como completada
                await queue.mark_completed(task['article_id'], {"status": "success"})
            
            # Estadísticas finales
            stats = await queue.get_queue_stats()
            print(f"Estadísticas finales: {stats}")
            
        finally:
            await queue.disconnect()
    
    # Ejecutar test
    asyncio.run(test_redis())
