#!/usr/bin/env python3
"""Run all CartInventoryManager tests."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Import pytest
try:
    import pytest
except ImportError:
    print("pytest not installed. Running tests with unittest instead.")
    import unittest
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    sys.exit(0 if result.wasSuccessful() else 1)

# Run tests with pytest
if __name__ == "__main__":
    # Get the directory containing test files
    test_dir = Path(__file__).parent
    
    # Run pytest with coverage if available
    args = [
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        str(test_dir),  # Test directory
    ]
    
    # Try to add coverage
    try:
        import pytest_cov
        args.extend([
            "--cov=tools.ecommerce.cart_inventory_manager",
            "--cov-report=term-missing"
        ])
    except ImportError:
        pass
    
    # Run tests
    exit_code = pytest.main(args)
    sys.exit(exit_code)