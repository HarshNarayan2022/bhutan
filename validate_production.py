#!/usr/bin/env python3
"""
Production Environment Validation Script
Validates that all required components are properly configured for deployment
"""

import os
import sys
import requests
import sqlite3
import yaml
from pathlib import Path
import subprocess
import json
from typing import Dict, List, Tuple, Any

class ProductionValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def log_error(self, message: str):
        """Log an error"""
        self.errors.append(f"❌ ERROR: {message}")
        
    def log_warning(self, message: str):
        """Log a warning"""
        self.warnings.append(f"⚠️  WARNING: {message}")
        
    def log_pass(self, message: str):
        """Log a successful check"""
        self.passed.append(f"✅ {message}")
        
    def check_environment_variables(self):
        """Check required environment variables"""
        print("\n🔍 Checking Environment Variables...")
        
        required_vars = [
            'SECRET_KEY',
            'GOOGLE_API_KEY',
            'GROQ_API_KEY',
        ]
        
        optional_vars = [
            'OPENAI_API_KEY',
            'ELEVENLABS_API_KEY',
            'DATABASE_URL',
            'REDIS_URL',
            'SENTRY_DSN',
        ]
        
        # Check required variables
        for var in required_vars:
            if not os.getenv(var):
                self.log_error(f"Required environment variable {var} is not set")
            else:
                self.log_pass(f"Required variable {var} is set")
        
        # Check optional variables
        for var in optional_vars:
            if not os.getenv(var):
                self.log_warning(f"Optional environment variable {var} is not set")
            else:
                self.log_pass(f"Optional variable {var} is set")
        
        # Check SECRET_KEY strength
        secret_key = os.getenv('SECRET_KEY', '')
        if secret_key:
            if len(secret_key) < 32:
                self.log_warning("SECRET_KEY should be at least 32 characters long")
            if secret_key in ['dev-secret-key', 'your_secret_key_here']:
                self.log_error("SECRET_KEY is using a default/example value")
        
        # Check Flask environment
        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env != 'production':
            self.log_warning(f"FLASK_ENV is set to '{flask_env}', should be 'production' for deployment")
        
        debug = os.getenv('DEBUG', 'False').lower()
        if debug == 'true':
            self.log_warning("DEBUG is enabled, should be disabled in production")
    
    def check_file_structure(self):
        """Check required files and directories"""
        print("\n🔍 Checking File Structure...")
        
        required_files = [
            'main.py',
            'fastapi_app.py',
            'requirements.txt',
            'Dockerfile',
            'docker-compose.yml',
            'gunicorn.conf.py',
            'start_services.py',
        ]
        
        required_dirs = [
            'templates',
            'static',
            'config',
            'agents',
            'crew_ai',
            'models',
        ]
        
        # Check files
        for file_path in required_files:
            if Path(file_path).exists():
                self.log_pass(f"Required file {file_path} exists")
            else:
                self.log_error(f"Required file {file_path} is missing")
        
        # Check directories
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                self.log_pass(f"Required directory {dir_path} exists")
            else:
                self.log_error(f"Required directory {dir_path} is missing")
        
        # Check runtime directories
        runtime_dirs = ['logs', 'data', 'uploads']
        for dir_path in runtime_dirs:
            Path(dir_path).mkdir(exist_ok=True)
            self.log_pass(f"Runtime directory {dir_path} created/verified")
    
    def check_dependencies(self):
        """Check Python dependencies"""
        print("\n🔍 Checking Dependencies...")
        
        try:
            import flask
            self.log_pass(f"Flask {flask.__version__} is installed")
        except ImportError:
            self.log_error("Flask is not installed")
        
        try:
            import fastapi
            self.log_pass(f"FastAPI {fastapi.__version__} is installed")
        except ImportError:
            self.log_error("FastAPI is not installed")
        
        try:
            import crewai
            self.log_pass("CrewAI is installed")
        except ImportError:
            self.log_error("CrewAI is not installed")
        
        try:
            import openai_whisper
            self.log_pass("OpenAI Whisper is installed")
        except ImportError:
            self.log_warning("OpenAI Whisper is not installed (voice features will be disabled)")
        
        # Check for security-related packages
        try:
            import bcrypt
            self.log_pass("bcrypt for password hashing is installed")
        except ImportError:
            self.log_error("bcrypt is not installed")
    
    def check_configuration_files(self):
        """Check configuration files"""
        print("\n🔍 Checking Configuration Files...")
        
        config_files = [
            'config/agents.yaml',
            'config/rag.yaml',
            'config/tasks.yaml',
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'r') as f:
                        yaml.safe_load(f)
                    self.log_pass(f"Configuration file {config_file} is valid YAML")
                except yaml.YAMLError as e:
                    self.log_error(f"Configuration file {config_file} has invalid YAML: {e}")
            else:
                self.log_warning(f"Configuration file {config_file} is missing")
    
    def check_docker_configuration(self):
        """Check Docker configuration"""
        print("\n🔍 Checking Docker Configuration...")
        
        # Check if Docker is available
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_pass(f"Docker is available: {result.stdout.strip()}")
            else:
                self.log_warning("Docker is not available")
        except FileNotFoundError:
            self.log_warning("Docker is not installed")
        
        # Check if Docker Compose is available
        compose_available = False
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_pass(f"Docker Compose (standalone) is available: {result.stdout.strip()}")
                compose_available = True
        except FileNotFoundError:
            pass
        
        if not compose_available:
            try:
                result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_pass(f"Docker Compose (plugin) is available: {result.stdout.strip()}")
                    compose_available = True
            except FileNotFoundError:
                pass
        
        if not compose_available:
            self.log_warning("Docker Compose is not available")
        
        # Validate Dockerfile
        if Path('Dockerfile').exists():
            with open('Dockerfile', 'r') as f:
                dockerfile_content = f.read()
                if 'FROM python:3.11' in dockerfile_content:
                    self.log_pass("Dockerfile uses Python 3.11 base image")
                if 'EXPOSE' in dockerfile_content:
                    self.log_pass("Dockerfile exposes ports")
                if 'USER user' in dockerfile_content:
                    self.log_pass("Dockerfile uses non-root user")
    
    def check_security_configuration(self):
        """Check security configuration"""
        print("\n🔍 Checking Security Configuration...")
        
        # Check session security
        session_secure = os.getenv('SESSION_COOKIE_SECURE', 'false').lower()
        if session_secure == 'true':
            self.log_pass("Session cookies are configured as secure")
        else:
            self.log_warning("Session cookies should be secure in production")
        
        session_httponly = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower()
        if session_httponly == 'true':
            self.log_pass("Session cookies are configured as httponly")
        else:
            self.log_error("Session cookies should be httponly")
        
        # Check for common security files
        security_files = ['.env.production', 'requirements.prod.txt']
        for file_path in security_files:
            if Path(file_path).exists():
                self.log_pass(f"Security file {file_path} exists")
            else:
                self.log_warning(f"Security file {file_path} is missing")
    
    def check_database_configuration(self):
        """Check database configuration"""
        print("\n🔍 Checking Database Configuration...")
        
        database_url = os.getenv('DATABASE_URL', '')
        
        if not database_url:
            self.log_warning("DATABASE_URL is not set, using default SQLite")
            database_url = 'sqlite:///data/mental_health_app.db'
        
        if database_url.startswith('sqlite'):
            # Check SQLite database
            db_path = database_url.replace('sqlite:///', '')
            db_dir = Path(db_path).parent
            db_dir.mkdir(exist_ok=True)
            self.log_pass("SQLite database directory exists")
            
            # Try to connect to database
            try:
                conn = sqlite3.connect(db_path)
                conn.close()
                self.log_pass("SQLite database connection successful")
            except Exception as e:
                self.log_error(f"SQLite database connection failed: {e}")
        
        elif database_url.startswith('postgresql'):
            self.log_pass("PostgreSQL database configured (recommended for production)")
            # Note: Actual connection test would require the database to be running
        else:
            self.log_warning(f"Unknown database type in DATABASE_URL: {database_url}")
    
    def check_api_keys(self):
        """Check API key validity"""
        print("\n🔍 Checking API Key Validity...")
        
        # Check Google API Key
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key and google_key != 'your_google_api_key_here':
            self.log_pass("Google API key appears to be configured")
        elif google_key:
            self.log_error("Google API key is using example value")
        
        # Check GROQ API Key
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key and groq_key != 'your_groq_api_key_here':
            self.log_pass("GROQ API key appears to be configured")
        elif groq_key:
            self.log_error("GROQ API key is using example value")
        
        # Check OpenAI API Key
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'your_openai_api_key_here':
            self.log_pass("OpenAI API key appears to be configured")
        elif openai_key:
            self.log_error("OpenAI API key is using example value")
    
    def check_ports(self):
        """Check port availability"""
        print("\n🔍 Checking Port Availability...")
        
        import socket
        
        ports_to_check = [
            (5000, "Flask"),
            (8000, "FastAPI"),
        ]
        
        for port, service in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                self.log_warning(f"Port {port} ({service}) is already in use")
            else:
                self.log_pass(f"Port {port} ({service}) is available")
    
    def run_all_checks(self):
        """Run all validation checks"""
        print("🚀 Production Environment Validation")
        print("=" * 50)
        
        # Run all checks
        self.check_environment_variables()
        self.check_file_structure()
        self.check_dependencies()
        self.check_configuration_files()
        self.check_docker_configuration()
        self.check_security_configuration()
        self.check_database_configuration()
        self.check_api_keys()
        self.check_ports()
        
        # Print summary
        print("\n📋 Validation Summary")
        print("=" * 50)
        
        if self.passed:
            print(f"\n✅ Passed Checks ({len(self.passed)}):")
            for item in self.passed:
                print(f"  {item}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for item in self.warnings:
                print(f"  {item}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for item in self.errors:
                print(f"  {item}")
        
        # Final assessment
        print(f"\n🎯 Final Assessment")
        print("=" * 50)
        
        if self.errors:
            print("❌ DEPLOYMENT NOT READY")
            print("Please fix the errors above before deploying to production.")
            return False
        elif self.warnings:
            print("⚠️  DEPLOYMENT READY WITH WARNINGS")
            print("Consider addressing the warnings above for optimal production deployment.")
            return True
        else:
            print("✅ DEPLOYMENT READY")
            print("All checks passed! The application is ready for production deployment.")
            return True

def main():
    """Main function"""
    validator = ProductionValidator()
    
    # Load environment from .env file if it exists
    if Path('.env').exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("📄 Loaded environment variables from .env file")
        except ImportError:
            print("⚠️  python-dotenv not installed, loading .env manually")
            # Simple .env file parser
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    success = validator.run_all_checks()
    
    if success:
        print("\n🚀 Ready to deploy! Run: ./deploy.sh deploy production")
    else:
        print("\n🛑 Please fix the issues above before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
