"""
Test configuration for Flask Social Media Application
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to Python path to import application modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from models import db
from logging_config import LoggingConfig


class TestConfig:
    """Test configuration class"""
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Testing configurations
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    
    # Disable logging during tests to reduce noise
    LOG_LEVEL = 'CRITICAL'


def create_test_app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config.from_object(TestConfig)
    
    # Initialize database
    db.init_app(app)
    
    # Initialize auth middleware for testing
    from auth_middleware import AuthMiddleware
    AuthMiddleware(app)
    
    # Setup minimal logging for tests
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    
    return app


def setup_test_db(app):
    """Setup test database with tables"""
    with app.app_context():
        db.create_all()


def teardown_test_db(app):
    """Cleanup test database"""
    with app.app_context():
        db.session.remove()
        db.drop_all()


def create_test_user(username="testuser", password="testpass"):
    """Helper function to create a test user"""
    from models import User
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def create_test_post(user, caption="Test post caption"):
    """Helper function to create a test post"""
    from models import Post
    post = Post(caption=caption, user_id=user.id)
    db.session.add(post)
    db.session.commit()
    return post


def create_test_comment(user, post, text="Test comment"):
    """Helper function to create a test comment"""
    from models import Comment
    comment = Comment(text=text, user_id=user.id, post_id=post.id)
    db.session.add(comment)
    db.session.commit()
    return comment


def login_user(client, username="testuser", password="testpass"):
    """Helper function to login a user via test client"""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def logout_user(client):
    """Helper function to logout current user"""
    return client.get('/logout', follow_redirects=True)