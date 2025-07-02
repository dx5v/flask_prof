"""
Test to verify the test setup works correctly
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_config import create_test_app, setup_test_db, teardown_test_db, create_test_user


def test_test_setup():
    """Test that the test setup works correctly"""
    app = create_test_app()
    
    assert app is not None
    assert app.config['TESTING'] == True
    assert 'sqlite:///:memory:' in app.config['SQLALCHEMY_DATABASE_URI']


def test_test_user_creation():
    """Test that test user creation works"""
    app = create_test_app()
    setup_test_db(app)
    
    try:
        with app.app_context():
            user = create_test_user("testuser", "testpass")
            assert user.username == "testuser"
            assert user.check_password("testpass") == True
    finally:
        teardown_test_db(app)


if __name__ == '__main__':
    pytest.main([__file__])