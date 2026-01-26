FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install ONLY what is necessary for the build phase
# We keep curl for the healthchecks/downloads, but minimize build-essential usage
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 1. Copy requirement files first
COPY setup.py .
COPY requirements.txt .

# 2. Install dependencies (Prefer binaries to avoid long compilation times)
RUN pip install --no-cache-dir --prefer-binary -e .

# 3. Copy application code last
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "application.py", "--server.port=8501", "--server.address=0.0.0.0","--server.headless=true"]
