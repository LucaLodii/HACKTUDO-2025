#!/usr/bin/env python3
"""
Test runner for sofIA application
Provides different test execution modes and reporting
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    if description:
        print(f"🚀 {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Exit code: {result.returncode}")
    print(f"Duration: {end_time - start_time:.2f} seconds")
    
    if result.stdout:
        print("\nSTDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    return result

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking test dependencies...")
    
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} found")
    except ImportError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    
    try:
        import asyncio
        print("✅ asyncio available")
    except ImportError:
        print("❌ asyncio not available")
        return False
    
    # Check for optional dependencies
    optional_deps = {
        'pytest-asyncio': 'pytest_asyncio',
        'pytest-cov': 'pytest_cov',
        'pytest-html': 'pytest_html',
        'pytest-xdist': 'xdist'
    }
    
    for dep_name, module_name in optional_deps.items():
        try:
            __import__(module_name)
            print(f"✅ {dep_name} available")
        except ImportError:
            print(f"⚠️  {dep_name} not available (optional)")
    
    return True

def run_unit_tests():
    """Run unit tests only"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_subscription_management.py",
        "tests/test_sofia_agent.py",
        "-m", "unit",
        "-v"
    ]
    
    return run_command(cmd, "Running Unit Tests")

def run_integration_tests():
    """Run integration tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_orchestrator.py",
        "tests/test_api_integration.py",
        "-m", "integration",
        "-v"
    ]
    
    return run_command(cmd, "Running Integration Tests")

def run_e2e_tests():
    """Run end-to-end tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_end_to_end.py",
        "-m", "e2e",
        "-v"
    ]
    
    return run_command(cmd, "Running End-to-End Tests")

def run_all_tests():
    """Run all tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, "Running All Tests")

def run_quick_tests():
    """Run quick tests (excluding slow ones)"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "not slow",
        "-v"
    ]
    
    return run_command(cmd, "Running Quick Tests")

def run_specific_test_file(test_file):
    """Run a specific test file"""
    test_path = Path("tests") / test_file
    if not test_path.exists():
        print(f"❌ Test file not found: {test_path}")
        return None
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "-v"
    ]
    
    return run_command(cmd, f"Running {test_file}")

def run_coverage_report():
    """Run tests with coverage report"""
    try:
        import pytest_cov
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "--cov=sofIA",
            "--cov=orchestrator",
            "--cov-report=html",
            "--cov-report=term",
            "-v"
        ]
        
        result = run_command(cmd, "Running Tests with Coverage")
        
        if result.returncode == 0:
            print("\n✅ Coverage report generated in htmlcov/index.html")
        
        return result
        
    except ImportError:
        print("❌ pytest-cov not installed. Install with: pip install pytest-cov")
        return None

def run_parallel_tests():
    """Run tests in parallel"""
    try:
        import xdist
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-n", "auto",  # Use all available CPUs
            "-v"
        ]
        
        return run_command(cmd, "Running Tests in Parallel")
        
    except ImportError:
        print("❌ pytest-xdist not installed. Install with: pip install pytest-xdist")
        return None

def validate_test_structure():
    """Validate test structure and files"""
    print("🔍 Validating test structure...")
    
    test_files = [
        "tests/conftest.py",
        "tests/test_subscription_management.py", 
        "tests/test_sofia_agent.py",
        "tests/test_orchestrator.py",
        "tests/test_api_integration.py",
        "tests/test_end_to_end.py",
        "tests/test_app.py",
        "tests/pytest.ini"
    ]
    
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
        else:
            print(f"✅ {test_file}")
    
    if missing_files:
        print(f"\n❌ Missing test files: {missing_files}")
        return False
    
    print(f"\n✅ All {len(test_files)} test files found!")
    return True

def run_test_suite_info():
    """Display information about the test suite"""
    print("📊 sofIA Test Suite Information")
    print("="*60)
    
    test_info = {
        "Test Files": [
            "test_subscription_management.py - Subscription tools and workflows",
            "test_sofia_agent.py - sofIA agent integration and functionality", 
            "test_orchestrator.py - Multi-agent orchestration and A2A communication",
            "test_api_integration.py - API endpoints and external service integration",
            "test_end_to_end.py - Complete user journeys and scenarios",
            "test_app.py - Main application initialization and configuration"
        ],
        "Test Categories": [
            "unit - Individual component tests",
            "integration - Component interaction tests", 
            "e2e - End-to-end user journey tests",
            "api - API endpoint tests",
            "database - Database integration tests",
            "whatsapp - WhatsApp bridge tests",
            "subscription - Subscription management tests",
            "payment - Payment processing tests",
            "agent - AI agent functionality tests"
        ],
        "Key Features Tested": [
            "🔄 Subscription discovery and management",
            "⏰ Proactive renewal reminders",
            "📈 Plan upgrade/downgrade workflows",
            "💳 AP2 payment processing",
            "🤖 Multi-agent coordination (A2A)",
            "📱 WhatsApp integration",
            "🛡️ Security and validation",
            "⚡ Performance and concurrency",
            "🐛 Error handling and recovery"
        ]
    }
    
    for category, items in test_info.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  • {item}")
    
    print(f"\n🎯 Total Test Coverage:")
    print(f"  • 6 test files")
    print(f"  • 100+ individual test cases")
    print(f"  • Complete user journey coverage")
    print(f"  • Mock data fallback for all operations")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="sofIA Test Runner")
    parser.add_argument("--mode", "-m", 
                       choices=["unit", "integration", "e2e", "all", "quick", "coverage", "parallel", "info"],
                       default="quick",
                       help="Test execution mode")
    parser.add_argument("--file", "-f",
                       help="Run specific test file")
    parser.add_argument("--check-deps", "-c",
                       action="store_true",
                       help="Check test dependencies")
    parser.add_argument("--validate", "-v",
                       action="store_true", 
                       help="Validate test structure")
    
    args = parser.parse_args()
    
    print("🧪 sofIA Test Runner")
    print("="*60)
    
    # Check dependencies if requested
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
        return
    
    # Validate test structure if requested
    if args.validate:
        if not validate_test_structure():
            sys.exit(1)
        return
    
    # Show test suite info
    if args.mode == "info":
        run_test_suite_info()
        return
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed. Install with: pip install pytest pytest-asyncio")
        sys.exit(1)
    
    # Run specific test file
    if args.file:
        result = run_specific_test_file(args.file)
        if result:
            sys.exit(result.returncode)
        else:
            sys.exit(1)
    
    # Run tests based on mode
    result = None
    if args.mode == "unit":
        result = run_unit_tests()
    elif args.mode == "integration":
        result = run_integration_tests()
    elif args.mode == "e2e":
        result = run_e2e_tests()
    elif args.mode == "all":
        result = run_all_tests()
    elif args.mode == "quick":
        result = run_quick_tests()
    elif args.mode == "coverage":
        result = run_coverage_report()
    elif args.mode == "parallel":
        result = run_parallel_tests()
    
    if result:
        print(f"\n{'='*60}")
        if result.returncode == 0:
            print("✅ Tests completed successfully!")
        else:
            print("❌ Tests failed!")
        print(f"Exit code: {result.returncode}")
        print("="*60)
        
        sys.exit(result.returncode)
    else:
        print("❌ Test execution failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
