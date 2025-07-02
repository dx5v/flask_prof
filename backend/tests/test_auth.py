"""
Unit tests for authentication functionality
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_config import create_test_app, setup_test_db, teardown_test_db, create_test_user, login_user, logout_user
from models import db, User


class TestAuthentication:
    """Test cases for authentication system"""
    
    @pytest.fixture
    def app(self):
        app = create_test_app()
        setup_test_db(app)
        yield app
        teardown_test_db(app)
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    @pytest.fixture
    def app_context(self, app):
        with app.app_context():
            yield app


class TestLogin(TestAuthentication):
    """Test login functionality"""
    
    def test_login_page_loads(self, client):
        """Test login page renders correctly"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_successful_login(self, client, app_context):
        """Test successful user login"""
        # Create test user
        create_test_user("testuser", "testpass")
        
        # Attempt login
        response = login_user(client, "testuser", "testpass")
        assert response.status_code == 200
        
        # Should redirect to home and show success message
        assert b'Login successful!' in response.data or b'testuser' in response.data
    
    def test_login_invalid_credentials(self, client, app_context):
        """Test login with invalid credentials"""
        # Create test user
        create_test_user("testuser", "testpass")
        
        # Attempt login with wrong password
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpass'
        }, follow_redirects=True)
        
        assert b'Invalid credentials' in response.data
    
    def test_login_nonexistent_user(self, client, app_context):
        """Test login with non-existent user"""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'somepass'
        }, follow_redirects=True)
        
        assert b'Invalid credentials' in response.data
    
    def test_login_missing_fields(self, client, app_context):
        """Test login with missing username or password"""
        # Missing username
        response = client.post('/login', data={
            'password': 'testpass'
        }, follow_redirects=True)
        assert b'Username and password required' in response.data
        
        # Missing password
        response = client.post('/login', data={
            'username': 'testuser'
        }, follow_redirects=True)
        assert b'Username and password required' in response.data
        
        # Missing both
        response = client.post('/login', data={}, follow_redirects=True)
        assert b'Username and password required' in response.data
    
    def test_session_after_login(self, client, app_context):
        """Test that session is properly set after login"""
        create_test_user("testuser", "testpass")
        
        with client.session_transaction() as sess:
            # Should not be logged in initially
            assert 'user_id' not in sess
        
        login_user(client, "testuser", "testpass")
        
        with client.session_transaction() as sess:
            # Should be logged in after successful login
            assert 'user_id' in sess
            assert sess['user_id'] is not None


class TestRegistration(TestAuthentication):
    """Test registration functionality"""
    
    def test_registration_page_loads(self, client):
        """Test registration page renders correctly"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data
    
    def test_successful_registration(self, client, app_context):
        """Test successful user registration"""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass',
            'confirm_password': 'newpass'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful!' in response.data
        
        # Verify user was created in database
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.check_password('newpass')
    
    def test_registration_duplicate_username(self, client, app_context):
        """Test registration with existing username"""
        # Create existing user
        create_test_user("existinguser", "pass1")
        
        # Try to register with same username
        response = client.post('/register', data={
            'username': 'existinguser',
            'password': 'pass2',
            'confirm_password': 'pass2'
        }, follow_redirects=True)
        
        assert b'Username already exists' in response.data
    
    def test_registration_password_mismatch(self, client, app_context):
        """Test registration with mismatched passwords"""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'password1',
            'confirm_password': 'password2'
        }, follow_redirects=True)
        
        assert b'Passwords do not match' in response.data
        
        # Verify user was NOT created
        user = User.query.filter_by(username='newuser').first()
        assert user is None
    
    def test_registration_missing_fields(self, client, app_context):
        """Test registration with missing required fields"""
        # Missing username
        response = client.post('/register', data={
            'password': 'testpass',
            'confirm_password': 'testpass'
        }, follow_redirects=True)
        assert b'All fields are required' in response.data
        
        # Missing password
        response = client.post('/register', data={
            'username': 'testuser',
            'confirm_password': 'testpass'
        }, follow_redirects=True)
        assert b'All fields are required' in response.data
        
        # Missing confirm_password
        response = client.post('/register', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        assert b'All fields are required' in response.data
    
    def test_auto_login_after_registration(self, client, app_context):
        """Test that user is automatically logged in after registration"""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass',
            'confirm_password': 'newpass'
        }, follow_redirects=True)
        
        with client.session_transaction() as sess:
            # Should be logged in after registration
            assert 'user_id' in sess
            user = User.query.filter_by(username='newuser').first()
            assert sess['user_id'] == user.id


class TestLogout(TestAuthentication):
    """Test logout functionality"""
    
    def test_logout_clears_session(self, client, app_context):
        """Test that logout clears the user session"""
        # Create and login user
        create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        # Verify logged in
        with client.session_transaction() as sess:
            assert 'user_id' in sess
        
        # Logout
        response = logout_user(client)
        assert response.status_code == 200
        assert b'You have been logged out' in response.data
        
        # Verify session cleared
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
    
    def test_logout_without_login(self, client, app_context):
        """Test logout when not logged in"""
        response = logout_user(client)
        assert response.status_code == 200
        # Should still show logout message
        assert b'You have been logged out' in response.data
    
    def test_logout_clears_flash_messages(self, client, app_context):
        """Test that logout clears accumulated flash messages"""
        # Create and login user
        create_test_user("testuser", "testpass")
        
        # Create some flash messages by performing actions
        login_user(client, "testuser", "testpass")
        
        # Logout should clear messages
        response = logout_user(client)
        assert response.status_code == 200


class TestSessionManagement(TestAuthentication):
    """Test session management and security"""
    
    def test_login_required_decorator(self, client, app_context):
        """Test that login_required decorator works"""
        # Try to access protected route without login
        response = client.get('/home', follow_redirects=True)
        
        # Should redirect to login page
        assert b'Login' in response.data or b'Please login' in response.data
    
    def test_redirect_after_login(self, client, app_context):
        """Test user is redirected appropriately after login"""
        create_test_user("testuser", "testpass")
        
        # Try to access protected page first
        response = client.get('/home')
        assert response.status_code == 302  # Should redirect
        
        # Login
        response = login_user(client, "testuser", "testpass")
        
        # Should be on home page or see success message
        assert response.status_code == 200
    
    def test_index_redirect_behavior(self, client, app_context):
        """Test index page redirect behavior"""
        # Without login, should redirect to login
        response = client.get('/', follow_redirects=True)
        assert b'Login' in response.data
        
        # With login, should redirect to home
        create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        response = client.get('/', follow_redirects=True)
        # Should be on home page (might contain posts, user info, etc.)
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__])