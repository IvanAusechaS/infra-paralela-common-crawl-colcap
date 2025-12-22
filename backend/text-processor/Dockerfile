# ==========================================
# Text Processor Service - Dockerfile
# News2Market Project
# 
# Multi-stage build para optimizar tamaño
# de imagen y tiempo de build
# ==========================================

FROM python:3.11-slim as base

# Metadatos
LABEL maintainer="News2Market Team"
LABEL service="text-processor"
LABEL version="1.0.0"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# ==========================================
# Stage 2: Dependencies
# ==========================================
FROM base as dependencies

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# Stage 3: Application
# ==========================================
FROM base as application

# Copiar dependencias instaladas
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Crear usuario no-root para mayor seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8002/health')" || exit 1

# Comando por defecto
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
