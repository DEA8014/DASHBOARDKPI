@echo off
title Dashboard P&L El Hornero - Puerto 8089
cd /d "%~dp0"
where docker >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Desplegando contenedor Docker en puerto 8089...
    docker compose up -d --build
    start http://localhost:8089
) else (
    echo Iniciando servidor autodesplegable en http://localhost:8089 ...
    start http://localhost:8089
    python server.py
)
