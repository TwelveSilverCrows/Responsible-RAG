# =============================================================================
# Dockerfile — Frontend (Next.js)
# =============================================================================
# Build:  docker build -t rag-frontend ./frontend
# Run:    docker run -p 3000:3000 rag-frontend
# =============================================================================

FROM oven/bun:1-alpine AS base

# =============================================================================
# Dependencies
# =============================================================================
FROM base AS deps

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/bun.lock ./

# Install dependencies
RUN bun install

# =============================================================================
# Builder
# =============================================================================
FROM base AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

# Build the Next.js application
RUN bun run build

# =============================================================================
# Runner
# =============================================================================
FROM base AS runner

WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]