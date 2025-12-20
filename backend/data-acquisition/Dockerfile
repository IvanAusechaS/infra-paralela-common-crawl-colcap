# Dockerfile con configuración para S3
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema para psycopg2 y otras
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Configurar AWS para acceso público (sin credenciales)
ENV AWS_ACCESS_KEY_ID=none
ENV AWS_SECRET_ACCESS_KEY=none
ENV AWS_DEFAULT_REGION=us-east-1
ENV COMMON_CRAWL_USE_S3=true
ENV COMMON_CRAWL_S3_BUCKET=commoncrawl

# Para desarrollo: permitir S3 sin credenciales
ENV AWS_S3_ALLOW_UNSIGNED=true

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]