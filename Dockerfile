FROM python:3.11-slim

# Set environment variables for Render deployment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    DEBIAN_FRONTEND=noninteractive \
    MEMORY_MODE=normal

# Install system dependencies required for the app
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.render.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/uploads /app/chat_sessions /app/survey_data

# Expose the port that Render expects
EXPOSE $PORT

# Health check for monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start command optimized for Render
CMD ["python", "render_start.py"]