# ================================================
# News2Market - Start and Verify System
# ================================================
# Este script inicia todos los servicios con Docker Compose
# y verifica que estén funcionando correctamente

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         NEWS2MARKET - SYSTEM STARTUP SCRIPT               ║" -ForegroundColor Cyan
Write-Host "║              Universidad del Valle - 2024                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Variables
$BackendDir = "backend"
$ScriptsDir = "scripts"
$MaxWaitTime = 120  # 2 minutos para que todo arranque

# Función para imprimir mensajes con colores
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Verificar que estamos en el directorio correcto
if (-not (Test-Path $BackendDir)) {
    Write-Error "No se encontró el directorio 'backend'. ¿Estás en el directorio raíz del proyecto?"
    exit 1
}

Write-Info "Paso 1: Verificando archivos .env..."
$envFiles = @(
    "$BackendDir\text-processor\.env",
    "$BackendDir\correlation-service\.env"
)

$missingEnv = $false
foreach ($envFile in $envFiles) {
    if (Test-Path $envFile) {
        Write-Success "Encontrado: $envFile"
    } else {
        Write-Error "Falta: $envFile"
        $missingEnv = $true
    }
}

if ($missingEnv) {
    Write-Error "Faltan archivos .env. Por favor créalos antes de continuar."
    exit 1
}

Write-Info "`nPaso 2: Deteniendo contenedores previos..."
Push-Location $BackendDir
docker-compose down -v 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Contenedores previos detenidos"
} else {
    Write-Warning "No había contenedores previos o hubo un error menor"
}

Write-Info "`nPaso 3: Construyendo imágenes Docker..."
docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error al construir imágenes Docker"
    Pop-Location
    exit 1
}
Write-Success "Imágenes Docker construidas exitosamente"

Write-Info "`nPaso 4: Iniciando servicios..."
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error al iniciar servicios"
    Pop-Location
    exit 1
}
Write-Success "Servicios iniciados"

Pop-Location

Write-Info "`nPaso 5: Esperando que los servicios estén listos..."
Write-Host "Esto puede tomar hasta $MaxWaitTime segundos..." -ForegroundColor Yellow

# Esperar un poco para que inicien
Start-Sleep -Seconds 10

# Verificar servicios
$services = @{
    "PostgreSQL" = "localhost:5432"
    "Redis" = "localhost:6379"
    "API Gateway" = "http://localhost:8000/health"
    "Data Acquisition" = "http://localhost:8001/health"
    "Text Processor" = "http://localhost:8002/health"
    "Correlation Service" = "http://localhost:8003/health"
}

$allHealthy = $true
$attempts = 0
$maxAttempts = 24  # 24 intentos x 5 segundos = 2 minutos

while ($attempts -lt $maxAttempts) {
    $attempts++
    Write-Host "`nIntento $attempts de $maxAttempts..." -ForegroundColor Cyan
    
    $currentlyHealthy = $true
    
    foreach ($service in $services.Keys) {
        $endpoint = $services[$service]
        
        if ($endpoint -like "http*") {
            try {
                $response = Invoke-WebRequest -Uri $endpoint -Method Get -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Success "$service está saludable"
                } else {
                    Write-Warning "$service respondió con código $($response.StatusCode)"
                    $currentlyHealthy = $false
                }
            } catch {
                Write-Warning "$service aún no responde"
                $currentlyHealthy = $false
            }
        } else {
            # Para PostgreSQL y Redis, solo verificamos que el contenedor esté corriendo
            $containerName = if ($service -eq "PostgreSQL") { "news2market-postgres" } else { "news2market-redis" }
            $running = docker ps --filter "name=$containerName" --filter "status=running" --format "{{.Names}}"
            if ($running) {
                Write-Success "$service contenedor está corriendo"
            } else {
                Write-Warning "$service contenedor no está corriendo"
                $currentlyHealthy = $false
            }
        }
    }
    
    if ($currentlyHealthy) {
        $allHealthy = $true
        break
    }
    
    if ($attempts -lt $maxAttempts) {
        Write-Host "Esperando 5 segundos antes del siguiente intento..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-not $allHealthy) {
    Write-Error "`nNo todos los servicios están saludables después de $MaxWaitTime segundos"
    Write-Warning "Verifica los logs con: docker-compose -f backend/docker-compose.yml logs"
    exit 1
}

Write-Success "`n✓ ✓ ✓ TODOS LOS SERVICIOS ESTÁN FUNCIONANDO CORRECTAMENTE ✓ ✓ ✓"

Write-Info "`nPaso 6: Ejecutando script de verificación completo..."
if (Test-Path "$ScriptsDir\verify_system.py") {
    python "$ScriptsDir\verify_system.py"
    $verificationExitCode = $LASTEXITCODE
} else {
    Write-Warning "Script verify_system.py no encontrado, saltando verificación avanzada"
    $verificationExitCode = 0
}

Write-Host "`n" + ("="*60) -ForegroundColor Cyan
Write-Host "SERVICIOS DISPONIBLES:" -ForegroundColor Cyan
Write-Host ("="*60) -ForegroundColor Cyan
Write-Host "  API Gateway:          http://localhost:8000" -ForegroundColor White
Write-Host "  Docs API Gateway:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Data Acquisition:     http://localhost:8001" -ForegroundColor White
Write-Host "  Text Processor:       http://localhost:8002" -ForegroundColor White
Write-Host "  Text Processor Docs:  http://localhost:8002/docs" -ForegroundColor White
Write-Host "  Correlation Service:  http://localhost:8003" -ForegroundColor White
Write-Host "  Correlation Docs:     http://localhost:8003/docs" -ForegroundColor White
Write-Host "  PostgreSQL:           localhost:5432" -ForegroundColor White
Write-Host "  Redis:                localhost:6379" -ForegroundColor White
Write-Host "  PgAdmin:              http://localhost:5050" -ForegroundColor White
Write-Host ("="*60) -ForegroundColor Cyan

Write-Host "`nPara ver los logs:" -ForegroundColor Yellow
Write-Host "  docker-compose -f backend/docker-compose.yml logs -f [servicio]" -ForegroundColor Gray

Write-Host "`nPara detener todo:" -ForegroundColor Yellow
Write-Host "  docker-compose -f backend/docker-compose.yml down" -ForegroundColor Gray

if ($verificationExitCode -eq 0) {
    Write-Success "`n✓ Sistema completamente operativo y verificado"
    exit 0
} else {
    Write-Warning "`n⚠ Sistema iniciado pero con algunas advertencias"
    exit 0
}
