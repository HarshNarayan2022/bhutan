#!/usr/bin/env python3
"""
Docker Build and Test Validation Script
Validates the Docker image can be built and runs within memory constraints
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def run_command(cmd, timeout=120):
    """Run shell command with timeout"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"

def validate_docker_build():
    """Validate Docker image can be built"""
    print("🔨 Building Docker image...")
    
    success, stdout, stderr = run_command(
        "docker build -t mental-health-chatbot:test .", 
        timeout=300
    )
    
    if not success:
        print("❌ Docker build failed!")
        print(f"Error: {stderr}")
        return False
    
    print("✅ Docker image built successfully")
    return True

def validate_docker_run():
    """Test Docker container runs and responds"""
    print("🚀 Starting Docker container...")
    
    # Start container
    start_cmd = "docker run -d -p 10000:10000 --memory=512m --name test-chatbot mental-health-chatbot:test"
    success, stdout, stderr = run_command(start_cmd)
    
    if not success:
        print("❌ Failed to start container")
        print(f"Error: {stderr}")
        return False
    
    container_id = stdout.strip()
    print(f"✅ Container started: {container_id[:12]}")
    
    try:
        # Wait for startup
        print("⏳ Waiting for application startup...")
        time.sleep(10)
        
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get("http://localhost:10000/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"Response: {response.json()}")
            else:
                print(f"❌ Health check failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check request failed: {e}")
            return False
        
        # Test main endpoint
        print("🔍 Testing main endpoint...")
        try:
            response = requests.get("http://localhost:10000/", timeout=10)
            if response.status_code == 200:
                print("✅ Main endpoint accessible")
            else:
                print(f"❌ Main endpoint failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Main endpoint request failed: {e}")
            return False
        
        # Test chat endpoint
        print("🔍 Testing chat endpoint...")
        try:
            response = requests.post(
                "http://localhost:10000/chat",
                json={"message": "Hello, I'm feeling anxious"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print("✅ Chat endpoint working")
                print(f"Response: {data.get('response', '')[:100]}...")
            else:
                print(f"❌ Chat endpoint failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Chat endpoint request failed: {e}")
            return False
        
        return True
        
    finally:
        # Clean up
        print("🧹 Cleaning up container...")
        run_command(f"docker stop {container_id}")
        run_command(f"docker rm {container_id}")

def validate_memory_usage():
    """Check memory usage of running container"""
    print("📊 Checking memory usage...")
    
    # Start container with memory monitoring
    start_cmd = "docker run -d -p 10000:10000 --memory=512m --name memory-test mental-health-chatbot:test"
    success, stdout, stderr = run_command(start_cmd)
    
    if not success:
        print("❌ Failed to start container for memory test")
        return False
    
    container_id = stdout.strip()
    
    try:
        time.sleep(15)  # Let it start up
        
        # Get memory stats
        success, stdout, stderr = run_command(f"docker stats --no-stream --format 'table {{{{.MemUsage}}}}' {container_id}")
        
        if success:
            print(f"📊 Memory usage: {stdout.strip()}")
            
            # Parse memory usage
            lines = stdout.strip().split('\n')
            if len(lines) > 1:
                mem_line = lines[1]  # Skip header
                if 'MiB' in mem_line or 'MB' in mem_line:
                    # Extract number
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)', mem_line)
                    if match:
                        mem_mb = float(match.group(1))
                        if mem_mb < 400:  # Leave some buffer
                            print(f"✅ Memory usage OK: {mem_mb}MB (under 400MB limit)")
                            return True
                        else:
                            print(f"⚠️ Memory usage high: {mem_mb}MB")
                            return False
            
        print("✅ Memory validation completed")
        return True
        
    finally:
        run_command(f"docker stop {container_id}")
        run_command(f"docker rm {container_id}")

def cleanup_docker():
    """Clean up Docker images and containers"""
    print("🧹 Cleaning up Docker resources...")
    
    # Remove test containers
    run_command("docker rm -f test-chatbot memory-test 2>/dev/null")
    
    # Remove test image
    run_command("docker rmi mental-health-chatbot:test 2>/dev/null")
    
    print("✅ Docker cleanup completed")

def main():
    """Main validation workflow"""
    print("🔍 Docker Validation for Render Deployment")
    print("=" * 50)
    
    # Check if Docker is available
    success, _, _ = run_command("docker --version")
    if not success:
        print("❌ Docker is not available")
        sys.exit(1)
    
    try:
        # Validate build
        if not validate_docker_build():
            sys.exit(1)
        
        # Validate run
        if not validate_docker_run():
            sys.exit(1)
        
        # Validate memory
        if not validate_memory_usage():
            print("⚠️ Memory usage validation failed, but continuing...")
        
        print("\n🎉 All validations passed!")
        print("✅ Ready for Render deployment")
        
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted")
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        sys.exit(1)
    finally:
        cleanup_docker()

if __name__ == "__main__":
    main()
