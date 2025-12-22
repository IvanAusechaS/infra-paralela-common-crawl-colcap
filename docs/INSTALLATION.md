# 📦 Guía de Instalación y Configuración - News2Market

## Tabla de Contenidos
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación de Herramientas Base](#instalación-de-herramientas-base)
- [Configuración de Python](#configuración-de-python)
- [Configuración de Node.js](#configuración-de-nodejs)
- [Instalación de Docker](#instalación-de-docker)
- [Instalación de Kubernetes](#instalación-de-kubernetes)
- [Configuración de AWS CLI](#configuración-de-aws-cli)
- [Configuración del Proyecto](#configuración-del-proyecto)
- [Ejecución Local](#ejecución-local)
- [Verificación de la Instalación](#verificación-de-la-instalación)

---

## Requisitos del Sistema

### Mínimos
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disco**: 20 GB libres
- **SO**: Windows 10/11, macOS 11+, Linux (Ubuntu 20.04+)

### Recomendados
- **CPU**: 8 cores
- **RAM**: 16 GB
- **Disco**: 50 GB SSD
- **SO**: Ubuntu 22.04 LTS o macOS 13+

---

## Instalación de Herramientas Base

### 1. Git

#### Windows
```powershell
# Opción 1: Descargar instalador
# https://git-scm.com/download/win

# Opción 2: Con winget
winget install --id Git.Git -e --source winget

# Verificar instalación
git --version
```

#### macOS
```bash
# Opción 1: Homebrew (recomendado)
brew install git

# Opción 2: Xcode Command Line Tools
xcode-select --install

# Verificar
git --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install git -y

# Verificar
git --version
```

**Versión mínima requerida**: Git 2.30+

---

## Configuración de Python

### 1. Instalar Python 3.11+

#### Windows
```powershell
# Opción 1: Desde python.org
# https://www.python.org/downloads/

# Opción 2: Con winget
winget install Python.Python.3.11

# Opción 3: Con Chocolatey
choco install python --version=3.11.0

# Agregar al PATH durante instalación ✅
# Verificar
python --version
python -m pip --version
```

#### macOS
```bash
# Opción 1: Homebrew (recomendado)
brew install python@3.11

# Opción 2: pyenv (para múltiples versiones)
brew install pyenv
pyenv install 3.11.7
pyenv global 3.11.7

# Agregar a .zshrc o .bash_profile
echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"' >> ~/.zshrc

# Verificar
python3 --version
pip3 --version
```

#### Linux (Ubuntu/Debian)
```bash
# Ubuntu 22.04 incluye Python 3.10, instalar 3.11
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Establecer como predeterminado (opcional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Instalar pip
sudo apt install python3-pip -y

# Verificar
python3 --version
pip3 --version
```

### 2. Instalar virtualenv (opcional pero recomendado)
```bash
# Instalar virtualenv globalmente
pip install virtualenv

# O usar venv (incluido en Python 3.3+)
python -m venv --help
```

### 3. Dependencias de Python para el proyecto

Crear entorno virtual para el backend:
```bash
# Navegar al proyecto
cd infra-paralela-common-crawl-colcap/backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
.\venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate

# Instalar dependencias de cada servicio
pip install --upgrade pip

# API Gateway
cd api-gateway
pip install -r requirements.txt

# Data Acquisition
cd ../data-acquisition
pip install -r requirements.txt

# Text Processor (cuando se cree)
cd ../text-processor
pip install -r requirements.txt

# Correlation Service (cuando se cree)
cd ../correlation-service
pip install -r requirements.txt
```

**Librerías principales**:
- fastapi>=0.104.0
- uvicorn[standard]>=0.24.0
- httpx>=0.25.0
- pydantic>=2.0.0
- sqlalchemy>=2.0.0
- asyncpg>=0.29.0
- redis>=5.0.0
- pandas>=2.1.0
- numpy>=1.24.0
- scipy>=1.11.0
- beautifulsoup4>=4.12.0
- warcio>=1.7.0
- boto3>=1.28.0 (para AWS S3)
- python-dotenv>=1.0.0

---

## Configuración de Node.js

### 1. Instalar Node.js LTS (v20+)

#### Windows
```powershell
# Opción 1: Desde nodejs.org (recomendado)
# https://nodejs.org/en/download/

# Opción 2: Con winget
winget install OpenJS.NodeJS.LTS

# Opción 3: Con Chocolatey
choco install nodejs-lts

# Verificar
node --version
npm --version
```

#### macOS
```bash
# Opción 1: Homebrew
brew install node@20

# Opción 2: nvm (recomendado para desarrollo)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.zshrc
nvm install 20
nvm use 20

# Verificar
node --version
npm --version
```

#### Linux (Ubuntu/Debian)
```bash
# Opción 1: NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Opción 2: nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# Verificar
node --version
npm --version
```

**Versión mínima requerida**: Node.js 18+ (recomendado 20 LTS)

### 2. Instalar dependencias del frontend

```bash
# Navegar al directorio frontend
cd infra-paralela-common-crawl-colcap/frontend

# Instalar dependencias
npm install

# O con yarn
npm install -g yarn
yarn install

# O con pnpm (más rápido)
npm install -g pnpm
pnpm install
```

**Dependencias principales**:
- react@18+
- react-dom@18+
- vite@5+
- sass@1.69+
- recharts@2.10+
- axios@1.6+
- react-router-dom@6+
- zustand o @reduxjs/toolkit
- framer-motion (para animaciones)

---

## Instalación de Docker

### 1. Docker Engine

#### Windows
```powershell
# Opción 1: Docker Desktop (recomendado)
# https://www.docker.com/products/docker-desktop/

# Descargar e instalar Docker Desktop
# Requiere: WSL 2 habilitado

# Verificar
docker --version
docker-compose --version
```

**Configurar WSL 2** (Windows):
```powershell
# Habilitar WSL
wsl --install

# Establecer WSL 2 como predeterminado
wsl --set-default-version 2

# Instalar Ubuntu
wsl --install -d Ubuntu-22.04
```

#### macOS
```bash
# Opción 1: Docker Desktop (recomendado)
# https://www.docker.com/products/docker-desktop/

# Opción 2: Homebrew
brew install --cask docker

# Iniciar Docker Desktop desde Applications

# Verificar
docker --version
docker-compose --version
```

#### Linux (Ubuntu/Debian)
```bash
# Desinstalar versiones antiguas
sudo apt-get remove docker docker-engine docker.io containerd runc

# Instalar dependencias
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Agregar clave GPG de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Agregar repositorio
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Agregar usuario al grupo docker (para ejecutar sin sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
docker compose version
```

**Versión mínima requerida**: Docker 24+, Docker Compose 2.20+

### 2. Configurar recursos de Docker

**Docker Desktop (Windows/macOS)**:
- Abrir Docker Desktop → Settings → Resources
- **CPU**: Asignar mínimo 4 cores
- **Memory**: Asignar mínimo 6 GB
- **Swap**: 2 GB
- **Disk image size**: 50 GB

---

## Instalación de Kubernetes

### 1. kubectl (CLI de Kubernetes)

#### Windows
```powershell
# Opción 1: Con Chocolatey
choco install kubernetes-cli

# Opción 2: Con curl
curl.exe -LO "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe"

# Mover a C:\Windows\System32 o agregar al PATH

# Verificar
kubectl version --client
```

#### macOS
```bash
# Opción 1: Homebrew
brew install kubectl

# Opción 2: Con curl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verificar
kubectl version --client
```

#### Linux
```bash
# Opción 1: Snap
sudo snap install kubectl --classic

# Opción 2: Con curl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verificar
kubectl version --client
```

**Versión mínima requerida**: kubectl 1.28+

### 2. Minikube (para pruebas locales)

#### Windows
```powershell
# Con Chocolatey
choco install minikube

# Con winget
winget install Kubernetes.minikube

# Verificar
minikube version
```

#### macOS
```bash
# Con Homebrew
brew install minikube

# Verificar
minikube version
```

#### Linux
```bash
# Con curl
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Verificar
minikube version
```

### 3. Iniciar cluster local con Minikube

```bash
# Iniciar Minikube con Docker driver
minikube start --driver=docker --cpus=4 --memory=8192 --disk-size=20g

# Verificar
minikube status
kubectl cluster-info
kubectl get nodes

# Habilitar dashboard (opcional)
minikube dashboard

# Habilitar ingress (opcional)
minikube addons enable ingress
```

### 4. Helm (gestor de paquetes para Kubernetes)

#### Windows
```powershell
choco install kubernetes-helm
```

#### macOS
```bash
brew install helm
```

#### Linux
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

**Verificar**:
```bash
helm version
```

---

## Configuración de AWS CLI

### 1. Instalar AWS CLI v2

#### Windows
```powershell
# Descargar e instalar desde:
# https://awscli.amazonaws.com/AWSCLIV2.msi

# O con Chocolatey
choco install awscli

# Verificar
aws --version
```

#### macOS
```bash
# Con Homebrew
brew install awscli

# O con instalador oficial
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verificar
aws --version
```

#### Linux
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verificar
aws --version
```

**Versión mínima requerida**: AWS CLI 2.13+

### 2. Configurar credenciales de AWS

```bash
# Configurar credenciales
aws configure

# Se solicitará:
# AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name: us-east-1
# Default output format: json

# Verificar configuración
aws sts get-caller-identity
```

**Obtener credenciales**:
1. Acceder a AWS Console
2. IAM → Users → Tu usuario
3. Security credentials → Create access key
4. Guardar Access Key ID y Secret Access Key

### 3. Instalar eksctl (para AWS EKS)

#### Windows
```powershell
choco install eksctl
```

#### macOS
```bash
brew tap weaveworks/tap
brew install weaveworks/tap/eksctl
```

#### Linux
```bash
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Verificar
eksctl version
```

### 4. Instalar AWS IAM Authenticator

#### Windows
```powershell
# Descargar desde GitHub
curl -o aws-iam-authenticator.exe https://amazon-eks.s3.us-west-2.amazonaws.com/1.21.2/2021-07-05/bin/windows/amd64/aws-iam-authenticator.exe

# Mover a C:\Windows\System32 o agregar al PATH
```

#### macOS/Linux
```bash
# Incluido con eksctl, o instalar manualmente
curl -o aws-iam-authenticator https://amazon-eks.s3.us-west-2.amazonaws.com/1.21.2/2021-07-05/bin/linux/amd64/aws-iam-authenticator
chmod +x ./aws-iam-authenticator
sudo mv ./aws-iam-authenticator /usr/local/bin

# Verificar
aws-iam-authenticator version
```

---

## Configuración del Proyecto

### 1. Clonar el repositorio

```bash
# Clonar proyecto
git clone https://github.com/tu-usuario/infra-paralela-common-crawl-colcap.git
cd infra-paralela-common-crawl-colcap

# Ver ramas
git branch -a

# Cambiar a rama de desarrollo
git checkout develop
```

### 2. Configurar variables de entorno

#### Backend

Crear archivo `.env` en el directorio raíz del backend:

```bash
# backend/.env
# ==============================================
# GENERAL CONFIG
# ==============================================
ENV=development
LOG_LEVEL=INFO

# ==============================================
# API GATEWAY
# ==============================================
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000
HTTP_TIMEOUT=30
CONNECT_TIMEOUT=5

# ==============================================
# SERVICES URLs
# ==============================================
DATA_SERVICE_URL=http://localhost:8001
PROCESS_SERVICE_URL=http://localhost:8002
CORRELATION_SERVICE_URL=http://localhost:8003

# ==============================================
# DATABASE
# ==============================================
DATABASE_URL=postgresql://user:password@localhost:5432/newsdb
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ==============================================
# REDIS
# ==============================================
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=10

# ==============================================
# COMMON CRAWL CONFIG
# ==============================================
USE_MOCK_MODE=true
COMMON_CRAWL_MODE=auto
COMMON_CRAWL_BUCKET=commoncrawl
MAX_RECORDS_PER_FILE=50
MAX_WARC_FILES=5
MAX_TOTAL_RECORDS=100

# ==============================================
# AWS CONFIG (para producción)
# ==============================================
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
AWS_ECR_REPOSITORY=news2market

# ==============================================
# COLCAP DATA SOURCE
# ==============================================
COLCAP_API_URL=https://api.example.com/colcap
COLCAP_API_KEY=your-api-key
```

#### Frontend

Crear archivo `.env` en el directorio frontend:

```bash
# frontend/.env
# ==============================================
# API CONFIG
# ==============================================
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# ==============================================
# APP CONFIG
# ==============================================
VITE_APP_TITLE=News2Market
VITE_APP_VERSION=1.0.0
VITE_ENABLE_MOCK=false
```

### 3. Inicializar base de datos

```bash
# Con Docker Compose (recomendado)
cd backend
docker-compose up -d postgres

# O instalar PostgreSQL localmente
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS
brew install postgresql@15
brew services start postgresql@15

# Crear base de datos y usuario
psql -U postgres
CREATE DATABASE newsdb;
CREATE USER user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE newsdb TO user;
\q

# Ejecutar migraciones (desde backend/)
cd data-acquisition
python -c "from database import init_db; init_db()"
```

### 4. Inicializar Redis

```bash
# Con Docker (recomendado)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# O instalar localmente
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Verificar
redis-cli ping
# Debe responder: PONG
```

---

## Ejecución Local

### Opción 1: Con Docker Compose (Recomendado)

```bash
# Navegar al backend
cd backend

# Construir y levantar todos los servicios
docker-compose up --build

# En segundo plano
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

**Servicios disponibles**:
- API Gateway: http://localhost:8000
- Data Acquisition: http://localhost:8001
- Text Processor: http://localhost:8002
- Correlation: http://localhost:8003
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Docs API Gateway: http://localhost:8000/docs

### Opción 2: Ejecución manual (desarrollo)

#### Terminal 1: PostgreSQL + Redis
```bash
# Ya deben estar corriendo (ver sección anterior)
```

#### Terminal 2: API Gateway
```bash
cd backend/api-gateway
source ../venv/bin/activate  # o .\venv\Scripts\Activate.ps1 en Windows
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 3: Data Acquisition
```bash
cd backend/data-acquisition
source ../venv/bin/activate
python -c "from database import init_db; init_db()"
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 4: Text Processor
```bash
cd backend/text-processor
source ../venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8002 --reload
```

#### Terminal 5: Correlation Service
```bash
cd backend/correlation-service
source ../venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8003 --reload
```

#### Terminal 6: Frontend
```bash
cd frontend
npm run dev
# O yarn dev / pnpm dev

# Frontend disponible en http://localhost:3000
```

---

## Verificación de la Instalación

### 1. Verificar Python y dependencias
```bash
python --version  # Debe ser 3.11+
pip list | grep fastapi
pip list | grep pandas
pip list | grep redis
```

### 2. Verificar Node.js y dependencias
```bash
node --version  # Debe ser 18+
npm --version
npm list -g --depth=0
```

### 3. Verificar Docker
```bash
docker --version
docker ps
docker images
docker-compose --version
```

### 4. Verificar Kubernetes
```bash
kubectl version --client
kubectl cluster-info
kubectl get nodes
```

### 5. Verificar AWS CLI
```bash
aws --version
aws sts get-caller-identity
eksctl version
```

### 6. Verificar servicios locales

#### Health checks
```bash
# API Gateway
curl http://localhost:8000/health

# Data Acquisition
curl http://localhost:8001/health

# Text Processor
curl http://localhost:8002/health

# Correlation Service
curl http://localhost:8003/health
```

#### Test de pipeline completo
```bash
# Iniciar análisis
curl -X POST http://localhost:8000/start-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "limit": 50
  }'
```

### 7. Verificar base de datos
```bash
# Conectar a PostgreSQL
psql -h localhost -U user -d newsdb

# Verificar tablas
\dt

# Verificar conexión desde Python
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:password@localhost:5432/newsdb')
print('Conexión exitosa' if engine.connect() else 'Error')
"
```

### 8. Verificar Redis
```bash
# CLI de Redis
redis-cli

# Dentro de redis-cli
PING
INFO server
KEYS *
EXIT
```

### 9. Verificar frontend
```bash
# Navegar a http://localhost:3000
# Debe mostrar la interfaz de News2Market

# Build de producción
cd frontend
npm run build

# Debe crear carpeta dist/ sin errores
```

---

## Solución de Problemas Comunes

### Error: Puerto ya en uso
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### Error: Docker no está corriendo
```bash
# Iniciar Docker Desktop (Windows/macOS)
# O en Linux
sudo systemctl start docker
```

### Error: Permisos de Docker (Linux)
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Error: Python module not found
```bash
# Asegurar que el entorno virtual está activado
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: Cannot connect to database
```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep postgres
# O
sudo systemctl status postgresql

# Verificar credenciales en .env
cat backend/.env | grep DATABASE_URL
```

### Error: Redis connection refused
```bash
# Verificar que Redis está corriendo
docker ps | grep redis
# O
sudo systemctl status redis

# Iniciar Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

---

## Siguientes Pasos

Una vez completada la instalación:

1. ✅ Leer [ARCHITECTURE.md](./ARCHITECTURE.md) para entender el diseño del sistema
2. ✅ Revisar [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) para despliegue en la nube
3. ✅ Explorar los endpoints en http://localhost:8000/docs
4. ✅ Ejecutar tests con `pytest backend/tests/`
5. ✅ Probar frontend en http://localhost:3000

---

**Última actualización**: Diciembre 2024
**Versión**: 1.0.0
**Soporte**: Consultar GitHub Issues
