#!/usr/bin/env python3
"""
Quick application test to verify basic functionality
"""

import os
import sys
import importlib
from pathlib import Path

def test_imports():
    """Test critical imports"""
    print("🔍 Testing critical imports...")
    
    try:
        import flask
        print("✅ Flask import successful")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import fastapi
        print("✅ FastAPI import successful")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        from main import app as flask_app
        print("✅ Flask app import successful")
    except ImportError as e:
        print(f"❌ Flask app import failed: {e}")
        return False
    
    try:
        from fastapi_app import app as fastapi_app
        print("✅ FastAPI app import successful")
    except ImportError as e:
        print(f"❌ FastAPI app import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        from main import engine, init_db
        
        # Test database initialization
        if init_db():
            print("✅ Database initialization successful")
            return True
        else:
            print("❌ Database initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    try:
        from config_manager import get_config
        config = get_config()
        print("✅ Configuration loading successful")
        
        # Test critical config values
        if config.SECRET_KEY and config.SECRET_KEY != 'your_secret_key_here':
            print("✅ SECRET_KEY is configured")
        else:
            print("⚠️  SECRET_KEY needs configuration")
        
        if config.GOOGLE_API_KEY and config.GOOGLE_API_KEY != 'your_google_api_key_here':
            print("✅ GOOGLE_API_KEY is configured")
        else:
            print("⚠️  GOOGLE_API_KEY needs configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Mental Health App - Quick Test")
    print("=" * 50)
    
    # Load environment
    if Path('.env').exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("📄 Environment loaded from .env")
        except ImportError:
            print("⚠️  python-dotenv not available, using system environment")
    
    # Run tests
    tests = [
        test_imports,
        test_database_connection,
        test_configuration,
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! Application is ready to start.")
        print("\n🚀 To start the application:")
        print("   python app.py  # For Hugging Face Spaces")
        print("   # Or for local development:")
        print("   python main.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
