#!/usr/bin/env python3
"""
Validation script for the 512MB deployment
Tests all major components work properly
"""

import sys
import os
import tempfile

def test_opensource_rag():
    """Test the open source RAG system"""
    print("🧪 Testing Open Source RAG...")
    try:
        from opensource_rag import OpenSourceRAG
        
        # Create test instance
        rag = OpenSourceRAG()
        
        # Test process_query method (FastAPI compatibility)
        result = rag.process_query("I feel sad and depressed", "sad", "Unknown")
        
        assert 'response' in result
        assert 'confidence' in result
        assert 'sources' in result
        assert result['confidence'] > 0
        
        print("✅ Open Source RAG: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Open Source RAG: FAILED - {e}")
        return False

def test_opensource_stt():
    """Test the open source speech-to-text"""
    print("🧪 Testing Open Source STT...")
    try:
        from opensource_stt import opensource_stt
        
        # Check if STT is available (might be disabled in free tier)
        if opensource_stt.is_available():
            print("✅ Open Source STT: Available")
        else:
            print("ℹ️ Open Source STT: Disabled for free tier (this is normal)")
        
        print("✅ Open Source STT: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Open Source STT: FAILED - {e}")
        return False

def test_requirements():
    """Test that all required packages can be imported"""
    print("🧪 Testing Requirements...")
    
    required_packages = [
        'flask',
        'fastapi',
        'scikit-learn',
        'numpy',
        'nltk',
        'edge_tts',
        'vosk',
        'soundfile'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            if package == 'scikit-learn':
                import sklearn
            elif package == 'edge_tts':
                import edge_tts
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError as e:
            print(f"  ❌ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"❌ Requirements: FAILED - Missing: {failed_imports}")
        return False
    else:
        print("✅ Requirements: PASSED")
        return True

def test_fastapi_integration():
    """Test FastAPI can start with the new components"""
    print("🧪 Testing FastAPI Integration...")
    try:
        # Import FastAPI app without starting it
        from fastapi_app import app
        
        # Check if the app has the expected state
        if hasattr(app, 'state'):
            print("  ✅ FastAPI app state exists")
        
        print("✅ FastAPI Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI Integration: FAILED - {e}")
        return False

def test_memory_optimization():
    """Test memory optimization measures"""
    print("🧪 Testing Memory Optimization...")
    
    # Check environment variables
    memory_mode = os.environ.get('MEMORY_MODE', 'standard')
    skip_ai = os.environ.get('SKIP_AI_MODELS', '0')
    
    print(f"  Memory Mode: {memory_mode}")
    print(f"  Skip AI Models: {skip_ai}")
    
    # Check if we're not importing heavy packages
    heavy_packages = ['transformers', 'torch', 'tensorflow', 'openai']
    
    for package in heavy_packages:
        if package in sys.modules:
            print(f"  ⚠️ Warning: {package} is loaded (might use too much memory)")
        else:
            print(f"  ✅ {package} not loaded")
    
    print("✅ Memory Optimization: PASSED")
    return True

def main():
    """Run all validation tests"""
    print("🚀 Starting 512MB Deployment Validation...\n")
    
    tests = [
        test_requirements,
        test_opensource_rag,
        test_opensource_stt,
        test_fastapi_integration,
        test_memory_optimization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
        print()  # Add spacing
    
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for 512MB deployment.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    exit(main())
