#!/bin/bash
set -e

echo "🚀 Starting full deployment..."

# 🧼 Step 0: Pre-cleanup

echo "🧼 Removing all stopped containers..."
sudo docker container prune -f

echo "🧼 Removing existing chatbot-* containers (if any)..."
existing_containers=$(sudo docker ps -aq --filter "name=chatbot-")
if [ -n "$existing_containers" ]; then
    sudo docker rm -f $existing_containers
fi

# 🧼 Optional: Kill any process using port 8080 (change to 80 or 3000 if needed)
echo "🔍 Checking if port 8080 is in use..."
used_pid=$(sudo lsof -t -i:8080 || true)
if [ -n "$used_pid" ]; then
    echo "❌ Port 8080 is in use by PID $used_pid. Killing it..."
    sudo kill -9 $used_pid
fi

# 1️⃣ BACKEND SETUP
echo "📦 Backend: Building chatbot-api..."
cd "$(dirname "$0")/API"
sudo docker build -t chatbot-api .

echo "🚀 Running chatbot-api..."
sudo docker run -d --env-file .env -p 8000:8000 --name chatbot-api-container chatbot-api

# 2️⃣ FRONTEND SETUP
echo "📦 Frontend: Building chatbot-frontend..."
cd ../frontend
sudo docker build -t chatbot-frontend .

echo "🚀 Running chatbot-frontend..."
sudo docker run -d -p 8080:80 --name chatbot-frontend-container chatbot-frontend

# 3️⃣ STATUS CHECK
echo "✅ All services are up and running:"
sudo docker ps --filter name=chatbot

# 4️⃣ Output helpful URLs
echo "🌐 Frontend is available at: http://localhost:8080"
echo "🔌 Backend API is available at: http://localhost:8000"

# Optional: tail logs
# sudo docker logs -f chatbot-api-container
