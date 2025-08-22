#!/usr/bin/env python3
"""
Simple test script to verify the kakashi package works correctly.
"""

import sys
import os

# Add the current directory to Python path for testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test basic import functionality."""
    try:
        import kakashi
        print(f"✅ Successfully imported kakashi version {kakashi.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import kakashi: {e}")
        return False

def test_basic_functionality():
    """Test basic logging functionality."""
    try:
        import kakashi
        
        # Test basic setup
        kakashi.setup()
        print("✅ Basic setup successful")
        
        # Test basic logging
        kakashi.info("Test info message")
        kakashi.warning("Test warning message")
        kakashi.error("Test error message")
        print("✅ Basic logging successful")
        
        # Test logger creation
        logger = kakashi.get_logger("test")
        logger.info("Test logger message")
        print("✅ Logger creation successful")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_console_scripts():
    """Test if console scripts are available."""
    try:
        import kakashi.examples.basic_usage
        print("✅ Console script modules importable")
        return True
    except ImportError as e:
        print(f"❌ Console script modules not importable: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Kakashi Package")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_import),
        ("Basic Functionality Test", test_basic_functionality),
        ("Console Scripts Test", test_console_scripts),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Package is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the package structure.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
