#!/bin/bash
set -e

# =================================================================
# AI SRS Engineer - Server One-Click Deployment Script
# Supports: Ubuntu, Debian, CentOS, AlmaLinux, RockyLinux
# =================================================================

echo "=========================================================="
echo "🚀 Starting AI SRS Engineer Deployment..."
echo "=========================================================="

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed successfully."
fi

# 2. Check for Docker Compose
if ! docker compose version &> /dev/null; then
    echo "⚠️  Docker Compose plugin not detected. Installing..."
    apt-get update && apt-get install -y docker-compose-plugin || yum install -y docker-compose-plugin
fi

# 3. Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env. Please update it with your real GROQ_API_KEY and passwords:"
        echo "  nano .env"
        echo "Then re-run this script."
        exit 1
    else
        echo "❌ .env.example not found. Please provide an environment file."
        exit 1
    fi
fi

# 4. Build and start services
echo "📦 Building and starting containers with Docker Compose..."
docker compose down || true
docker compose up -d --build

# 5. Wait for services to be ready
echo "⏳ Waiting for services to become healthy..."
sleep 10

# 6. Run verification
echo "🔍 Running deployment verification..."
chmod +x ./verify.sh 2>/dev/null || true
if [ -f ./verify.sh ]; then
    ./verify.sh
else
    echo "Containers status:"
    docker compose ps
fi

echo "=========================================================="
echo "🎉 Deployment complete!"
echo "Public Access: http://$(curl -s ifconfig.me || echo 'YOUR_SERVER_IP')"
echo "API Docs:     http://$(curl -s ifconfig.me || echo 'YOUR_SERVER_IP'):8000/docs"
echo "=========================================================="
