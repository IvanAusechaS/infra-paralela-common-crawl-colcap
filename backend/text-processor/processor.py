"""
Text Processor Module - News2Market

Módulo principal para procesamiento de texto de artículos de noticias.
Incluye limpieza HTML, normalización, extracción de keywords económicas,
y análisis de sentimiento básico.

Características:
- Limpieza de HTML con BeautifulSoup
- Normalización de texto
- Extracción de keywords económicas colombianas
- Análisis de sentimiento básico
- Extracción de entidades nombradas
- Conteo de palabras y métricas

Autor: Equipo News2Market
Versión: 1.0.0
"""

from bs4 import BeautifulSoup
import re
from typing import Dict, List, Tuple, Any
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Palabras clave económicas relevantes para Colombia y COLCAP
ECONOMIC_KEYWORDS = [
    # Mercado bursátil
    "colcap", "bolsa", "acciones", "bursátil", "mercado", "índice",
    "inversión", "inversionistas", "cotización", "valorización",
    
    # Economía general
    "economía", "económico", "pib", "crecimiento", "desarrollo",
    "producción", "productividad", "competitividad",
    
    # Finanzas
    "banco", "bancos", "bancario", "financiero", "crédito", "préstamo",
    "tasa", "tasas", "interés", "financiamiento",
    
    # Comercio
    "comercio", "exportación", "exportaciones", "importación", "importaciones",
    "balanza", "déficit", "superávit", "aranceles",
    
    # Moneda
    "dólar", "dólares", "peso", "pesos", "divisa", "divisas",
    "devaluación", "revaluación", "cambio", "tasa de cambio",
    
    # Inflación y precios
    "inflación", "deflación", "precios", "IPC", "costo", "costos",
    "encarecimiento", "abaratamiento",
    
    # Empleo
    "empleo", "desempleo", "trabajo", "empleos", "desocupación",
    "ocupación", "laboral", "salario", "salarios",
    
    # Sectores
    "petróleo", "petrolero", "energía", "minería", "agricultura",
    "industria", "servicios", "construcción", "turismo",
    
    # Gobierno y política económica
    "impuesto", "impuestos", "tributario", "fiscal", "presupuesto",
    "gasto", "reforma", "política económica",
    
    # Crisis y recuperación
    "crisis", "recesión", "recuperación", "reactivación", "estabilidad",
    "volatilidad", "riesgo", "incertidumbre"
]

# Stopwords en español (palabras comunes a ignorar)
SPANISH_STOPWORDS = {
    "el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no", "haber",
    "por", "con", "su", "para", "como", "estar", "tener", "le", "lo", "todo",
    "pero", "más", "hacer", "o", "poder", "decir", "este", "ir", "otro", "ese",
    "si", "me", "ya", "ver", "porque", "dar", "cuando", "él", "muy", "sin",
    "vez", "mucho", "saber", "qué", "sobre", "mi", "alguno", "mismo", "yo",
    "también", "hasta", "año", "dos", "querer", "entre", "así", "primero",
    "desde", "grande", "eso", "ni", "nos", "llegar", "pasar", "tiempo", "ella",
    "sí", "día", "uno", "bien", "poco", "deber", "entonces", "poner", "cosa",
    "tanto", "hombre", "parecer", "nuestro", "tan", "donde", "ahora", "parte",
    "después", "vida", "quedar", "siempre", "creer", "hablar", "llevar", "dejar",
    "nada", "cada", "seguir", "menos", "nuevo", "encontrar", "algo", "solo",
    "decir", "puede", "fue", "han", "son", "sus", "les", "una", "las", "del",
    "los", "al", "está", "ha", "hay", "fueron", "era", "sean", "son", "sobre"
}

# Palabras positivas y negativas para análisis de sentimiento básico
POSITIVE_WORDS = {
    "crecimiento", "recuperación", "éxito", "ganancia", "beneficio", "aumento",
    "mejora", "optimismo", "positivo", "favorable", "ventaja", "fortaleza",
    "prosperidad", "avance", "progreso", "subida", "alza", "expansión",
    "superávit", "rentabilidad", "eficiencia", "competitivo", "innovación"
}

NEGATIVE_WORDS = {
    "crisis", "caída", "pérdida", "déficit", "recesión", "desplome", "baja",
    "declive", "retroceso", "negativo", "desfavorable", "riesgo", "incertidumbre",
    "volatilidad", "desempleo", "inflación", "devaluación", "colapso", "quiebra",
    "bancarrota", "deterioro", "debilidad", "contracción", "reducción"
}

