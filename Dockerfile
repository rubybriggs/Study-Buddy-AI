# Use Bookworm (Stable) instead of Trixie (Testing)
FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

# Only install what you absolutely need
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Use --user or --prefix to keep the build stage clean
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final Image
FROM python:3.10-slim-bookworm
WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

CMD ["python", "app.py"]