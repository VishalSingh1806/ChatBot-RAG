#!/bin/bash
set -e

echo "🚀 Starting full deployment..."

# ─── Step 0: Ensure shared network exists ───────────────────────────────────────
echo "🌐 Ensuring Docker network 'chat-net' exists..."
if ! docker network inspect chat-net &>/dev/null; then
  docker network create chat-net
  echo "✅ Created network 'chat-net'"
else
  echo "✅ Network 'chat-net' already present"
fi

# ─── Step 1: Pre-cleanup ────────────────────────────────────────────────────────
echo "🧼 Removing all stopped containers..."
sudo docker container prune -f

echo "🧼 Removing existing chatbot-* containers (if any)..."
existing_containers=$(sudo docker ps -aq --filter "name=chatbot-")
if [ -n "$existing_containers" ]; then
    sudo docker rm -f $existing_containers
fi

echo "🧼 Removing existing Redis container (if any)..."
existing_redis=$(sudo docker ps -aq --filter "name=chatbot-redis")
if [ -n "$existing_redis" ]; then
    sudo docker rm -f $existing_redis
fi

echo "🔍 Checking if port 80 is in use..."
used_pid=$(sudo lsof -t -i:80 || true)
if [ -n "$used_pid" ]; then
    echo "❌ Port 80 is in use by PID $used_pid. Killing it..."
    sudo kill -9 $used_pid
fi

echo "🔍 Checking if port 8000 is in use..."
used_pid=$(sudo lsof -t -i:8000 || true)
if [ -n "$used_pid" ]; then
    echo "❌ Port 8000 is in use by PID $used_pid. Killing it..."
    sudo kill -9 $used_pid
fi

# ─── Step 2: Fetch service-account key ─────────────────────────────────────────
echo "🔐 Ensuring gsutil is available..."
if ! command -v gsutil &> /dev/null; then
  echo "❌ gsutil not found. Please install the Google Cloud SDK and retry." >&2
  exit 1
fi

echo "🔐 Fetching service-account key from GCS…"
sudo mkdir -p /etc/epr-chatbot/keys
sudo chmod 700 /etc/epr-chatbot/keys

sudo gsutil cp gs://epr-bucket/epr-chatbot-443706-ede5db0d0b98.json \
    /etc/epr-chatbot/keys/sa-key.json

sudo chmod 600 /etc/epr-chatbot/keys/sa-key.json
echo "🔐 Service account key stored at /etc/epr-chatbot/keys/sa-key.json"

# ─── Step 3: Start Redis ───────────────────────────────────────────────────────
echo "🔴 Starting Redis container..."
sudo docker run -d \
  --name chatbot-redis \
  --network chat-net \
  -p 6379:6379 \
  redis:alpine

# ─── Step 4: Build & run backend ───────────────────────────────────────────────
echo "📦 Building chatbot-api Docker image..."
cd "$(dirname "$0")/API"
sudo docker build -t chatbot-api .

echo "🚀 Launching chatbot-api…"
sudo docker run -d \
  --name chatbot-api-container \
  --network chat-net \
  --env-file .env \
  -e GOOGLE_APPLICATION_CREDENTIALS=/etc/keys/sa-key.json \
  -e REDIS_HOST=chatbot-redis \
  -v /etc/epr-chatbot/keys/sa-key.json:/etc/keys/sa-key.json:ro \
  -p 8000:8000 \
  chatbot-api

# ─── Step 5: Build & run frontend ──────────────────────────────────────────────
echo "📦 Building chatbot-frontend Docker image..."
cd ../frontend
sudo docker build -t chatbot-frontend .

echo "🚀 Launching chatbot-frontend…"
sudo docker run -d \
  --name chatbot-frontend-container \
  --network chat-net \
  -p 80:80 \
  chatbot-frontend

# ─── Step 6: Final status & URLs ───────────────────────────────────────────────
echo "✅ All services are up and running:"
sudo docker ps --filter name=chatbot

echo ""
echo "🌟 ===== DEPLOYMENT COMPLETE ===== 🌟"
echo "🌐 Frontend: http://rebot.recircle.in"
echo "🌐 Frontend (IP): http://34.173.78.39"
echo "🔌 Backend:  http://34.173.78.39:8000"
echo ""
echo "📋 Service Status:"
echo "   - Redis: chatbot-redis (internal)"
echo "   - API: chatbot-api-container:8000"
echo "   - Frontend: chatbot-frontend-container:80"
echo ""
echo "✨ Your bot is now accessible at: http://rebot.recircle.in"
echo "⚡ Backend health check: http://34.173.78.39:8000/"
