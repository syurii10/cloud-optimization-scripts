# Cloud Optimization Project - Multi-stage Docker Build

# Stage 1: Python Base
FROM python:3.11-slim as python-base

WORKDIR /app

# Встановлення system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Копіювання Python залежностей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Node.js для дашборду
FROM node:18-alpine as node-base

WORKDIR /app

# Копіювання Node.js залежностей
COPY package.json ./
RUN npm install --production

# Stage 3: Final image
FROM python:3.11-slim

WORKDIR /app

# Встановлення runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    openssh-client \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Копіювання Python залежностей з python-base
COPY --from=python-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin

# Копіювання Node.js залежностей з node-base
COPY --from=node-base /app/node_modules ./node_modules

# Копіювання проекту
COPY scripts/ ./scripts/
COPY terraform/ ./terraform/
COPY *.py ./
COPY *.js ./
COPY *.html ./
COPY package.json ./

# Створення директорій для результатів
RUN mkdir -p /app/results /app/logs

# Права доступу
RUN chmod +x scripts/*.py

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    AWS_REGION=eu-central-1 \
    LOG_LEVEL=INFO

# Expose port для веб-дашборду
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Default command
CMD ["node", "server.js"]
