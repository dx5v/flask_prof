from functools import wraps
from flask import session, redirect, url_for, flash, abort
from models import User, Post, Comment


def get_current_user():
    """Get the current user from session."""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def post_owner_required(f):
    """Decorator to ensure user owns the post they're trying to access."""
    @wraps(f)
    def decorated_function(post_id, *args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        
        current_user = get_current_user()
        post = Post.query.get_or_404(post_id)
        
        if post.user_id != current_user.id:
            abort(403)  # Forbidden
        
        return f(post_id, *args, **kwargs)
    return decorated_function


def comment_owner_required(f):
    """Decorator to ensure user owns the comment they're trying to access."""
    @wraps(f)
    def decorated_function(comment_id, *args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        
        current_user = get_current_user()
        comment = Comment.query.get_or_404(comment_id)
        
        if comment.user_id != current_user.id:
            abort(403)  # Forbidden
        
        return f(comment_id, *args, **kwargs)
    return decorated_function