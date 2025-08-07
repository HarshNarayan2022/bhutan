#!/usr/bin/env python3
"""
Minimal startup script for Render - Starts all services
"""

import os
import sys
import time
import subprocess
import multiprocessing
import signal
from pathlib import Path

def setup_environment():
    """Setup environment variables"""
    os.environ['FLASK_ENV'] = 'production'
    os.environ['PYTHONPATH'] = '/app'
    
    # Set default port
    if 'PORT' not in os.environ:
        os.environ['PORT'] = '10000'

def init_database():
    """Initialize database if needed"""
    try:
        from main import init_db
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database init warning: {e}")

def start_flask():
    """Start Flask application"""
    print("🌐 Starting Flask frontend (main.py)...")
    try:
        cmd = [sys.executable, "main.py"]
        env = os.environ.copy()
        env['FLASK_RUN_HOST'] = '0.0.0.0'
        env['FLASK_RUN_PORT'] = '5000'
        return subprocess.Popen(cmd, env=env)
    except Exception as e:
        print(f"❌ Failed to start Flask: {e}")
        return None

def start_fastapi():
    """Start FastAPI application"""
    print("🔧 Starting FastAPI backend (fastapi_app.py)...")
    try:
        cmd = [sys.executable, "fastapi_app.py"]
        env = os.environ.copy()
        return subprocess.Popen(cmd, env=env)
    except Exception as e:
        print(f"❌ Failed to start FastAPI: {e}")
        return None

def start_proxy():
    """Start HTTP proxy"""
    print("🔀 Starting HTTP proxy...")
    try:
        cmd = [sys.executable, "nginx_proxy.py"]
        return subprocess.Popen(cmd)
    except Exception as e:
        print(f"❌ Failed to start proxy: {e}")
        return None

def cleanup_processes(processes):
    """Clean up all processes"""
    print("🧹 Shutting down services...")
    for name, proc in processes.items():
        if proc and proc.poll() is None:
            print(f"Stopping {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

def main():
    """Main startup function"""
    print("🚀 Starting Bhutan Mental Health Chatbot")
    print("=" * 50)
    
    # Setup
    setup_environment()
    
    # Initialize database
    init_database()
    
    # Start services
    processes = {}
    
    try:
        # Start Flask
        processes['flask'] = start_flask()
        time.sleep(3)  # Give Flask time to start
        
        # Start FastAPI
        processes['fastapi'] = start_fastapi()
        time.sleep(3)  # Give FastAPI time to start
        
        # Start proxy
        processes['proxy'] = start_proxy()
        time.sleep(2)  # Give proxy time to start
        
        print("✅ All services started successfully!")
        print(f"🌐 Application available on port {os.environ['PORT']}")
        
        # Keep running and monitor
        while True:
            # Check if any process died
            for name, proc in processes.items():
                if proc and proc.poll() is not None:
                    print(f"⚠️ {name} process died, restarting...")
                    if name == 'flask':
                        processes[name] = start_flask()
                    elif name == 'fastapi':
                        processes[name] = start_fastapi()
                    elif name == 'proxy':
                        processes[name] = start_proxy()
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cleanup_processes(processes)
        print("👋 Shutdown complete")

if __name__ == "__main__":
    main()
