"""
Authentication Middleware for Flask Social Media Application

This middleware handles authentication for all requests, managing user sessions
and providing centralized authentication logic.
"""

from flask import session, request, g, redirect, url_for, flash
from models import User
from social_media_logger import social_logger
import logging


class AuthMiddleware:
    """Authentication middleware for Flask application"""
    
    def __init__(self, app=None):
        self.app = app
        self.public_routes = {
            'login', 'register', 'static', 'favicon'
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        app.before_request(self.before_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        """Process request before routing to check authentication"""
        # Clear any existing user context
        g.current_user = None
        
        # Skip auth checks for static files
        if request.endpoint == 'static':
            return
        
        # Load user from session if exists
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                g.current_user = user
            else:
                # Session has invalid user_id, clear it
                session.pop('user_id', None)
                social_logger.log_security_event(
                    event_type="invalid_session",
                    description="Session contained invalid user_id",
                    additional_data={'session_user_id': session.get('user_id')}
                )
        
        # Check if route requires authentication
        if self._requires_auth():
            if not g.current_user:
                # Store attempted URL for redirect after login
                session['next_url'] = request.url
                flash('Please login to access this page', 'error')
                return redirect(url_for('login'))
    
    def teardown_request(self, exception):
        """Clean up request context"""
        g.current_user = None
    
    def _requires_auth(self):
        """Check if current route requires authentication"""
        # If no endpoint, assume auth required
        if not request.endpoint:
            return True
        
        # Check if route is in public routes
        if request.endpoint in self.public_routes:
            return False
        
        # All other routes require authentication
        return True
    
    def is_authenticated(self):
        """Check if current user is authenticated"""
        return g.current_user is not None
    
    def get_current_user(self):
        """Get current authenticated user"""
        return getattr(g, 'current_user', None)
    
    def login_user(self, user):
        """Login a user and create session"""
        session['user_id'] = user.id
        g.current_user = user
        social_logger.log_login_attempt(user.username, success=True)
    
    def logout_user(self):
        """Logout current user and clear session"""
        user = g.current_user
        if user:
            social_logger.log_logout(user.id, user.username)
        
        session.pop('user_id', None)
        g.current_user = None
    
    def require_auth(self, f):
        """Decorator to ensure route requires authentication"""
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.is_authenticated():
                flash('Please login to access this page', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function