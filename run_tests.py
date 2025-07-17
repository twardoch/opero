#!/usr/bin/env python3
"""
Simple test runner to verify the test suite works.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    repo_root = Path(__file__).parent
    os.chdir(repo_root)
    
    # Add src to path
    sys.path.insert(0, str(repo_root / "src"))
    
    print("Testing basic imports...")
    try:
        import opero
        print(f"✅ Opero imported successfully (version: {opero.__version__})")
    except Exception as e:
        print(f"❌ Failed to import opero: {e}")
        return 1
    
    print("\nTesting core functionality...")
    try:
        from opero import opero as opero_decorator
        
        @opero_decorator(cache=False)
        def test_function(x):
            return x * 2
        
        result = test_function(5)
        assert result == 10
        print("✅ Basic opero decorator works")
    except Exception as e:
        print(f"❌ Basic opero decorator failed: {e}")
        return 1
    
    print("\nTesting imports of all modules...")
    try:
        from opero.core import get_retry_decorator, get_fallback_decorator
        from opero.decorators import opero, opmap
        from opero.exceptions import AllFailedError, OperoError
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return 1
    
    print("\n✅ All basic tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())