# Frontend Dashboard Production Image
# Multi-stage build: build static assets with Node, serve via Nginx

FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy rest of source
COPY . .

# Build-time API endpoint (provided via docker-compose build args)
ARG REACT_APP_API_URL
ENV VITE_API_URL=${REACT_APP_API_URL}

# Build static assets
RUN npm run build

# -------------------- Runtime Stage --------------------
FROM nginx:1.27-alpine AS runtime

# Remove default config and add SPA-friendly config on port 3000
RUN rm /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config for React Router style SPA
RUN printf 'server {\n  listen 3000;\n  server_name _;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / {\n    try_files $uri $uri/ /index.html;\n  }\n  location ~* \.(?:js|css|svg|png|jpg|jpeg|gif|ico)$ {\n    try_files $uri =404;\n    add_header Cache-Control "public, max-age=31536000, immutable";\n  }\n}\n' > /etc/nginx/conf.d/dashboard.conf

EXPOSE 3000

# No CMD override needed; use default nginx -g 'daemon off;'