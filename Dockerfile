# Multi-stage Dockerfile for API + Frontend

# --- Frontend build stage (Debian, glibc) ---
FROM node:20-bookworm-slim AS frontend-builder
WORKDIR /app/frontend

# Copy only package files first for better caching
COPY frontend/package*.json ./

# Clean, reproducible install
RUN npm ci

# Copy the rest of the frontend source
COPY frontend/ .

# Build the production bundle
RUN npm run build

# --- Backend build stage ---
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV using official method
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Use system Python environment (recommended for Docker)
ENV UV_SYSTEM_PYTHON=1

# Fix Python logging in Docker containers
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

WORKDIR /app

# Copy API source code
COPY backend/ .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Install Python dependencies using uv
RUN uv sync

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Run the application using uvicorn directly with proper logging
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--log-level", "info"]