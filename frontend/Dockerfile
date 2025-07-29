# Step 1: Build the frontend using Node.js
FROM node:18 AS builder

WORKDIR /app
COPY . .

# Install deps and build
RUN npm install && npm run build

# Step 2: Serve using nginx
FROM nginx:alpine

# Copy built frontend files to nginx's public folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Optional: override default nginx config
# COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
