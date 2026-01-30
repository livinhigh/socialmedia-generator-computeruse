FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first to leverage Docker cache
COPY socialmedia_generator/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r /app/requirements.txt

# Copy application code
COPY . /app
COPY image/ ./


# Make scripts executable
RUN chmod +x *.sh


# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1


ENTRYPOINT ["./entrypoint_fastapi.sh"]
