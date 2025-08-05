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

echo "🔍 Checking if port 443 is in use..."
used_pid=$(sudo lsof -t -i:443 || true)
if [ -n "$used_pid" ]; then
    echo "❌ Port 443 is in use by PID $used_pid. Killing it..."
    sudo kill -9 $used_pid
fi

# ─── Step 2: Install and configure SSL certificate ────────────────────────────
echo "🔒 Setting up SSL certificate with certbot..."

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
else
    echo "✅ Certbot already installed"
fi

# Stop nginx if running to allow certbot to bind to port 80
sudo systemctl stop nginx 2>/dev/null || true

# Install nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing nginx..."
    sudo apt install -y nginx
else
    echo "✅ Nginx already installed"
fi

# Create nginx configuration for the domain
echo "📝 Creating nginx configuration..."
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled

cat << 'EOF' | sudo tee /etc/nginx/sites-available/chatbot > /dev/null
server {
    listen 80;
    server_name rebot.recircle.in;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name rebot.recircle.in;
    
    # SSL configuration will be added by certbot
    
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Get SSL certificate
echo "🔒 Obtaining SSL certificate for rebot.recircle.in..."
sudo certbot --nginx -d rebot.recircle.in --non-interactive --agree-tos --email admin@recircle.in --redirect

# Setup auto-renewal
echo "⚡ Setting up SSL certificate auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo "✅ SSL certificate setup complete!"

# ─── Step 3: Fetch service-account key ─────────────────────────────────────────
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

# ─── Step 4: Start Redis ───────────────────────────────────────────────────────
echo "🔴 Starting Redis container..."
sudo docker run -d \
  --name chatbot-redis \
  --network chat-net \
  -p 6379:6379 \
  redis:alpine

# ─── Step 5: Build & run backend ───────────────────────────────────────────────
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

# ─── Step 6: Build & run frontend ──────────────────────────────────────────────
echo "📦 Building chatbot-frontend Docker image..."
cd ../frontend
sudo docker build -t chatbot-frontend .

echo "🚀 Launching chatbot-frontend…"
sudo docker run -d \
  --name chatbot-frontend-container \
  --network chat-net \
  -p 3000:80 \
  chatbot-frontend

# ─── Step 7: Update nginx configuration for Docker containers ─────────────────
echo "🔄 Updating nginx configuration for container ports..."

cat << 'EOF' | sudo tee /etc/nginx/sites-available/chatbot > /dev/null
server {
    listen 80;
    server_name rebot.recircle.in;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name rebot.recircle.in;
    
    # SSL configuration managed by certbot
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Reload nginx configuration
sudo nginx -t && sudo systemctl reload nginx

# ─── Step 8: Final status & URLs ───────────────────────────────────────────────
echo "✅ All services are up and running:"
sudo docker ps --filter name=chatbot

echo ""
echo "🌟 ===== DEPLOYMENT COMPLETE WITH SSL ===== 🌟"
echo "🔒 HTTPS Frontend: https://rebot.recircle.in"
echo "🌐 HTTP Frontend (IP): http://34.173.78.39:3000"
echo "🔌 Backend API: http://34.173.78.39:8000"
echo ""
echo "📋 Service Status:"
echo "   - Redis: chatbot-redis (internal)"
echo "   - API: chatbot-api-container:8000"
echo "   - Frontend: chatbot-frontend-container:3000"
echo "   - Nginx: SSL proxy on ports 80/443"
echo ""
echo "✨ Your bot is now accessible via HTTPS at: https://rebot.recircle.in"
echo "🔒 SSL certificate auto-renewal is configured"
echo "⚡ Backend health check: http://34.173.78.39:8000/"
