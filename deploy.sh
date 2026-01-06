#!/bin/bash
set -e

echo "🚀 Starting full deployment..."

# ─── Step 0: Ensure shared network exists ───────────────────────────────────────
echo "🌐 Ensuring Docker network 'chat-net' exists..."
if ! sudo docker network inspect chat-net &>/dev/null; then
  sudo docker network create chat-net
  echo "✅ Created network 'chat-net'"
else
  echo "✅ Network 'chat-net' already present"
fi

# ─── Step 1: Pre-cleanup ────────────────────────────────────────────────────────
echo "🧼 Cleaning up old containers and ports..."

# Stop and remove any existing chatbot containers (handles both naming conventions)
for name in chatbot-api-container chatbot-frontend-container chatbot-redis chatbot_redis chatbot_api chatbot_frontend; do
  id=$(sudo docker ps -aq --filter "name=$name")
  if [ -n "$id" ]; then
    echo "🗑️  Removing container: $name"
    sudo docker stop $id 2>/dev/null || true
    sudo docker rm -f $id 2>/dev/null || true
  fi
done

# Prune stopped containers
sudo docker container prune -f

# Kill anything on 80, 443, 8000, 3000, 6379 (Redis)
for port in 80 443 8000 3000 6379; do
  pid=$(sudo lsof -t -i:$port || true)
  if [ -n "$pid" ]; then
    echo "❌ Port $port in use by PID $pid—killing"
    sudo kill -9 $pid
  fi
done

# ─── Step 2: Obtain SSL cert via standalone plugin ─────────────────────────────
DOMAIN="rebot.recircle.in"
EMAIL="admin@recircle.in"  # ← your real email

echo "🔒 Installing Certbot & obtaining certificate for $DOMAIN..."
if ! command -v certbot &>/dev/null; then
  sudo apt update
  sudo apt install -y certbot
fi

# Ensure Nginx is stopped so certbot can bind to :80
sudo systemctl stop nginx 2>/dev/null || true

# Obtain or renew certificate
sudo certbot certonly --standalone \
  --non-interactive --agree-tos \
  --email "$EMAIL" \
  -d "$DOMAIN"

echo "✅ Certificate installed at /etc/letsencrypt/live/$DOMAIN/"

# ─── Step 3: Launch Redis ───────────────────────────────────────────────────────
echo "🔴 Starting Redis container..."
sudo docker run -d \
  --name chatbot-redis \
  --network chat-net \
  -p 6379:6379 \
  redis:alpine

# ─── Step 4: Build & run backend ───────────────────────────────────────────────
echo "📦 Building & launching chatbot-api..."
cd "$(dirname "$0")/API"

# Create ChromaDB directory if it doesn't exist
sudo mkdir -p /var/lib/chatbot/chroma_db

sudo docker build -t chatbot-api .
sudo docker run -d \
  --name chatbot-api-container \
  --network chat-net \
  --env-file .env \
  -e GOOGLE_APPLICATION_CREDENTIALS=/etc/keys/sa-key.json \
  -e REDIS_HOST=chatbot-redis \
  -e CHROMA_DB_PATH=/app/chroma_db \
  -v /etc/epr-chatbot/keys/sa-key.json:/etc/keys/sa-key.json:ro \
  -v /var/lib/chatbot/chroma_db:/app/chroma_db \
  -p 8000:8000 \
  chatbot-api

# ─── Step 5: Build & run frontend ──────────────────────────────────────────────
echo "📦 Building & launching chatbot-frontend..."
cd ../frontend
sudo docker build -t chatbot-frontend .
sudo docker run -d \
  --name chatbot-frontend-container \
  --network chat-net \
  -p 3000:80 \
  chatbot-frontend

# ─── Step 6: Write host‐level Nginx config ─────────────────────────────────────
echo "📝 Writing Nginx SSL proxy config for $DOMAIN..."
sudo bash -c "cat > /etc/nginx/sites-available/chatbot <<'EOF'
# Redirect HTTP → HTTPS
server {
  listen 80;
  server_name $DOMAIN;
  return 301 https://\$host\$request_uri;
}

# HTTPS proxy to frontend container
server {
  listen 443 ssl http2;
  server_name $DOMAIN;

  ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
  ssl_protocols       TLSv1.2 TLSv1.3;
  ssl_ciphers         HIGH:!aNULL:!MD5;

  # Proxy every path to the frontend container
  location / {
    proxy_pass http://localhost:3000;
    proxy_set_header Host              \$host;
    proxy_set_header X-Real-IP         \$remote_addr;
    proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
}
EOF"

# Enable site
sudo ln -sf /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test & reload Nginx
sudo /usr/sbin/nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx

# ─── Step 7: Final status & URLs ───────────────────────────────────────────────
echo "✅ Deployment complete!"
echo "🔒 HTTPS Frontend: https://$DOMAIN"
echo "🔌 Backend API:   http://<your-server-ip>:8000  (internal to nginx via container)"
echo ""
sudo docker ps --filter name=chatbot
