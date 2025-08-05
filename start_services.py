#!/usr/bin/env python3
"""
Production service startup script for Mental Health App
Starts both Flask and FastAPI services
"""

import os
import sys
import signal
import subprocess
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/startup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = {}
        self.shutdown = False
        
    def start_fastapi(self):
        """Start FastAPI service with uvicorn"""
        port = os.getenv('FASTAPI_PORT', 8000)
        workers = os.getenv('WORKERS', 1)
        
        cmd = [
            'uvicorn', 
            'fastapi_app:app',
            '--host', '0.0.0.0',
            '--port', str(port),
            '--workers', str(workers),
            '--log-level', 'info',
            '--access-log'
        ]
        
        logger.info(f"Starting FastAPI on port {port}")
        process = subprocess.Popen(cmd, cwd='/app')
        self.processes['fastapi'] = process
        return process
        
    def start_flask(self):
        """Start Flask service with gunicorn"""
        port = os.getenv('PORT', 5000)
        
        cmd = [
            'gunicorn',
            '--config', 'gunicorn.conf.py',
            'main:app'
        ]
        
        logger.info(f"Starting Flask on port {port}")
        process = subprocess.Popen(cmd, cwd='/app')
        self.processes['flask'] = process
        return process
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.shutdown = True
            self.stop_all_services()
            sys.exit(0)
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def stop_all_services(self):
        """Stop all running services"""
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}...")
                    process.kill()
    
    def wait_for_service(self, url, timeout=60):
        """Wait for a service to be ready"""
        import requests
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        return False
    
    def health_check(self):
        """Perform health checks on services"""
        services = {
            'flask': f"http://localhost:{os.getenv('PORT', 5000)}/",
            'fastapi': f"http://localhost:{os.getenv('FASTAPI_PORT', 8000)}/health"
        }
        
        for name, url in services.items():
            if name in self.processes:
                if not self.wait_for_service(url, timeout=30):
                    logger.error(f"{name} service failed health check")
                    return False
                logger.info(f"{name} service is healthy")
        return True
    
    def monitor_services(self):
        """Monitor running services and restart if needed"""
        while not self.shutdown:
            for name, process in self.processes.items():
                if process.poll() is not None:
                    logger.error(f"{name} service stopped unexpectedly")
                    if name == 'fastapi':
                        self.processes[name] = self.start_fastapi()
                    elif name == 'flask':
                        self.processes[name] = self.start_flask()
            time.sleep(10)
    
    def run(self):
        """Main execution method"""
        logger.info("Starting Mental Health App services...")
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Create necessary directories
        os.makedirs('/app/logs', exist_ok=True)
        os.makedirs('/app/data', exist_ok=True)
        os.makedirs('/app/uploads', exist_ok=True)
        
        try:
            # Start services
            self.start_fastapi()
            time.sleep(5)  # Wait a bit before starting Flask
            self.start_flask()
            
            # Wait for services to be ready
            if self.health_check():
                logger.info("All services started successfully")
                
                # Monitor services
                self.monitor_services()
            else:
                logger.error("Service health check failed")
                self.stop_all_services()
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            self.stop_all_services()
            sys.exit(1)

if __name__ == "__main__":
    manager = ServiceManager()
    manager.run()
