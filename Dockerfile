
#  SecureFlow — Multi-Stage Dockerfile
#  Stage 1: Install Python dependencies
#  Stage 2: Build React dashboard
#  Stage 3: Production runtime


# --- Stage 1: Python dependency builder ---
FROM python:3.11-slim AS python-builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Stage 2: Dashboard builder ---
FROM node:20-alpine AS dashboard-builder

WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm ci --production=false 2>/dev/null || npm install
COPY dashboard/ .
RUN npm run build

# --- Stage 3: Production runtime ---
FROM python:3.11-slim

# Security: run as non-root
RUN groupadd -r secureflow && useradd -r -g secureflow secureflow

WORKDIR /app

# Copy Python packages from builder
COPY --from=python-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source
COPY secureflow/ ./secureflow/
COPY pyproject.toml .

# Copy built dashboard to static directory
COPY --from=dashboard-builder /app/dashboard/dist ./dashboard/dist

# Install the package in editable-like mode
RUN pip install --no-cache-dir -e .

# Cloud Run uses PORT env var (default 8080)
ENV PORT=8080
EXPOSE ${PORT}

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:${PORT}/health'); assert r.status_code == 200" || exit 1

# Run with uvicorn — Cloud Run sends SIGTERM for graceful shutdown
CMD ["sh", "-c", "uvicorn secureflow.api.main:app --host 0.0.0.0 --port ${PORT} --workers 2 --timeout-graceful-shutdown 30"]
