@echo off
REM MemoVault - Ollama Docker Setup Script for Windows
setlocal enabledelayedexpansion

echo ===================================
echo MemoVault - Ollama Docker Setup
echo ===================================

REM Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not installed.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not running.
    echo Please start Docker Desktop and try again.
    exit /b 1
)

echo [OK] Docker is installed and running

REM Navigate to project directory
cd /d "%~dp0.."

REM Start Ollama container
echo.
echo Starting Ollama container...
docker compose up -d ollama

REM Wait for Ollama to be ready
echo.
echo Waiting for Ollama to be ready...
set timeout=60
:wait_loop
curl -s http://localhost:11435/api/tags >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Ollama is ready
    goto :pull_models
)
timeout /t 2 /nobreak >nul
set /a timeout-=2
if %timeout% gtr 0 goto :wait_loop

echo Error: Ollama failed to start within 60 seconds
exit /b 1

:pull_models
REM Pull required models
echo.
echo Pulling required models (this may take a few minutes)...
echo   - llama3.1:latest (~4.9GB)
docker exec memovault-ollama ollama pull llama3.1:latest

echo   - nomic-embed-text:latest (~274MB)
docker exec memovault-ollama ollama pull nomic-embed-text:latest

echo.
echo ===================================
echo [OK] Setup Complete!
echo ===================================
echo.
echo Ollama is running at: http://localhost:11435
echo.
echo To manage Ollama:
echo   Start:   docker compose up -d ollama
echo   Stop:    docker compose down
echo   Logs:    docker compose logs -f ollama
echo   Status:  docker compose ps
echo.
echo Next: Restart Claude Code to use MemoVault with Ollama

pause
