# =============================================================================
# Dockerfile — Frontend (Vite + React)
# =============================================================================
# Build:  docker build -t rag-frontend -f Dockerfile .
# Run:    docker run -p 3000:3000 rag-frontend
# =============================================================================

FROM node:22-alpine AS base

# =============================================================================
# Dependencies
# =============================================================================
FROM base AS deps

WORKDIR /app

# Copy package files (no lockfile — npm will generate one)
COPY package.json ./

# Install dependencies (--no-fund --no-audit to reduce memory & network overhead)
RUN npm install --no-fund --no-audit

# =============================================================================
# Builder
# =============================================================================
FROM base AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NODE_OPTIONS="--max-old-space-size=512"
ENV NODE_OPTIONS=$NODE_OPTIONS

# Build the Vite application
RUN npm run build

# =============================================================================
# Runner
# =============================================================================
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# Copy built assets
COPY --from=builder /app/dist ./dist

EXPOSE 3000

# Use npx to run serve without permanently installing it
CMD ["npx", "--yes", "serve", "dist", "-s", "-l", "3000"]