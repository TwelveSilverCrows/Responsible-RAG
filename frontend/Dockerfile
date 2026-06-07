# =============================================================================
# Dockerfile — Frontend (Vite + React)
# =============================================================================
# Build:  docker build -t rag-frontend -f Dockerfile .
# Run:    docker run -p 3000:3000 rag-frontend
# =============================================================================

FROM oven/bun:1-alpine AS base

# =============================================================================
# Dependencies
# =============================================================================
FROM base AS deps

WORKDIR /app

# Copy package files (no lockfile — bun will generate one)
COPY package.json ./

# Install dependencies
RUN bun install

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
RUN bun run build

# =============================================================================
# Runner
# =============================================================================
FROM oven/bun:1-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# Copy built assets
COPY --from=builder /app/dist ./dist

# Install a minimal static file server
RUN bun add serve

EXPOSE 3000

CMD ["bun", "x", "serve", "dist", "-s", "-l", "3000"]