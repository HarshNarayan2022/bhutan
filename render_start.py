#!/usr/bin/env python3
"""
Render.com optimized startup script for Mental Health Chatbot
Single port deployment with both Flask and FastAPI
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Set default port for Render
PORT = int(os.environ.get('PORT', 10000))

class RenderServiceManager:
    def __init__(self):
        self.processes = []
        self.shutdown_event = threading.Event()
        
    def signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.shutdown_event.set()
        self.stop_all_services()
        sys.exit(0)
        
    def start_background_service(self, command, name, env=None):
        """Start a background service"""
        print(f"🚀 Starting {name}...")
        
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                env=env or os.environ.copy(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append((process, name))
            
            # Log output in separate thread
            def log_output():
                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        print(f"[{name}] {line.strip()}")
                        
            threading.Thread(target=log_output, daemon=True).start()
            
            # Monitor process health
            threading.Thread(target=self.monitor_process, args=(process, name, command, env), daemon=True).start()
            
            print(f"✅ {name} started with PID {process.pid}")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def monitor_process(self, process, name, command, env=None):
        """Monitor process and restart if it crashes"""
        while not self.shutdown_event.is_set():
            try:
                # Check if process is still running
                if process.poll() is not None:
                    print(f"⚠️ {name} crashed (exit code: {process.returncode}), restarting...")
                    time.sleep(2)  # Brief delay before restart
                    
                    # Restart the process
                    new_process = subprocess.Popen(
                        command,
                        shell=True,
                        env=env or os.environ.copy(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    # Update process in list
                    for i, (proc, proc_name) in enumerate(self.processes):
                        if proc == process:
                            self.processes[i] = (new_process, proc_name)
                            break
                    
                    process = new_process
                    print(f"🔄 {name} restarted with PID {process.pid}")
                    
                    # Start logging for new process
                    def log_output():
                        for line in iter(process.stdout.readline, ''):
                            if line.strip():
                                print(f"[{name}] {line.strip()}")
                    threading.Thread(target=log_output, daemon=True).start()
                
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"❌ Error monitoring {name}: {e}")
                time.sleep(5)
    
    def stop_all_services(self):
        """Stop all background services"""
        for process, name in self.processes:
            try:
                print(f"⏹️ Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        self.processes.clear()
    
    def setup_environment(self):
        """Setup environment variables for memory optimization"""
        # Memory optimization for AI models
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'  # Disable MPS
        os.environ['TRANSFORMERS_CACHE'] = '/tmp/transformers_cache'
        os.environ['HF_HOME'] = '/tmp/huggingface_cache'
        os.environ['WHISPER_CACHE'] = '/tmp/whisper_cache'
        
        # Disable unnecessary features to save memory
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        
        # Python memory optimization
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        
        # Memory mode optimization
        memory_mode = os.environ.get('MEMORY_MODE', 'normal')
        if memory_mode == 'lite':
            os.environ['SKIP_AI_MODELS'] = '1'
            os.environ['DISABLE_WHISPER'] = '1'
            print("🔧 Running in LITE memory mode - AI features limited")
        
        print("🔧 Environment optimized for memory constraints")
        
    def setup_directories(self):
        """Create necessary directories"""
        directories = ["data", "logs", "uploads", "chat_sessions", "survey_data"]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Directory {directory} ready")
    
    def start_fastapi_background(self):
        """Start FastAPI as background service on internal port"""
        internal_port = PORT + 1000  # Use different port internally
        fastapi_env = os.environ.copy()
        fastapi_env['FASTAPI_PORT'] = str(internal_port)
        
        return self.start_background_service(
            f"python -m uvicorn fastapi_app:app --host 0.0.0.0 --port {internal_port}",
            "FastAPI Backend",
            fastapi_env
        )
    
    def wait_for_service(self, url, timeout=30):
        """Wait for service to be ready"""
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(2)
        return False
    
    def run_flask_main(self):
        """Run Flask as the main process on Render port"""
        print(f"🌐 Starting Flask main service on port {PORT}")
        
        # Update Flask app configuration for Render
        flask_env = os.environ.copy()
        flask_env['PORT'] = str(PORT)
        flask_env['HOST'] = '0.0.0.0'
        flask_env['BACKEND_URL'] = f'http://localhost:{PORT + 1000}'
        
        # Run Flask with gunicorn for production (Render-optimized)
        cmd = [
            'python', '-m', 'gunicorn',
            'main:app',
            '--bind', f'0.0.0.0:{PORT}',
            '--workers', '1',  # Single worker for memory constraints
            '--timeout', '300',  # 5 minutes for AI processing
            '--keep-alive', '2',
            '--max-requests', '500',  # Lower to prevent memory leaks
            '--max-requests-jitter', '50',
            '--worker-class', 'sync',
            '--worker-connections', '1000',
            '--preload'
        ]
        
        print(f"🚀 Starting Flask with command: {' '.join(cmd)}")
        
        try:
            # Run Flask as main process (blocking)
            subprocess.run(cmd, env=flask_env, check=True)
        except KeyboardInterrupt:
            print("🛑 Flask service interrupted")
        except subprocess.CalledProcessError as e:
            print(f"❌ Flask service failed: {e}")
            sys.exit(1)
    
    def run(self):
        """Main execution method for Render"""
        print("🎯 Starting Mental Health Chatbot for Render.com")
        print("=" * 60)
        print(f"🌐 Port: {PORT}")
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Setup environment for memory optimization
        self.setup_environment()
        
        # Setup directories
        self.setup_directories()
        
        # Start FastAPI in background
        fastapi_process = self.start_fastapi_background()
        if not fastapi_process:
            print("❌ Failed to start FastAPI backend")
            return 1
        
        # Wait a moment for FastAPI to start
        time.sleep(5)
        
        # Check if FastAPI is ready
        internal_port = PORT + 1000
        if not self.wait_for_service(f"http://localhost:{internal_port}/health"):
            print("⚠️ FastAPI health check failed, but continuing...")
        
        print("🎉 Background services ready!")
        print(f"📊 Application will be available on port {PORT}")
        
        # Run Flask as main process (this blocks)
        try:
            self.run_flask_main()
        except Exception as e:
            print(f"❌ Critical error: {e}")
            self.stop_all_services()
            return 1
        finally:
            self.stop_all_services()
        
        return 0

if __name__ == "__main__":
    print("🚀 Mental Health Chatbot - Render Deployment")
    manager = RenderServiceManager()
    exit_code = manager.run()
    sys.exit(exit_code)
