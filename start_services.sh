#!/bin/bash
# Startup script for Render deployment
# Starts Flask, FastAPI, and proxy services

set -e

echo "🚀 Starting Bhutan Mental Health Chatbot Production Services"
echo "============================================================="

# Set environment variables
export FLASK_ENV=production
export PYTHONPATH=/app
export PORT=${PORT:-10000}

echo "📊 System Resources:"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "CPU cores: $(nproc)"
echo "Disk space: $(df -h / | tail -1 | awk '{print $4}')"

echo ""
echo "🔧 Environment:"
echo "FLASK_ENV: $FLASK_ENV"
echo "PORT: $PORT"
echo "PYTHONPATH: $PYTHONPATH"

echo ""
echo "📁 Creating necessary directories..."
mkdir -p /app/logs /app/data /app/uploads /app/chat_sessions /app/processed_docs
mkdir -p /var/log/supervisor

echo ""
echo "🗄️ Initializing database..."
cd /app
python -c "
import sys
sys.path.append('/app')
try:
    from main import init_db
    init_db()
    print('✅ Database initialized')
except Exception as e:
    print(f'⚠️ Database init warning: {e}')
"

echo ""
echo "🔍 Validating services..."

# Test imports
python -c "
import sys
sys.path.append('/app')
try:
    import main
    print('✅ Flask app (main.py) imports successfully')
except Exception as e:
    print(f'❌ Flask import error: {e}')
    sys.exit(1)

try:
    import fastapi_app
    print('✅ FastAPI app (fastapi_app.py) imports successfully')
except Exception as e:
    print(f'❌ FastAPI import error: {e}')
    sys.exit(1)
"

echo ""
echo "🚀 Starting services with supervisor..."

# Start supervisor
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
