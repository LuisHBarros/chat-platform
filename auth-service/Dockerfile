# Auth Service Dockerfile using Python 3.14 & UV package manager
FROM python:3.14-slim AS builder

WORKDIR /app

# Prevent Python from writing .pyc files & enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project dependency files
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen --no-dev

# Copy application source code
COPY . .

EXPOSE 8000

# Copy and prepare entrypoint script
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Run migrations then start FastAPI app
CMD ["./entrypoint.sh"]
