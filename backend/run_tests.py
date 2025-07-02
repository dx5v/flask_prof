#!/usr/bin/env python3
"""
Test runner script for Flask Social Media Application

This script provides convenient ways to run different test suites and generate reports.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command and handle errors"""
    print(f"{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install -r requirements-test.txt")
        return False


def install_dependencies():
    """Install test dependencies"""
    return run_command([
        sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
    ], "Installing test dependencies")


def run_all_tests():
    """Run all tests with coverage"""
    return run_command([
        "python", "-m", "pytest", 
        "--cov=.", 
        "--cov-report=html", 
        "--cov-report=term-missing",
        "-v"
    ], "Running all tests with coverage")


def run_unit_tests():
    """Run only unit tests"""
    return run_command([
        "python", "-m", "pytest", 
        "-m", "unit",
        "-v"
    ], "Running unit tests")


def run_auth_tests():
    """Run authentication tests"""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_auth.py",
        "-v"
    ], "Running authentication tests")


def run_model_tests():
    """Run database model tests"""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_models.py",
        "-v"
    ], "Running database model tests")


def run_route_tests():
    """Run route/endpoint tests"""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_routes.py",
        "-v"
    ], "Running route tests")


def run_auth_tests_only():
    """Run authorization tests"""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_authorization.py",
        "-v"
    ], "Running authorization tests")


def run_logging_tests():
    """Run logging system tests"""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_logging.py",
        "-v"
    ], "Running logging tests")


def run_fast_tests():
    """Run tests excluding slow ones"""
    return run_command([
        "python", "-m", "pytest", 
        "-m", "not slow",
        "-v"
    ], "Running fast tests")


def run_security_tests():
    """Run security-related tests"""
    return run_command([
        "python", "-m", "pytest", 
        "-m", "security",
        "-v"
    ], "Running security tests")


def generate_coverage_report():
    """Generate detailed coverage report"""
    return run_command([
        "python", "-m", "coverage", "html"
    ], "Generating HTML coverage report")


def clean_test_artifacts():
    """Clean test artifacts and cache files"""
    artifacts = [
        ".pytest_cache",
        "__pycache__",
        "htmlcov",
        ".coverage",
        "coverage.xml"
    ]
    
    print("Cleaning test artifacts...")
    for artifact in artifacts:
        if os.path.exists(artifact):
            if os.path.isdir(artifact):
                import shutil
                shutil.rmtree(artifact)
                print(f"Removed directory: {artifact}")
            else:
                os.remove(artifact)
                print(f"Removed file: {artifact}")
    
    # Clean Python cache files recursively
    for root, dirs, files in os.walk("."):
        for dir_name in dirs[:]:
            if dir_name == "__pycache__":
                import shutil
                shutil.rmtree(os.path.join(root, dir_name))
                dirs.remove(dir_name)
        for file_name in files:
            if file_name.endswith(".pyc"):
                os.remove(os.path.join(root, file_name))
    
    print("✅ Test artifacts cleaned")
    return True


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="Test runner for Flask Social Media Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all           # Run all tests with coverage
  python run_tests.py --auth          # Run authentication tests only
  python run_tests.py --models        # Run database model tests only
  python run_tests.py --routes        # Run route tests only
  python run_tests.py --logging       # Run logging tests only
  python run_tests.py --fast          # Run fast tests (exclude slow)
  python run_tests.py --security      # Run security tests only
  python run_tests.py --install       # Install test dependencies
  python run_tests.py --clean         # Clean test artifacts
  python run_tests.py --coverage      # Generate coverage report
        """
    )
    
    parser.add_argument("--all", action="store_true", 
                       help="Run all tests with coverage")
    parser.add_argument("--unit", action="store_true", 
                       help="Run unit tests only")
    parser.add_argument("--auth", action="store_true", 
                       help="Run authentication tests")
    parser.add_argument("--models", action="store_true", 
                       help="Run database model tests")
    parser.add_argument("--routes", action="store_true", 
                       help="Run route/endpoint tests")
    parser.add_argument("--authorization", action="store_true", 
                       help="Run authorization tests")
    parser.add_argument("--logging", action="store_true", 
                       help="Run logging system tests")
    parser.add_argument("--fast", action="store_true", 
                       help="Run fast tests (exclude slow)")
    parser.add_argument("--security", action="store_true", 
                       help="Run security-related tests")
    parser.add_argument("--install", action="store_true", 
                       help="Install test dependencies")
    parser.add_argument("--coverage", action="store_true", 
                       help="Generate HTML coverage report")
    parser.add_argument("--clean", action="store_true", 
                       help="Clean test artifacts and cache files")
    
    args = parser.parse_args()
    
    # Change to backend directory
    os.chdir(Path(__file__).parent)
    
    success = True
    
    if args.install:
        success &= install_dependencies()
    
    if args.clean:
        success &= clean_test_artifacts()
    
    if args.all:
        success &= run_all_tests()
    elif args.unit:
        success &= run_unit_tests()
    elif args.auth:
        success &= run_auth_tests()
    elif args.models:
        success &= run_model_tests()
    elif args.routes:
        success &= run_route_tests()
    elif args.authorization:
        success &= run_auth_tests_only()
    elif args.logging:
        success &= run_logging_tests()
    elif args.fast:
        success &= run_fast_tests()
    elif args.security:
        success &= run_security_tests()
    elif args.coverage:
        success &= generate_coverage_report()
    else:
        # Default: run all tests
        print("No specific test type specified. Running all tests...")
        success &= run_all_tests()
    
    if success:
        print("\n🎉 All operations completed successfully!")
        if args.all or (not any(vars(args).values())):
            print("\n📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n💥 Some operations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()