#!/usr/bin/env python3
"""
Test runner for the School Menu Notifier project

This script runs all unit tests and provides a comprehensive summary.
"""

import unittest
import sys
import os

def run_tests():
    """Run all tests and return results."""
    # Discover and run all tests
    loader = unittest.TestLoader()
    # Look in the tests directory
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result

def main():
    """Main function to run tests and display results."""
    print("🧪 Running School Menu Notifier Tests")
    print("=" * 50)
    
    # Run the tests
    result = run_tests()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    # Display summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    
    print(f"Total Tests Run: {total_tests}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    
    if failures > 0:
        print(f"\n❌ Failures ({failures}):")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print(f"\n💥 Errors ({errors}):")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if failures == 0 and errors == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {failures + errors} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