class TextProcessor:
    """
    Clase para procesamiento avanzado de texto de artículos de noticias
    """
    
    def __init__(self):
        """Inicializar el procesador de texto"""
        self.economic_keywords = set(ECONOMIC_KEYWORDS)
        self.stopwords = SPANISH_STOPWORDS
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        
        logger.info("✅ TextProcessor inicializado")
    
    def clean_html(self, html_content: str) -> str:
        """
        Limpiar HTML y extraer solo el texto
        
        Args:
            html_content: Contenido HTML del artículo
            
        Returns:
            str: Texto limpio sin etiquetas HTML
        """
        try:
            # Parsear HTML con BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Eliminar scripts, estilos y otros elementos no deseados
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # Extraer texto
            text = soup.get_text(separator=' ', strip=True)
            
            # Limpiar espacios múltiples
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error limpiando HTML: {e}")
            # Si falla BeautifulSoup, intentar regex básico
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
    
    def normalize_text(self, text: str) -> str:
        """
        Normalizar texto (minúsculas, eliminar puntuación excesiva, etc.)
        
        Args:
            text: Texto a normalizar
            
        Returns:
            str: Texto normalizado
        """
        # Convertir a minúsculas
        text = text.lower()
        
        # Eliminar URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Eliminar emails
        text = re.sub(r'\S+@\S+', '', text)
        
        # Eliminar caracteres especiales pero mantener acentos y ñ
        text = re.sub(r'[^a-záéíóúüñ\s]', ' ', text)
        
        # Eliminar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenizar texto en palabras
        
        Args:
            text: Texto a tokenizar
            
        Returns:
            List[str]: Lista de palabras (tokens)
        """
        # Dividir por espacios
        tokens = text.split()
        
        # Filtrar palabras muy cortas (menos de 3 caracteres)
        tokens = [token for token in tokens if len(token) >= 3]
        
        # Filtrar stopwords
        tokens = [token for token in tokens if token not in self.stopwords]
        
        return tokens
    
    def extract_economic_keywords(self, tokens: List[str]) -> Dict[str, int]:
        """
        Extraer y contar keywords económicas del texto
        
        Args:
            tokens: Lista de tokens del texto
            
        Returns:
            Dict[str, int]: Diccionario con keywords y sus frecuencias
        """
        # Contar ocurrencias de keywords económicas
        keyword_counts = {}
        
        for token in tokens:
            if token in self.economic_keywords:
                keyword_counts[token] = keyword_counts.get(token, 0) + 1
        
        # Ordenar por frecuencia (mayor a menor)
        keyword_counts = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True))
        
        return keyword_counts
    
    def calculate_sentiment(self, tokens: List[str]) -> float:
        """
        Calcular sentimiento básico del texto
        
        Args:
            tokens: Lista de tokens del texto
            
        Returns:
            float: Score de sentimiento (-1.0 a 1.0)
                   -1.0 = muy negativo
                    0.0 = neutral
                    1.0 = muy positivo
        """
        positive_count = sum(1 for token in tokens if token in self.positive_words)
        negative_count = sum(1 for token in tokens if token in self.negative_words)
        
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return 0.0  # Neutral
        
        # Calcular score normalizado
        sentiment_score = (positive_count - negative_count) / total_sentiment_words
        
        return round(sentiment_score, 3)
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extraer entidades nombradas básicas (organizaciones, lugares)
        
        Args:
            text: Texto del cual extraer entidades
            
        Returns:
            List[str]: Lista de entidades encontradas
        """
        entities = []
        
        # Palabras que indican organizaciones
        org_indicators = ["banco", "empresa", "compañía", "corporación", "grupo", "ministerio"]
        
        # Buscar patrones de entidades (palabras capitalizadas)
        words = text.split()
        for i, word in enumerate(words):
            # Si la palabra comienza con mayúscula y no es la primera del texto
            if word and word[0].isupper() and i > 0:
                # Verificar si es parte de una organización
                if i > 0 and any(indicator in words[i-1].lower() for indicator in org_indicators):
                    entities.append(word)
                # O si es seguida por palabras en mayúscula (nombres compuestos)
                elif i < len(words) - 1 and words[i+1] and words[i+1][0].isupper():
                    entities.append(f"{word} {words[i+1]}")
        
        # Eliminar duplicados y retornar
        return list(set(entities))[:20]  # Limitar a 20 entidades
    
    def process_article(self, title: str, content: str, url: str) -> Dict[str, Any]:
        """
        Procesar un artículo completo
        
        Args:
            title: Título del artículo
            content: Contenido HTML del artículo
            url: URL del artículo
            
        Returns:
            Dict[str, Any]: Diccionario con todos los resultados del procesamiento
        """
        try:
            # 1. Limpiar HTML
            cleaned_text = self.clean_html(content)
            
            # 2. Agregar título al texto
            full_text = f"{title}. {cleaned_text}"
            
            # 3. Normalizar
            normalized_text = self.normalize_text(full_text)
            
            # 4. Tokenizar
            tokens = self.tokenize(normalized_text)
            
            # 5. Contar palabras
            word_count = len(tokens)
            
            # 6. Extraer keywords económicas
            economic_keywords = self.extract_economic_keywords(tokens)
            
            # 7. Calcular sentimiento
            sentiment_score = self.calculate_sentiment(tokens)
            
            # 8. Extraer entidades
            entities = self.extract_entities(cleaned_text)
            
            # 9. Calcular métricas adicionales
            economic_density = len(economic_keywords) / max(word_count, 1)
            
            result = {
                "cleaned_content": cleaned_text[:2000],  # Limitar para almacenamiento
                "word_count": word_count,
                "economic_keywords": economic_keywords,
                "economic_keyword_count": len(economic_keywords),
                "economic_density": round(economic_density, 4),
                "sentiment_score": sentiment_score,
                "entities": entities,
                "entity_count": len(entities),
                "title": title,
                "url": url
            }
            
            logger.debug(f"✅ Artículo procesado: {word_count} palabras, {len(economic_keywords)} keywords económicas")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando artículo: {e}")
            # Retornar resultado vacío en caso de error
            return {
                "cleaned_content": "",
                "word_count": 0,
                "economic_keywords": {},
                "economic_keyword_count": 0,
                "economic_density": 0.0,
                "sentiment_score": 0.0,
                "entities": [],
                "entity_count": 0,
                "title": title,
                "url": url,
                "error": str(e)
            }
    
    def batch_process(self, articles: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Procesar un lote de artículos
        
        Args:
            articles: Lista de diccionarios con datos de artículos
                      Cada uno debe tener: title, content, url
            
        Returns:
            List[Dict[str, Any]]: Lista con resultados de procesamiento
        """
        results = []
        
        for article in articles:
            result = self.process_article(
                title=article.get('title', ''),
                content=article.get('content', ''),
                url=article.get('url', '')
            )
            results.append(result)
        
        logger.info(f"✅ Lote procesado: {len(results)} artículos")
        
        return results

# ==================== FUNCIONES AUXILIARES ====================

def calculate_readability(text: str) -> float:
    """
    Calcular índice de legibilidad simple (basado en longitud de palabras)
    
    Args:
        text: Texto a analizar
        
    Returns:
        float: Score de legibilidad (0-100, mayor = más fácil de leer)
    """
    words = text.split()
    if not words:
        return 0.0
    
    # Promedio de longitud de palabras
    avg_word_length = sum(len(word) for word in words) / len(words)
    
    # Normalizar a escala 0-100 (palabras más cortas = más legible)
    readability = max(0, 100 - (avg_word_length - 4) * 10)
    
    return round(readability, 2)

def extract_dates(text: str) -> List[str]:
    """
    Extraer fechas mencionadas en el texto
    
    Args:
        text: Texto del cual extraer fechas
        
    Returns:
        List[str]: Lista de fechas encontradas
    """
    # Patrones de fecha comunes en español
    date_patterns = [
        r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',  # 15 de enero de 2024
        r'\d{1,2}/\d{1,2}/\d{4}',             # 15/01/2024
        r'\d{4}-\d{2}-\d{2}'                  # 2024-01-15
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    
    return dates

# ==================== TESTING ====================

if __name__ == "__main__":
    # Configurar logging para testing
    logging.basicConfig(level=logging.DEBUG)
    
    # Crear instancia del procesador
    processor = TextProcessor()
    
    # Texto de prueba
    sample_html = """
    <html>
        <head><title>Test</title></head>
        <body>
            <h1>Análisis del COLCAP en 2024</h1>
            <p>El índice <strong>COLCAP</strong> ha mostrado un crecimiento sostenido durante el primer trimestre.
            Los inversionistas mantienen optimismo sobre el comportamiento del mercado bursátil colombiano.</p>
            <p>Expertos del Banco de la República señalan que la inflación se ha estabilizado,
            lo cual favorece el clima de inversión. El dólar ha mantenido una tasa de cambio estable.</p>
        </body>
    </html>
    """
    
    # Procesar
    result = processor.process_article(
        title="Análisis del COLCAP en 2024",
        content=sample_html,
        url="http://example.com"
    )
    
    # Mostrar resultados
    print("\n" + "="*50)
    print("RESULTADOS DEL PROCESAMIENTO")
    print("="*50)
    print(f"Palabras: {result['word_count']}")
    print(f"Keywords económicas: {result['economic_keywords']}")
    print(f"Sentimiento: {result['sentiment_score']}")
    print(f"Entidades: {result['entities']}")
    print(f"Densidad económica: {result['economic_density']}")
    print("="*50)
