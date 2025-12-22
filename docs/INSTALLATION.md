# Guía de Instalación - News2Market

Esta guía te ayudará a configurar y ejecutar el proyecto News2Market desde cero en tu máquina local.

## Tabla de Contenidos

1. [Prerrequisitos](#prerrequisitos)
2. [Instalación](#instalación)
3. [Configuración](#configuración)
4. [Ejecución con Docker](#ejecución-con-docker)
5. [Ejecución sin Docker (Desarrollo)](#ejecución-sin-docker-desarrollo)
6. [Verificación del Sistema](#verificación-del-sistema)
7. [Solución de Problemas](#solución-de-problemas)
8. [Comandos Útiles](#comandos-útiles)

---

## Prerrequisitos

Antes de comenzar, asegúrate de tener instalado lo siguiente:

### Software Requerido

1. **Docker Desktop** (recomendado)
   - Versión: 20.10+
   - Descarga: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - Incluye Docker Compose automáticamente

2. **Git**
   - Versión: 2.30+
   - Descarga: [https://git-scm.com/downloads](https://git-scm.com/downloads)

### Software Opcional (solo para desarrollo sin Docker)

3. **Node.js**
   - Versión: 20.x LTS
   - Descarga: [https://nodejs.org/](https://nodejs.org/)
   - Incluye npm automáticamente

4. **Python**
   - Versión: 3.11+
   - Descarga: [https://www.python.org/downloads/](https://www.python.org/downloads/)

5. **PostgreSQL**
   - Versión: 15+
   - Descarga: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)

6. **Redis**
   - Versión: 7+
   - Descarga: [https://redis.io/download](https://redis.io/download)

### Verificación de Instalación

Ejecuta estos comandos para verificar que tienes todo instalado:

```bash
# Docker
docker --version
# Debe mostrar: Docker version 20.10.x o superior

docker-compose --version
# Debe mostrar: Docker Compose version v2.x.x o superior

# Git
git --version
# Debe mostrar: git version 2.30.x o superior

# Opcional (para desarrollo sin Docker)
node --version
# Debe mostrar: v20.x.x

npm --version
# Debe mostrar: 10.x.x

python --version
# Debe mostrar: Python 3.11.x o superior
```

---

## Instalación

### 1. Clonar el Repositorio

```bash
# Clonar con HTTPS
git clone https://github.com/tu-usuario/infra-paralela-common-crawl-colcap.git

# O clonar con SSH (requiere configuración de llaves)
git clone git@github.com:tu-usuario/infra-paralela-common-crawl-colcap.git

# Entrar al directorio del proyecto
cd infra-paralela-common-crawl-colcap
```

### 2. Verificar la Estructura

Asegúrate de que la estructura del proyecto es correcta:

```bash
ls -la
# Deberías ver:
# backend/
# frontend/
# docs/
# k8s/
# scripts/
# docker-compose.yml (si está en la raíz)
```

---

## Configuración

### 1. Variables de Entorno

El proyecto usa valores por defecto que funcionan con Docker Compose. Si necesitas personalizarlos, crea un archivo `.env` en la raíz del proyecto:

```bash
# Copiar ejemplo de variables de entorno (si existe)
cp .env.example .env

# O crear uno nuevo
touch .env
```

**Contenido del `.env` (opcional)**:

```env
# Base de datos
POSTGRES_USER=news2market
POSTGRES_PASSWORD=password
POSTGRES_DB=news2market
DATABASE_URL=postgresql+asyncpg://news2market:password@postgres:5432/news2market

# Redis
REDIS_URL=redis://redis:6379/0

# Puertos de servicios (cambiar solo si hay conflictos)
API_GATEWAY_PORT=8000
DATA_ACQUISITION_PORT=8001
TEXT_PROCESSOR_PORT=8002
CORRELATION_SERVICE_PORT=8003
MOCK_SERVICES_PORT=8004

# Frontend
VITE_API_URL=http://localhost:8000/api/v1

# Entorno
ENV=development
LOG_LEVEL=INFO
```

⚠️ **Nota**: Los valores por defecto en `docker-compose.yml` funcionan sin necesidad de crear este archivo.

---

## Ejecución con Docker

Esta es la forma **más fácil y recomendada** de ejecutar el proyecto.

### 1. Iniciar todos los servicios

Desde la raíz del proyecto:

```bash
# Iniciar en modo detached (background)
docker-compose up -d

# O iniciar viendo logs en tiempo real
docker-compose up
```

**Qué hace esto**:
- Descarga las imágenes de Docker necesarias (primera vez)
- Crea la red `news2market-network`
- Inicia PostgreSQL y Redis
- Construye e inicia los 4 microservicios del backend
- Construye e inicia el frontend
- Ejecuta el script de inicialización de base de datos

### 2. Verificar que los servicios estén corriendo

```bash
docker-compose ps
```

**Salida esperada**:
```
NAME                          STATUS              PORTS
api-gateway                   Up                  0.0.0.0:8000->8000/tcp
correlation-service           Up                  0.0.0.0:8003->8003/tcp
data-acquisition              Up                  0.0.0.0:8001->8001/tcp
frontend                      Up                  0.0.0.0:80->80/tcp
postgres                      Up                  0.0.0.0:5432->5432/tcp
redis                         Up                  0.0.0.0:6379->6379/tcp
text-processor                Up                  0.0.0.0:8002->8002/tcp
```

### 3. Ver logs

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f api-gateway
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 4. Acceder a la aplicación

Una vez que todos los servicios estén corriendo (espera ~30 segundos la primera vez):

- **Frontend**: [http://localhost](http://localhost) o [http://localhost:80](http://localhost:80)
- **API Gateway**: [http://localhost:8000](http://localhost:8000)
- **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Data Acquisition**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Text Processor**: [http://localhost:8002/docs](http://localhost:8002/docs)
- **Correlation Service**: [http://localhost:8003/docs](http://localhost:8003/docs)

### 5. Detener los servicios

```bash
# Detener sin eliminar volúmenes (conserva la base de datos)
docker-compose down

# Detener y eliminar volúmenes (limpieza completa)
docker-compose down -v
```

---

## Ejecución sin Docker (Desarrollo)

Si prefieres ejecutar los servicios individualmente para desarrollo:

### 1. Backend

#### a. Instalar dependencias de Python

```bash
# Entrar al directorio del backend
cd backend

# Crear un entorno virtual (recomendado)
python -m venv venv

# Activar el entorno virtual
# En Windows PowerShell:
.\venv\Scripts\Activate.ps1

# En Windows CMD:
.\venv\Scripts\activate.bat

# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias de cada servicio
cd api-gateway
pip install -r requirements.txt

cd ../data-acquisition
pip install -r requirements.txt

cd ../text-processor
pip install -r requirements.txt

cd ../correlation-service
pip install -r requirements.txt
```

#### b. Iniciar PostgreSQL y Redis

```bash
# Opción 1: Con Docker solo para DB
docker run -d -p 5432:5432 -e POSTGRES_USER=news2market -e POSTGRES_PASSWORD=password -e POSTGRES_DB=news2market postgres:15

docker run -d -p 6379:6379 redis:7

# Opción 2: Instalación local (sigue la documentación oficial)
```

#### c. Inicializar la base de datos

```bash
# Conectar a PostgreSQL
psql -h localhost -U news2market -d news2market

# Ejecutar el script de inicialización
\i backend/init-db.sql

# O desde la terminal
psql -h localhost -U news2market -d news2market -f backend/init-db.sql
```

#### d. Iniciar los servicios

Abre **4 terminales separadas** y ejecuta cada servicio:

**Terminal 1: API Gateway**
```bash
cd backend/api-gateway
python app.py
# Corre en http://localhost:8000
```

**Terminal 2: Data Acquisition**
```bash
cd backend/data-acquisition
python app.py
# Corre en http://localhost:8001
```

**Terminal 3: Text Processor**
```bash
cd backend/text-processor
python app.py
# Corre en http://localhost:8002
```

**Terminal 4: Correlation Service**
```bash
cd backend/correlation-service
python app.py
# Corre en http://localhost:8003
```

### 2. Frontend

En una **quinta terminal**:

```bash
# Entrar al directorio del frontend
cd frontend

# Instalar dependencias
npm install

# Iniciar el servidor de desarrollo
npm run dev
# Corre en http://localhost:5173
```

⚠️ **Nota**: El frontend intentará conectar a `http://localhost:8000/api/v1` por defecto.

---

## Verificación del Sistema

### 1. Health Checks

Verifica que todos los servicios estén saludables:

```bash
# API Gateway + resumen de todos los servicios
curl http://localhost:8000/api/v1/health

# Data Acquisition
curl http://localhost:8001/health

# Text Processor
curl http://localhost:8002/health

# Correlation Service
curl http://localhost:8003/health
```

**Respuesta esperada** (ejemplo para API Gateway):
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00",
  "services": {
    "api_gateway": "healthy",
    "data_acquisition": "healthy",
    "text_processor": "healthy",
    "correlation_service": "healthy"
  }
}
```

### 2. Test de Funcionalidad

#### Test 1: Verificar conexión a PostgreSQL

```bash
# Dentro de Docker
docker exec -it postgres psql -U news2market -d news2market -c "SELECT version();"

# Localmente
psql -h localhost -U news2market -d news2market -c "SELECT version();"
```

#### Test 2: Verificar conexión a Redis

```bash
# Dentro de Docker
docker exec -it redis redis-cli PING
# Debe responder: PONG

# Localmente
redis-cli PING
```

#### Test 3: Test de extremo a extremo

```bash
# Buscar noticias (puede tardar unos segundos)
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["economia", "mercado"],
    "limit": 5
  }'

# Calcular correlación (requiere datos previos)
curl -X POST http://localhost:8003/correlate \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "metrics": ["volume", "keywords", "sentiment"],
    "lag_days": 0
  }'
```

### 3. Script de Verificación Automática

Ejecuta el script de verificación incluido:

```bash
# Desde la raíz del proyecto
python scripts/verify_system.py
```

Este script verifica:
- Conectividad de todos los servicios
- Estado de la base de datos
- Estado de Redis
- Endpoints críticos

---

## Solución de Problemas

### Problema 1: Puerto ya en uso

**Error**: `Error: bind: address already in use`

**Solución**:
```bash
# Ver qué proceso usa el puerto
# Windows PowerShell:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Matar el proceso o cambiar el puerto en docker-compose.yml
```

### Problema 2: Docker no tiene permisos (Linux)

**Error**: `permission denied while trying to connect to the Docker daemon`

**Solución**:
```bash
# Agregar tu usuario al grupo docker
sudo usermod -aG docker $USER

# Cerrar sesión y volver a iniciar
newgrp docker
```

### Problema 3: Servicio no se conecta a la base de datos

**Error**: `could not connect to server: Connection refused`

**Solución**:
```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Ver logs de PostgreSQL
docker-compose logs postgres

# Reiniciar PostgreSQL
docker-compose restart postgres

# Verificar variables de entorno en docker-compose.yml
```

### Problema 4: Frontend no carga

**Error**: `Failed to fetch` o `Network Error`

**Solución**:
```bash
# Verificar que el API Gateway está corriendo
curl http://localhost:8000/api/v1/health

# Ver logs del frontend
docker-compose logs frontend

# Limpiar caché del navegador
# O abrir en modo incógnito
```

### Problema 5: Análisis de correlación falla

**Error**: `500 Internal Server Error` al calcular correlación

**Solución**:
```bash
# Ver logs del correlation-service
docker-compose logs correlation-service

# Verificar que hay datos de noticias en la base de datos
docker exec -it postgres psql -U news2market -d news2market -c "SELECT COUNT(*) FROM news_articles;"

# Si no hay datos, primero realiza una búsqueda de noticias
```

### Problema 6: Contenedor se reinicia constantemente

**Síntoma**: `docker-compose ps` muestra "Restarting"

**Solución**:
```bash
# Ver logs detallados del servicio problemático
docker-compose logs [service-name]

# Verificar si hay error de sintaxis en el código
# Verificar que todas las dependencias están en requirements.txt

# Reconstruir la imagen
docker-compose build [service-name]
docker-compose up -d [service-name]
```

---

## Comandos Útiles

### Docker Compose

```bash
# Iniciar todos los servicios
docker-compose up -d

# Iniciar solo ciertos servicios
docker-compose up -d postgres redis api-gateway

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (limpieza completa)
docker-compose down -v

# Ver logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f api-gateway

# Reconstruir imágenes
docker-compose build

# Reconstruir un servicio específico
docker-compose build frontend

# Reiniciar un servicio
docker-compose restart correlation-service

# Ejecutar comando en un contenedor
docker-compose exec postgres psql -U news2market

# Ver estado de servicios
docker-compose ps

# Ver uso de recursos
docker stats
```

### Base de Datos

```bash
# Conectar a PostgreSQL
docker exec -it postgres psql -U news2market -d news2market

# Listar tablas
docker exec -it postgres psql -U news2market -d news2market -c "\dt"

# Ver noticias almacenadas
docker exec -it postgres psql -U news2market -d news2market -c "SELECT COUNT(*) FROM news_articles;"

# Ver resultados de correlación
docker exec -it postgres psql -U news2market -d news2market -c "SELECT * FROM correlation_results ORDER BY created_at DESC LIMIT 5;"

# Backup de base de datos
docker exec postgres pg_dump -U news2market news2market > backup.sql

# Restaurar base de datos
docker exec -i postgres psql -U news2market news2market < backup.sql
```

### Redis

```bash
# Conectar a Redis CLI
docker exec -it redis redis-cli

# Ver todas las claves
docker exec -it redis redis-cli KEYS "*"

# Ver valor de una clave
docker exec -it redis redis-cli GET "key_name"

# Limpiar toda la base de datos de Redis
docker exec -it redis redis-cli FLUSHALL
```

### Frontend

```bash
# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Linting
npm run lint
```

---

## Siguiente Pasos

Una vez que el sistema esté funcionando correctamente:

1. **Explora la interfaz**: Abre [http://localhost](http://localhost) en tu navegador
2. **Prueba el análisis**: Ve a la página de Análisis y configura tu primera correlación
3. **Revisa la documentación de la API**: [http://localhost:8000/docs](http://localhost:8000/docs)
4. **Lee la arquitectura**: Consulta `docs/ARCHITECTURE.md` y `docs/AWS_DEPLOYMENT.md`
5. **Contribuye**: Lee `CONTRIBUTING.md` (si existe) para guías de desarrollo

---

## Recursos Adicionales

- **Documentación de FastAPI**: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **Documentación de React**: [https://react.dev/](https://react.dev/)
- **Documentación de Docker**: [https://docs.docker.com/](https://docs.docker.com/)
- **Documentación de PostgreSQL**: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)

---

## Soporte

Si encuentras problemas no cubiertos en esta guía:

1. Revisa los logs: `docker-compose logs -f`
2. Verifica el health check: `curl http://localhost:8000/api/v1/health`
3. Consulta la documentación en `docs/`
4. Abre un issue en GitHub con los detalles del problema

---

**Última actualización**: Enero 2025

¡Feliz desarrollo! 🚀
