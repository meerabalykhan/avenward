FROM node:22-alpine AS dependencies

WORKDIR /app
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --store-dir /tmp/pnpm-store

FROM dependencies AS test
COPY frontend/ .
CMD ["pnpm", "test"]

FROM dependencies AS builder
COPY frontend/ .
RUN pnpm build

FROM nginx:1.31-alpine AS runtime
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 8080
