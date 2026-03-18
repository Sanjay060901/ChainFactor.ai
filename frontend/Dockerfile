# ---- Dependencies stage ----
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

# ---- Development stage (used by docker-compose) ----
FROM node:20-alpine AS development

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

# Non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 3000

CMD ["npm", "run", "dev"]

# ---- Production build stage (static export for S3+CloudFront) ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ---- Production output (static files only, for CI/CD to push to S3) ----
FROM alpine:3.20 AS production

RUN apk add --no-cache aws-cli

WORKDIR /app

COPY --from=builder /app/out ./out

# Static files in /app/out -- push to S3 via CI/CD:
# aws s3 sync /app/out s3://$FRONTEND_BUCKET --delete
CMD ["echo", "Static files in /app/out. Use: aws s3 sync /app/out s3://BUCKET --delete"]
