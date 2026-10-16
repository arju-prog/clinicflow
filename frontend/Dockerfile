# syntax=docker/dockerfile:1

# ---- Stage 1: build the React app with Node ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG APP_VERSION=dev
ENV VITE_APP_VERSION=${APP_VERSION}
RUN npm run build

# ---- Stage 2: serve static files with Nginx (no Node, no source, no node_modules) ----
FROM nginxinc/nginx-unprivileged:stable-alpine
ARG APP_VERSION=dev
LABEL org.opencontainers.image.title="clinicflow-frontend" \
      org.opencontainers.image.description="ClinicFlow React frontend served by Nginx" \
      org.opencontainers.image.revision="${APP_VERSION}"

# Apply Alpine security patches released after the base image was published.
USER root
RUN apk upgrade --no-cache
# The nginx-unprivileged image runs as uid 101 and listens on 8080 (no root, no port 80).
USER 101

ENV BACKEND_URL=http://backend:8000 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1
COPY --chown=101:101 nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build --chown=101:101 /app/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
