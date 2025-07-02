# Flask Social Media Application - Test Suite

This directory contains all unit tests for the Flask social media application.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── test_config.py              # Test configuration and fixtures
├── test_models.py              # Database model tests
├── test_auth.py                # Authentication tests (login, register, logout)
├── test_authorization.py       # Authorization and ownership tests
├── test_routes.py              # Route and endpoint tests
├── test_logging.py             # Logging system tests
└── test_setup.py               # Basic setup verification tests
```

## Running Tests

### From the backend directory:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests with coverage
python -m pytest

# Run specific test files
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_models.py -v

# Use the test runner script
python run_tests.py --all           # Run all tests with coverage
python run_tests.py --auth          # Run authentication tests only
python run_tests.py --models        # Run database model tests only
python run_tests.py --routes        # Run route tests only
python run_tests.py --logging       # Run logging tests only
python run_tests.py --clean         # Clean test artifacts
```

## Test Coverage

The test suite provides comprehensive coverage for:

- **Authentication**: Login, registration, logout, session management
- **Authorization**: Ownership-based access control for posts and comments
- **Database Models**: User, Post, Like, Comment models with relationships
- **API Routes**: All endpoints with success and error cases
- **Logging System**: Structured logging, security events, performance metrics
- **Security**: Unauthorized access prevention, sensitive data masking

## Test Configuration

- Uses in-memory SQLite database for fast test execution
- Isolated test environment with proper setup and teardown
- Helper functions for creating test data (users, posts, comments)
- Mock support for external dependencies

## Writing New Tests

When adding new tests:

1. Follow the existing naming convention: `test_*.py`
2. Import parent directory modules using the standard pattern:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   ```
3. Use the test configuration and fixtures from `test_config.py`
4. Group related tests in classes
5. Use descriptive test names that explain what is being tested

## Coverage Reports

After running tests with coverage, view the HTML report:
```bash
open htmlcov/index.html
```