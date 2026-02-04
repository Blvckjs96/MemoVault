#!/bin/bash
# MemoVault - Ollama Docker Setup Script
# Works on macOS, Linux, and Windows (WSL/Git Bash)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==================================="
echo "MemoVault - Ollama Docker Setup"
echo "==================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running."
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✓ Docker is installed and running"

# Navigate to project directory
cd "$PROJECT_DIR"

# Start Ollama container
echo ""
echo "Starting Ollama container..."
docker compose up -d ollama

# Wait for Ollama to be healthy
echo ""
echo "Waiting for Ollama to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost:11435/api/tags &> /dev/null; then
        echo "✓ Ollama is ready"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "Error: Ollama failed to start within 60 seconds"
    exit 1
fi

# Pull required models
echo ""
echo "Pulling required models (this may take a few minutes)..."
echo "  - llama3.1:latest (~4.9GB)"
docker exec memovault-ollama ollama pull llama3.1:latest

echo "  - nomic-embed-text:latest (~274MB)"
docker exec memovault-ollama ollama pull nomic-embed-text:latest

echo ""
echo "==================================="
echo "✓ Setup Complete!"
echo "==================================="
echo ""
echo "Ollama is running at: http://localhost:11435"
echo ""
echo "To manage Ollama:"
echo "  Start:   docker compose up -d ollama"
echo "  Stop:    docker compose down"
echo "  Logs:    docker compose logs -f ollama"
echo "  Status:  docker compose ps"
echo ""
echo "Next: Restart Claude Code to use MemoVault with Ollama"
