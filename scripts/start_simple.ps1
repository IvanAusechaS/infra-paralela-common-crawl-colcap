# Simple test script to start system step by step

$projectPath = "c:\Users\lu\Downloads\Proyectos\Infraestructuras\infra-paralela-common-crawl-colcap"
$composeFile = "$projectPath\backend\docker-compose.yml"

Write-Host "=== Testing Docker Compose ===" -ForegroundColor Cyan

# Test 1: Validate compose file
Write-Host "`n1. Validating docker-compose.yml..." -ForegroundColor Yellow
docker-compose -f $composeFile config --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ docker-compose.yml is valid" -ForegroundColor Green
} else {
    Write-Host "✗ docker-compose.yml has errors" -ForegroundColor Red
    exit 1
}

# Test 2: Clean up
Write-Host "`n2. Cleaning up previous containers..." -ForegroundColor Yellow
docker-compose -f $composeFile down -v 2>&1 | Out-Null

# Test 3: Start only databases first
Write-Host "`n3. Starting databases (postgres + redis)..." -ForegroundColor Yellow
docker-compose -f $composeFile up -d postgres redis

Start-Sleep -Seconds 15

# Check if databases are running
$postgresRunning = docker ps --filter "name=news2market-postgres" --filter "status=running" --format "{{.Names}}"
$redisRunning = docker ps --filter "name=news2market-redis" --filter "status=running" --format "{{.Names}}"

if ($postgresRunning -and $redisRunning) {
    Write-Host "✓ Databases are running" -ForegroundColor Green
} else {
    Write-Host "✗ Databases failed to start" -ForegroundColor Red
    docker-compose -f $composeFile logs postgres redis
    exit 1
}

# Test 4: Start backend services
Write-Host "`n4. Starting backend services..." -ForegroundColor Yellow
docker-compose -f $composeFile up -d data-acquisition text-processor correlation-service

Start-Sleep -Seconds 20

# Test 5: Start API Gateway
Write-Host "`n5. Starting API Gateway..." -ForegroundColor Yellow
docker-compose -f $composeFile up -d api-gateway

Start-Sleep -Seconds 10

# Final check
Write-Host "`n6. Checking all services..." -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n=== System started! ===" -ForegroundColor Green
Write-Host "Services available at:" -ForegroundColor Cyan
Write-Host "  - API Gateway: http://localhost:8000" -ForegroundColor White
Write-Host "  - Text Processor: http://localhost:8002" -ForegroundColor White
Write-Host "  - Correlation Service: http://localhost:8003" -ForegroundColor White
