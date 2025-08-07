#!/usr/bin/env python3
"""
Deployment Script for Render Cloud
Prepares the application for Render deployment
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'Dockerfile',
        'requirements_render.txt', 
        'app_render.py',
        'render.yaml'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def validate_dockerfile():
    """Validate Dockerfile for Render compatibility"""
    with open('Dockerfile', 'r') as f:
        content = f.read()
    
    checks = [
        ('EXPOSE 10000', 'Port 10000 exposed'),
        ('python:3.11-slim', 'Using Python 3.11 slim base'),
        ('app_render.py', 'Running app_render.py'),
        ('HEALTHCHECK', 'Health check configured')
    ]
    
    for check, description in checks:
        if check in content:
            print(f"✅ {description}")
        else:
            print(f"❌ Missing: {description}")
            return False
    
    return True

def validate_requirements():
    """Validate requirements are lightweight"""
    with open('requirements_render.txt', 'r') as f:
        lines = f.readlines()
    
    # Check for heavy packages that shouldn't be there
    heavy_packages = [
        'torch', 'tensorflow', 'transformers', 'gradio', 
        'streamlit', 'numpy', 'pandas', 'matplotlib', 'seaborn'
    ]
    
    for line in lines:
        package = line.strip().lower()
        for heavy in heavy_packages:
            if heavy in package:
                print(f"⚠️ Warning: Heavy package detected: {package}")
    
    print(f"✅ Requirements file validated ({len(lines)} packages)")
    return True

def test_app_import():
    """Test if app_render.py can be imported"""
    try:
        sys.path.insert(0, os.getcwd())
        
        # Test basic imports
        import flask
        from textblob import TextBlob
        import sqlite3
        
        print("✅ Core dependencies importable")
        
        # Test app import (without running)
        spec = __import__('app_render')
        print("✅ app_render.py imports successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ App validation error: {e}")
        return False

def generate_deployment_info():
    """Generate deployment information"""
    info = {
        "service_name": "mental-health-chatbot",
        "platform": "render",
        "memory_limit": "512MB",
        "port": 10000,
        "health_endpoint": "/health",
        "main_endpoint": "/",
        "docker_image": "python:3.11-slim",
        "app_file": "app_render.py",
        "requirements": "requirements_render.txt",
        "features": [
            "Mental health chatbot with keyword-based responses",
            "Sentiment analysis using TextBlob",
            "SQLite database for chat logging",
            "Simple mental health assessment",
            "Crisis resource information",
            "Memory optimized for 512MB RAM"
        ],
        "endpoints": {
            "/": "Main chat interface (HTML)",
            "/health": "Health check for monitoring",
            "/chat": "POST endpoint for chat messages",
            "/assessment": "Mental health assessment form"
        }
    }
    
    with open('deployment_info.json', 'w') as f:
        json.dump(info, f, indent=2)
    
    print("✅ Deployment info generated: deployment_info.json")
    return True

def create_env_template():
    """Create environment variable template"""
    env_template = """# Environment Variables for Render Deployment
# Copy these to your Render dashboard

# Required
PORT=10000
FLASK_ENV=production
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Optional (will use defaults if not set)
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///mental_health.db

# Render automatically provides these:
# RENDER=true
# RENDER_SERVICE_NAME=mental-health-chatbot
# RENDER_SERVICE_ID=your-service-id
"""
    
    with open('.env.render', 'w') as f:
        f.write(env_template)
    
    print("✅ Environment template created: .env.render")
    return True

def print_deployment_instructions():
    """Print step-by-step deployment instructions"""
    instructions = """
🚀 RENDER DEPLOYMENT INSTRUCTIONS
================================

1. Prepare Repository:
   - Commit all files to your Git repository
   - Push to GitHub/GitLab

2. Create Render Service:
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your repository
   - Select the repository containing this project

3. Configure Service:
   - Name: mental-health-chatbot
   - Environment: Docker
   - Region: Choose closest to your users
   - Branch: main (or your default branch)
   - Dockerfile path: ./Dockerfile

4. Set Environment Variables:
   - PORT: 10000 (auto-set by Render)
   - FLASK_ENV: production
   - PYTHONUNBUFFERED: 1
   - PYTHONDONTWRITEBYTECODE: 1
   - SECRET_KEY: (generate a secure key)

5. Deploy:
   - Click "Create Web Service"
   - Wait for build and deployment (5-10 minutes)
   - Check health at: https://your-app.onrender.com/health

6. Test Endpoints:
   - Main chat: https://your-app.onrender.com/
   - Health check: https://your-app.onrender.com/health
   - Assessment: https://your-app.onrender.com/assessment

📊 RESOURCE USAGE:
- Memory: ~200-300MB (well under 512MB limit)
- Storage: ~100MB for app + logs
- Build time: 3-5 minutes
- Cold start: 10-15 seconds

⚠️ LIMITATIONS (Free Tier):
- Service sleeps after 15 minutes of inactivity
- 750 hours/month free compute time
- Shared resources with other users

🔧 TROUBLESHOOTING:
- Check build logs in Render dashboard
- Verify all environment variables are set
- Use health endpoint to monitor service status
- Check application logs for runtime errors

✅ Your app is ready for deployment!
"""
    
    print(instructions)

def main():
    """Main deployment preparation workflow"""
    print("🚀 Render Deployment Preparation")
    print("=" * 40)
    
    # Run all checks
    checks = [
        ("Checking required files", check_requirements),
        ("Validating Dockerfile", validate_dockerfile), 
        ("Validating requirements", validate_requirements),
        ("Testing app import", test_app_import),
        ("Generating deployment info", generate_deployment_info),
        ("Creating env template", create_env_template)
    ]
    
    for description, check_func in checks:
        print(f"\n{description}...")
        if not check_func():
            print(f"❌ {description} failed")
            sys.exit(1)
    
    print("\n🎉 Deployment preparation completed successfully!")
    print("✅ Ready for Render cloud deployment")
    
    # Print instructions
    print_deployment_instructions()

if __name__ == "__main__":
    main()
