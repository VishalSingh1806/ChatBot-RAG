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

echo "🔍 Checking if port 8080 is in use..."
used_pid=$(sudo lsof -t -i:8080 || true)
if [ -n "$used_pid" ]; then
    echo "❌ Port 8080 is in use by PID $used_pid. Killing it..."
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

# ─── Step 3: Build & run backend ───────────────────────────────────────────────
echo "📦 Building chatbot-api Docker image..."
cd "$(dirname "$0")/API"
sudo docker build -t chatbot-api .

echo "🚀 Launching chatbot-api…"
sudo docker run -d \
  --name chatbot-api-container \
  --network chat-net \
  --env-file .env \
  -e GOOGLE_APPLICATION_CREDENTIALS=/etc/keys/sa-key.json \
  -v /etc/epr-chatbot/keys/sa-key.json:/etc/keys/sa-key.json:ro \
  -p 8000:8000 \
  chatbot-api

# ─── Step 4: Build & run frontend ──────────────────────────────────────────────
echo "📦 Building chatbot-frontend Docker image..."
cd ../frontend
sudo docker build -t chatbot-frontend .

echo "🚀 Launching chatbot-frontend…"
sudo docker run -d \
  --name chatbot-frontend-container \
  --network chat-net \
  -p 8080:80 \
  chatbot-frontend

# ─── Step 5: Final status & URLs ───────────────────────────────────────────────
echo "✅ All services are up and running:"
sudo docker ps --filter name=chatbot

echo "🌐 Frontend: http://localhost:8080"
echo "🔌 Backend:  http://localhost:8000"
