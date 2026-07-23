# Aangan — single-container deployment (backend serves the built frontend).
# Build:  docker build -t aangan .
# Run:    docker compose up   (see docker-compose.yml for volumes)

FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-fund --no-audit
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false

COPY backend/requirements.txt .
# --timeout/--retries: recover from stalled wheel downloads instead of hanging
RUN pip install --no-cache-dir --timeout 60 --retries 5 -r requirements.txt

COPY backend/ .
COPY --from=frontend /build/dist /app/frontend/dist

# db, vectors, and audio live on mounted volumes (see docker-compose.yml)
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
