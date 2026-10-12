# syntax=docker/dockerfile:1.7
# ---- build stage: Node compiles the React app into static files ----
FROM node:26-alpine3.24 AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# ---- runtime stage: unprivileged Nginx serves dist/ and proxies /api ----
FROM nginxinc/nginx-unprivileged:1.30-alpine3.24 AS runtime
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.title="pantrypulse-frontend" \
      org.opencontainers.image.description="PantryPulse web app (static React build on Nginx)" \
      org.opencontainers.image.authors="Pratyush Mishra" \
      org.opencontainers.image.source="https://github.com/PratyushMishra-2nd/DevopsProject" \
      org.opencontainers.image.revision="${GIT_SHA}"
USER root
# Apply Alpine security fixes published after the base image was built.
RUN apk upgrade --no-cache
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /src/dist /usr/share/nginx/html
# nginx-unprivileged runs as UID 101 and listens on 8080 (no root, no port below 1024).
USER 101
ENV BACKEND_UPSTREAM=backend:8000
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
