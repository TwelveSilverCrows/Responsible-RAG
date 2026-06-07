# =============================================================================
# Dockerfile — Frontend (Vite + React)
# =============================================================================
# Build:  docker build -t rag-frontend -f Dockerfile .
# Run:    docker run -p 3000:3000 rag-frontend
# =============================================================================

# ── Builder ───────────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package manifest (lockfile generated automatically inside container)
COPY package.json ./

# Install all deps (including dev) for the build
RUN npm install --no-fund --no-audit --progress=false

# Copy source
COPY . .

# Limit Node heap to prevent OOM on low-memory hosts
ENV NODE_OPTIONS="--max-old-space-size=512"
# CI=true disables spinner/color overhead during build
ENV CI=true

# Build the Vite application
RUN npm run build

# ── Runner ────────────────────────────────────────────────────────────────────
FROM nginx:alpine AS runner

# Copy built static assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Remove default nginx config and add a minimal one for SPA routing
RUN rm -rf /etc/nginx/conf.d/default.conf
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen       80;
    server_name  localhost;

    root   /usr/share/nginx/html;
    index  index.html;

    # SPA fallback — serve index.html for all non-file routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets aggressively
    location ~* \.(?:ico|css|js|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}
EOF

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]