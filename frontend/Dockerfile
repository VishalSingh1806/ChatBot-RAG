# Step 1: Build the frontend using Node.js
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies to leverage Docker cache
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the source code and build the app
COPY . .
RUN npm run build

# Step 2: Serve using nginx
FROM nginx:alpine

# Copy built frontend files to nginx's public folder
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
