@echo off
cd /d %~dp0backend
echo === Limpiando contenedores previos ===
docker-compose down -v

echo.
echo === Iniciando bases de datos ===
docker-compose up -d postgres redis

echo.
echo Esperando 10 segundos...
timeout /t 10 /nobreak >nul

echo.
echo === Iniciando servicios backend ===
docker-compose up -d text-processor correlation-service data-acquisition

echo.
echo Esperando 10 segundos...
timeout /t 10 /nobreak >nul

echo.
echo === Iniciando API Gateway ===
docker-compose up -d api-gateway

echo.
echo Esperando 5 segundos...
timeout /t 5 /nobreak >nul

echo.
echo === Estado de contenedores ===
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo === Sistema iniciado ===
echo Puedes verificar los logs con: docker-compose logs -f
echo Para detener el sistema: docker-compose down
