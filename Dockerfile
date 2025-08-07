# Production Dockerfile for Render - Flask + FastAPI
# Optimized for 512MB RAM deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for memory optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV TOKENIZERS_PARALLELISM=false
ENV FLASK_ENV=production

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements_production.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data uploads chat_sessions processed_docs

# Copy supervisor configuration
COPY supervisor.conf /etc/supervisor/conf.d/supervisord.conf

# Make scripts executable
RUN chmod +x start_services.sh start_minimal.py

# Expose port for Render
EXPOSE 10000

# Health check (check proxy service)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Start services using minimal Python launcher
CMD ["python3", "start_minimal.py"]
