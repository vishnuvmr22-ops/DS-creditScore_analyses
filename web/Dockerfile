# CreditSentinel operator console — its own image, its own runtime.
# Multi-stage: install deps, build the standalone output, then run it on a slim
# non-root Node base. The scoring service is reached over HTTP only; nothing here
# shares the Python image (constitution v1.1.0: the console is confined to web/).

# --- deps -----------------------------------------------------------------
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# --- build ----------------------------------------------------------------
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# --- runtime --------------------------------------------------------------
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000
# The service address is read from CS_API_BASE_URL at request time (FR-023).

# Standalone output carries only the traced dependency set.
COPY --from=build /app/public ./public
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static

USER node
EXPOSE 3000
CMD ["node", "server.js"]
