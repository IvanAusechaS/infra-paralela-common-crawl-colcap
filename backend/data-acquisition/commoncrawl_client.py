import boto3
import requests
import gzip
import io
import asyncio
import aiohttp
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime, timedelta
import logging
from warcio import ArchiveIterator
from bs4 import BeautifulSoup
from botocore import UNSIGNED
from botocore.config import Config
from urllib.parse import urlparse
import random
import os

logger = logging.getLogger(__name__)

class CommonCrawlClient:
    """
    Cliente para descargar y procesar datos de Common Crawl
    Versión corregida que funciona con S3 público
    """
    
    def __init__(self, use_s3_direct: bool = False, mode: str = "auto"):
        """
        Inicializar cliente
        
        Args:
            use_s3_direct: Si True, usa boto3 para S3 directo
            mode: "auto" (elige el mejor), "s3" (solo S3), "http" (solo HTTP)
        """
        self.mode = mode
        self.use_s3_direct = use_s3_direct
        
        # Configurar S3 para acceso público SOLO si se va a usar
        if use_s3_direct or mode in ["s3", "auto"]:
            try:
                self.s3 = boto3.client(
                    's3',
                    region_name='us-east-1',
                    config=Config(
                        signature_version=UNSIGNED,
                        s3={'addressing_style': 'path'}
                    )
                )
                logger.info("Cliente S3 configurado (acceso público)")
            except Exception as e:
                logger.error(f"Error configurando S3: {e}")
                self.s3 = None
        
        self.bucket_name = 'commoncrawl'
        
        # Determinar la mejor URL base automáticamente
        if mode == "s3":
            self.base_url = f"https://{self.bucket_name}.s3.amazonaws.com"
        elif mode == "http":
            self.base_url = "https://data.commoncrawl.org"
        else:  # auto - probar data.commoncrawl.org primero
            self.base_url = "https://data.commoncrawl.org"
        
        self.session = None
        self.test_results = {}
        
    async def __aenter__(self):
        """Context manager para sesión async"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cerrar sesión async"""
        if self.session:
            await self.session.close()
    
    def get_available_crawls(self) -> List[Dict]:
        """Obtener lista de crawls disponibles - versión corregida"""
        try:
            # Intentar con data.commoncrawl.org primero
            test_url = f"{self.base_url}/crawl-data/CC-MAIN-2024-10/warc.paths.gz"
            response = requests.head(test_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ {self.base_url} accesible")
                return self._get_real_crawl_list()
            else:
                logger.warning(f"{self.base_url} no accesible, usando lista local")
                return self._get_fallback_crawl_list()
                
        except Exception as e:
            logger.error(f"Error verificando acceso: {e}")
            return self._get_fallback_crawl_list()
    
    def _get_real_crawl_list(self) -> List[Dict]:
        """Lista real de crawls (simplificada)"""
        return [
            {"id": "CC-MAIN-2024-10", "date": "2024-05-2024-06", "size": "~280TB"},
            {"id": "CC-MAIN-2024-05", "date": "2024-03-2024-04", "size": "~250TB"},
            {"id": "CC-MAIN-2023-50", "date": "2023-12-2024-01", "size": "~270TB"},
            {"id": "CC-MAIN-2023-40", "date": "2023-09-2023-10", "size": "~260TB"}
        ]
    
    def _get_fallback_crawl_list(self) -> List[Dict]:
        """Lista de fallback si no hay conexión"""
        return [
            {"id": "CC-MAIN-2024-10", "date": "2024-05-2024-06", "size": "mock"},
            {"id": "CC-MAIN-2024-05", "date": "2024-03-2024-04", "size": "mock"},
        ]
    
    async def download_warc_file(self, warc_path: str, max_records: int = 20) -> List[Dict]:
        """
        Descargar y procesar un archivo WARC específico
        Versión corregida que maneja diferentes métodos
        """
        # Método 1: Intentar con data.commoncrawl.org
        warc_url = f"{self.base_url}/{warc_path}"
        
        logger.info(f"Descargando WARC: {warc_path}")
        
        # HEADER importante para evitar 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/octet-stream',
            'Accept-Encoding': 'gzip'
        }
        
        try:
            # Intentar descargar
            async with self.session.get(warc_url, headers=headers, timeout=60) as response:
                if response.status == 200:
                    content = await response.read()
                    return await self._process_warc_content(content, warc_path, max_records)
                elif response.status == 403 and self.use_s3_direct and self.s3:
                    # Si da 403, intentar con S3 directo
                    logger.info(f"HTTP 403, intentando con S3 directo...")
                    return await self._download_via_s3_direct(warc_path, max_records)
                else:
                    logger.error(f"Error {response.status} descargando {warc_url}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout descargando {warc_path}")
            return []
        except Exception as e:
            logger.error(f"Error procesando WARC {warc_path}: {e}")
            return []
    
    async def _download_via_s3_direct(self, s3_key: str, max_records: int) -> List[Dict]:
        """Descargar usando boto3 S3 directo"""
        try:
            logger.info(f"Descargando via S3: {s3_key}")
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read()
            return await self._process_warc_content(content, s3_key, max_records)
            
        except Exception as e:
            logger.error(f"Error S3 directo: {e}")
            return []
    
    async def _process_warc_content(self, content: bytes, source: str, max_records: int) -> List[Dict]:
        """Procesar contenido WARC"""
        records = []
        stream = io.BytesIO(content)
        
        try:
            for i, record in enumerate(ArchiveIterator(stream)):
                if i >= max_records:
                    break
                
                if record.rec_type == 'response':
                    try:
                        html_content = record.content_stream().read()
                        soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')
                        text = soup.get_text(separator=' ', strip=True)
                        
                        url = record.rec_headers.get_header('WARC-Target-URI', '')
                        
                        # Filtrar solo noticias colombianas relevantes
                        if self._is_relevant_news(url, text):
                            records.append({
                                'url': url,
                                'title': soup.title.string[:200] if soup.title else '',
                                'content': text[:2000],  # Limitar para pruebas
                                'date': record.rec_headers.get_header('WARC-Date', ''),
                                'language': self._detect_language(text),
                                'source_domain': self._extract_domain(url),
                                'warc_file': source,
                                'record_id': f"{source}:{i}",
                                'keywords': self._extract_keywords(text)
                            })
                            
                    except Exception as e:
                        logger.debug(f"Error registro {i}: {e}")
                        continue
                        
            logger.info(f"Procesados {len(records)} registros de {source}")
            return records
            
        except Exception as e:
            logger.error(f"Error procesando contenido: {e}")
            return []
    
    def _is_relevant_news(self, url: str, text: str) -> bool:
        """Filtrar noticias relevantes para Colombia"""
        if not text or len(text) < 100:  # Muy corto, probablemente no es noticia
            return False
        
        keywords = [
            'colombia', 'colombiano', 'colombiana', 'bogotá', 'medellín', 'cali',
            'colcap', 'bolsa de valores', 'economía', 'petróleo', 'peso colombiano',
            'banco de la república', 'inflación', 'dólar', 'exportación'
        ]
        
        text_lower = text.lower()
        
        # Verificar si contiene palabras clave relevantes
        keyword_count = sum(1 for kw in keywords if kw in text_lower)
        
        # Devolver True si tiene al menos 2 palabras clave o es dominio .co
        if keyword_count >= 2:
            return True
        
        # También aceptar si es dominio colombiano
        if '.co' in url.lower() or any(domain in url.lower() for domain in ['eltiempo.com', 'semana.com', 'portafolio.co']):
            return True
            
        return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extraer palabras clave del texto"""
        common_words = ['el', 'la', 'los', 'las', 'de', 'que', 'y', 'en', 'a', 'para']
        words = text.lower().split()[:50]  # Primeras 50 palabras
        
        # Filtrar palabras comunes y mantener palabras significativas
        keywords = [w for w in words if len(w) > 3 and w not in common_words]
        return list(set(keywords))[:10]  # Máximo 10 palabras clave únicas
    
    def _detect_language(self, text: str) -> str:
        """Detección simple de idioma"""
        if not text:
            return 'es'
        
        spanish_words = ['el', 'la', 'los', 'las', 'de', 'que', 'y', 'en', 'con', 'por']
        english_words = ['the', 'and', 'of', 'to', 'in', 'that', 'for', 'with', 'on', 'at']
        
        text_lower = text.lower()[:1000]
        spanish_count = sum(text_lower.count(word) for word in spanish_words)
        english_count = sum(text_lower.count(word) for word in english_words)
        
        return 'es' if spanish_count > english_count else 'en'
    
    def _extract_domain(self, url: str) -> str:
        """Extraer dominio de una URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ''
    
    async def search_news_by_date(
        self, 
        start_date: str, 
        end_date: str, 
        max_records: int = 50,  # Reducido para pruebas
        batch_size: int = 20
    ) -> List[Dict]:
        """
        Buscar noticias en un rango de fechas - VERSIÓN CORREGIDA
        """
        logger.info(f"🔍 Buscando noticias de {start_date} a {end_date}")
        
        # Si es modo local/mock, devolver datos de prueba
        if os.getenv('USE_MOCK_MODE', 'false').lower() == 'true':
            logger.info("Usando modo MOCK para desarrollo")
            return self._get_mock_news_data(start_date, end_date, max_records)
        
        # Obtener crawls que cubran el período
        crawls = self._get_crawls_for_date_range(start_date, end_date)
        
        if not crawls:
            logger.warning("No se encontraron crawls para el rango de fechas")
            return self._get_mock_news_data(start_date, end_date, max_records)
        
        all_records = []
        
        # Probar con máximo 2 crawls para no sobrecargar
        for crawl in crawls[:2]:
            logger.info(f"Procesando crawl: {crawl['id']}")
            
            # Obtener algunos archivos WARC
            warc_files = await self._get_warc_files_for_crawl(crawl['id'], limit=3)  # Solo 3 archivos
            
            if not warc_files:
                logger.warning(f"No se encontraron archivos WARC para {crawl['id']}")
                continue
            
            for warc_file in warc_files:
                records = await self.download_warc_file(warc_file, max_records=batch_size)
                all_records.extend(records)
                
                logger.info(f"Archivo {warc_file}: {len(records)} registros")
                
                if len(all_records) >= max_records:
                    logger.info(f"✓ Alcanzado límite de {max_records} registros")
                    return all_records[:max_records]
        
        logger.info(f"✓ Total de registros obtenidos: {len(all_records)}")
        return all_records[:max_records]
    
    def _get_crawls_for_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Obtener crawls que cubran el rango de fechas"""
        # Mapeo simplificado de fechas a crawls
        crawl_map = {
            "2024-01": "CC-MAIN-2024-05",
            "2024-02": "CC-MAIN-2024-05", 
            "2024-03": "CC-MAIN-2024-05",
            "2024-04": "CC-MAIN-2024-10",
            "2024-05": "CC-MAIN-2024-10",
            "2024-06": "CC-MAIN-2024-10",
            "2023-12": "CC-MAIN-2023-50",
            "2023-11": "CC-MAIN-2023-40",
            "2023-10": "CC-MAIN-2023-40"
        }
        
        # Extraer año-mes de la fecha de inicio
        try:
            year_month = start_date[:7]  # "2024-01"
            if year_month in crawl_map:
                return [{"id": crawl_map[year_month], "date_range": f"{start_date}_{end_date}"}]
        except:
            pass
        
        # Fallback: usar los crawls más recientes
        return [
            {"id": "CC-MAIN-2024-10", "date_range": "2024-05-2024-06"},
            {"id": "CC-MAIN-2024-05", "date_range": "2024-03-2024-04"}
        ]
    
    async def _get_warc_files_for_crawl(self, crawl_id: str, limit: int = 5) -> List[str]:
        """
        Obtener lista REAL de archivos WARC - VERSIÓN CORREGIDA
        """
        index_url = f"{self.base_url}/crawl-data/{crawl_id}/warc.paths.gz"
        
        logger.info(f"📥 Descargando índice: {index_url}")
        
        try:
            # Headers importantes
            headers = {'User-Agent': 'CommonCrawl-Research/1.0'}
            
            async with self.session.get(index_url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    with gzip.open(io.BytesIO(content), 'rt', encoding='utf-8') as f:
                        all_paths = [line.strip() for line in f.readlines()]
                        
                        # Filtrar solo archivos WARC
                        warc_files = [path for path in all_paths if '.warc.' in path]
                        
                        logger.info(f"📊 Índice descargado: {len(all_paths)} rutas, {len(warc_files)} WARC")
                        
                        if not warc_files:
                            logger.warning("No se encontraron archivos WARC en el índice")
                            return []
                        
                        # Tomar una muestra aleatoria (pero pequeña para pruebas)
                        sample_size = min(limit, len(warc_files))
                        selected = random.sample(warc_files, sample_size)
                        
                        logger.info(f"🎯 Seleccionados {len(selected)} archivos WARC")
                        return selected
                        
                else:
                    logger.error(f"❌ Error {response.status} descargando índice")
                    
                    # Fallback: usar archivos de ejemplo conocidos
                    return self._get_fallback_warc_files(crawl_id, limit)
                    
        except asyncio.TimeoutError:
            logger.error(f"⏱️  Timeout descargando índice para {crawl_id}")
            return self._get_fallback_warc_files(crawl_id, limit)
        except Exception as e:
            logger.error(f"⚠️  Error obteniendo índice: {e}")
            return self._get_fallback_warc_files(crawl_id, limit)
    
    def _get_fallback_warc_files(self, crawl_id: str, limit: int) -> List[str]:
        """Archivos WARC de fallback si no se puede descargar el índice"""
        # Archivos de ejemplo conocidos (pueden no existir todos)
        fallback_files = {
            "CC-MAIN-2024-10": [
                "crawl-data/CC-MAIN-2024-10/segments/1707947425256.96/warc/CC-MAIN-20240215215748-20240216005748-00000.warc.gz",
                "crawl-data/CC-MAIN-2024-10/segments/1707947425256.96/warc/CC-MAIN-20240215215748-20240216005748-00001.warc.gz"
            ],
            "CC-MAIN-2024-05": [
                "crawl-data/CC-MAIN-2024-05/segments/1705779538516.12/warc/CC-MAIN-20240121000718-20240121030718-00000.warc.gz",
                "crawl-data/CC-MAIN-2024-05/segments/1705779538516.12/warc/CC-MAIN-20240121000718-20240121030718-00001.warc.gz"
            ]
        }
        
        return fallback_files.get(crawl_id, [])[:limit]
    
    def _get_mock_news_data(self, start_date: str, end_date: str, limit: int) -> List[Dict]:
        """Generar datos mock para desarrollo"""
        logger.info("🛠️  Generando datos MOCK para desarrollo")
        
        mock_domains = [
            "eltiempo.com", "semana.com", "portafolio.co", 
            "bluradio.com", "caracol.com.co", "rcnradio.com",
            "reuters.com", "bloomberg.com"
        ]
        
        mock_titles = [
            "COLCAP cierra en alza tras resultados positivos",
            "Economía colombiana muestra crecimiento en primer trimestre",
            "Analistas predicen fortalecimiento del peso colombiano",
            "Mercado bursátil reacciona a noticias económicas",
            "Banco de la República anuncia nuevas medidas",
            "Exportaciones colombianas registran incremento",
            "Inflación muestra tendencia a la baja en Colombia",
            "Sector financiero impulsa crecimiento económico"
        ]
        
        mock_articles = []
        
        # Generar fechas dentro del rango
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        for i in range(min(limit, 15)):  # Máximo 15 artículos mock
            days_diff = (end - start).days
            random_days = random.randint(0, days_diff) if days_diff > 0 else 0
            article_date = start + timedelta(days=random_days)
            
            domain = random.choice(mock_domains)
            title = random.choice(mock_titles)
            
            mock_articles.append({
                'url': f"https://{domain}/economia/articulo-{i}-{article_date.strftime('%Y%m%d')}",
                'title': f"{title} - {article_date.strftime('%d/%m/%Y')}",
                'content': f"Noticia de prueba sobre economía colombiana. El índice COLCAP mostró un comportamiento positivo durante la jornada. Los analistas del mercado consideran que la economía nacional mantiene una tendencia de crecimiento sostenido. {title.lower()} según los últimos reportes económicos.",
                'date': article_date.strftime("%Y-%m-%d"),
                'language': 'es' if '.co' in domain else 'en',
                'source_domain': domain,
                'warc_file': 'mock_data_source',
                'record_id': f"mock_{i}_{article_date.strftime('%Y%m%d')}",
                'keywords': ['colombia', 'economía', 'colcap', 'mercado', 'finanzas']
            })
        
        logger.info(f"🛠️  Generados {len(mock_articles)} artículos MOCK")
        return mock_articles
    
    async def test_connection(self) -> Dict:
        """Probar conexión a Common Crawl"""
        test_urls = [
            f"{self.base_url}/crawl-data/CC-MAIN-2024-10/warc.paths.gz",
            f"https://{self.bucket_name}.s3.amazonaws.com/crawl-data/CC-MAIN-2024-10/warc.paths.gz",
            "https://data.commoncrawl.org/crawl-data/CC-MAIN-2024-10/warc.paths.gz"
        ]
        
        results = {}
        
        for url in test_urls:
            try:
                async with aiohttp.ClientSession() as temp_session:
                    async with temp_session.head(url, timeout=10) as response:
                        results[url] = {
                            'status': response.status,
                            'accessible': response.status == 200
                        }
            except Exception as e:
                results[url] = {
                    'status': 'error',
                    'accessible': False,
                    'error': str(e)
                }
        
        return results