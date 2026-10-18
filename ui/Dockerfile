# syntax=docker/dockerfile:1

# ---- build: compile TypeScript with the exact locked toolchain ------------------------------
FROM node:24.22.0-alpine3.24 AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY tsconfig.json tsconfig.build.json ./
COPY src ./src
RUN npm run build && npm prune --omit=dev --ignore-scripts

# ---- runtime: production dependencies only, non-root ----------------------------------------
FROM node:24.22.0-alpine3.24 AS runtime
ENV NODE_ENV=production
WORKDIR /app
COPY --from=build --chown=root:root /src/package.json ./
COPY --from=build --chown=root:root /src/node_modules ./node_modules
COPY --from=build --chown=root:root /src/dist ./dist
COPY --chown=root:root views ./views
COPY --chown=root:root public ./public
# The image's built-in unprivileged user; application files stay root-owned and read-only.
USER node
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
CMD ["node", "dist/src/server.js"]
