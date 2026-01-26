# Stage 1: Builder
FROM python:3.10-slim AS builder

# Set shell to fail fast
SHELL ["/bin/bash", "-c"]

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install to /install instead of /root/.local for cleaner copying
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Stage 2: Final Image
FROM python:3.10-slim
WORKDIR /app

# Install ONLY runtime libraries if needed (e.g., libpq for postgres)
# If your app is simple pure-python, you can skip this RUN block.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \ 
    && rm -rf /var/lib/apt/lists/*

# Copy the installed packages from the builder
COPY --from=builder /install /usr/local
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["python", "app.py"]