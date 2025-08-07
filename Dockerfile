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

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements_production.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data uploads chat_sessions processed_docs \
    && mkdir -p /var/log/supervisor

# Copy supervisor configuration
COPY supervisor.conf /etc/supervisor/conf.d/supervisord.conf

# Create startup script
COPY start_services.sh /start_services.sh
RUN chmod +x /start_services.sh

# Expose port for Render
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start services using supervisor
CMD ["/start_services.sh"]
