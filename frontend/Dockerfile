# =============================================================================
# Dockerfile — Frontend (Vite + React)
# =============================================================================
# Build:  docker build -t rag-frontend -f Dockerfile .
# Run:    docker run -p 3000:3000 rag-frontend
# =============================================================================

# ── Builder ───────────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

ARG VITE_API_URL
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

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

    client_max_body_size 500M;

    root   /usr/share/nginx/html;
    index  index.html;

    # ── API proxy: forward /api/v1/* to the backend ──────────────────────
    # When running behind Caddy this rule is redundant (Caddy handles it),
    # but it allows the frontend container to work standalone.
    location /api/v1/ {
        client_max_body_size 500M;
        proxy_pass http://backend:8000/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

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