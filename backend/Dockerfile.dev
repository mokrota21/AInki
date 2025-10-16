FROM python:3.12-slim

# Install system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV like the production Dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Use system Python and unbuffered logging
ENV UV_SYSTEM_PYTHON=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

WORKDIR /app

# Copy project files required for dependency resolution
COPY pyproject.toml uv.lock ./

# Install dependencies (runtime only for dev image)
RUN uv sync --no-dev

# Copy application source
COPY . .

# Expose port
EXPOSE 8000

# Default command runs uvicorn with reload; app module path is main:app
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

