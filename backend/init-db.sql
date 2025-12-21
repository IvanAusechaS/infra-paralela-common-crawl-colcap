-- init-db.sql CORREGIDO
-- Script de inicialización de la base de datos Common Crawl

-- Crear schema si no existe
CREATE SCHEMA IF NOT EXISTS commoncrawl;

-- Tabla de artículos de noticias - VERSIÓN CORREGIDA
CREATE TABLE IF NOT EXISTS commoncrawl.news_articles (
    id SERIAL PRIMARY KEY,
    url VARCHAR(1000) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64),  -- ¡COLUMNA AGREGADA!
    date DATE NOT NULL,
    language VARCHAR(10) DEFAULT 'es',
    source_domain VARCHAR(255) NOT NULL,
    warc_file VARCHAR(500),
    record_id VARCHAR(500),
    keywords TEXT[] DEFAULT '{}',
    sentiment_score REAL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para logs de procesos
CREATE TABLE IF NOT EXISTS commoncrawl.process_logs (
    id SERIAL PRIMARY KEY,
    process_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    parameters JSONB
);

-- Tabla para estadísticas
CREATE TABLE IF NOT EXISTS commoncrawl.stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE UNIQUE NOT NULL,
    total_articles INTEGER DEFAULT 0,
    articles_by_domain JSONB,
    articles_by_language JSONB,
    avg_sentiment REAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insertar datos de prueba iniciales
INSERT INTO commoncrawl.news_articles 
(url, title, content, date, source_domain, language, processed) 
VALUES 
(
    'https://eltiempo.com/economia/colcap-enero-2024',
    'COLCAP cierra en alza tras resultados positivos',
    'El índice COLCAP de la Bolsa de Valores de Colombia registró un incremento del 1.5% al cierre de la jornada del martes, impulsado por los buenos resultados de las empresas del sector financiero.',
    '2024-01-15',
    'eltiempo.com',
    'es',
    true
),
(
    'https://portafolio.co/mercados/analisis-economico',
    'Análisis: Perspectivas económicas para 2024',
    'Los expertos consideran que la economía colombiana mostrará una recuperación gradual durante el primer trimestre de 2024, con especial atención a los indicadores del mercado bursátil.',
    '2024-01-14',
    'portafolio.co',
    'es',
    true
),
(
    'https://reuters.com/world/americas/colombia-economy-q1-2024',
    'Colombia economy shows resilience amid challenges',
    'Colombian economic indicators, including the COLCAP index, demonstrate resilience despite global economic uncertainties and domestic challenges.',
    '2024-01-13',
    'reuters.com',
    'en',
    true
)
ON CONFLICT (url) DO NOTHING;

-- Crear índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_articles_date ON commoncrawl.news_articles(date);
CREATE INDEX IF NOT EXISTS idx_articles_domain ON commoncrawl.news_articles(source_domain);
CREATE INDEX IF NOT EXISTS idx_articles_language ON commoncrawl.news_articles(language);
CREATE INDEX IF NOT EXISTS idx_articles_processed ON commoncrawl.news_articles(processed);

-- Verificar creación
SELECT '✅ Base de datos Common Crawl inicializada correctamente' as message;
SELECT '📊 Tablas creadas:' as info;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'commoncrawl' ORDER BY table_name;
SELECT '📰 Artículos de prueba:' as info;
SELECT COUNT(*) as total_articles FROM commoncrawl.news_articles;