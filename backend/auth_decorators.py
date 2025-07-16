from functools import wraps
from flask import g, redirect, url_for, flash, abort
from models import Post, Comment
import logging


def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.current_user:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def post_owner_required(f):
    """Decorator to ensure user owns the post they're trying to access."""
    @wraps(f)
    def decorated_function(post_id, *args, **kwargs):
        if not g.current_user:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        
        post = Post.query.get_or_404(post_id)
        
        if post.user_id != g.current_user.id:
            # Log unauthorized access attempt
            security_logger = logging.getLogger('security')
            security_logger.warning(
                "Unauthorized post access attempt",
                extra={
                    'event_type': 'unauthorized_access',
                    'resource_type': 'post',
                    'resource_id': post_id,
                    'user_id': g.current_user.id,
                    'owner_id': post.user_id,
                    'attempted_action': f.__name__
                }
            )
            abort(403)  # Forbidden
        
        return f(post_id, *args, **kwargs)
    return decorated_function


def comment_owner_required(f):
    """Decorator to ensure user owns the comment they're trying to access."""
    @wraps(f)
    def decorated_function(comment_id, *args, **kwargs):
        if not g.current_user:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        
        comment = Comment.query.get_or_404(comment_id)
        
        if comment.user_id != g.current_user.id:
            # Log unauthorized access attempt
            security_logger = logging.getLogger('security')
            security_logger.warning(
                "Unauthorized comment access attempt",
                extra={
                    'event_type': 'unauthorized_access',
                    'resource_type': 'comment',
                    'resource_id': comment_id,
                    'user_id': g.current_user.id,
                    'owner_id': comment.user_id,
                    'attempted_action': f.__name__
                }
            )
            abort(403)  # Forbidden
        
        return f(comment_id, *args, **kwargs)
    return decorated_function