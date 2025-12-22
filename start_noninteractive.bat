@echo off
cd /d %~dp0backend

REM Iniciar servicios en modo detached
docker-compose up -d

REM Esperar un momento
timeout /t 15 /nobreak >nul

REM Mostrar estado
docker-compose ps
