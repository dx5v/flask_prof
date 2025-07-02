"""
Unit tests for authorization decorators and ownership checks
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_config import (
    create_test_app, setup_test_db, teardown_test_db, 
    create_test_user, create_test_post, create_test_comment, login_user
)
from models import db


class TestAuthorizationDecorators:
    """Test cases for authorization decorators"""
    
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


class TestPostOwnership(TestAuthorizationDecorators):
    """Test post ownership authorization"""
    
    def test_edit_own_post_allowed(self, client, app_context):
        """Test that users can edit their own posts"""
        # Create user and post
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Original caption")
        
        # Login and try to edit own post
        login_user(client, "testuser", "testpass")
        
        response = client.get(f'/edit_post/{post.id}')
        assert response.status_code == 200
        assert b'Original caption' in response.data
        
        # Submit edit
        response = client.post(f'/edit_post/{post.id}', data={
            'caption': 'Updated caption'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Post updated successfully!' in response.data
    
    def test_edit_other_user_post_denied(self, client, app_context):
        """Test that users cannot edit other users' posts"""
        # Create two users
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        # User1 creates a post
        post = create_test_post(user1, "User1's post")
        
        # User2 tries to edit user1's post
        login_user(client, "user2", "pass2")
        
        response = client.get(f'/edit_post/{post.id}')
        assert response.status_code == 403  # Forbidden
        
        response = client.post(f'/edit_post/{post.id}', data={
            'caption': 'Hacked caption'
        })
        assert response.status_code == 403  # Forbidden
    
    def test_delete_own_post_allowed(self, client, app_context):
        """Test that users can delete their own posts"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "My post to delete")
        
        login_user(client, "testuser", "testpass")
        
        response = client.post(f'/delete_post/{post.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'Post deleted successfully!' in response.data
    
    def test_delete_other_user_post_denied(self, client, app_context):
        """Test that users cannot delete other users' posts"""
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        post = create_test_post(user1, "User1's post")
        
        login_user(client, "user2", "pass2")
        
        response = client.post(f'/delete_post/{post.id}')
        assert response.status_code == 403  # Forbidden
    
    def test_post_access_without_login(self, client, app_context):
        """Test post operations require login"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        
        # Try to edit without login
        response = client.get(f'/edit_post/{post.id}', follow_redirects=True)
        assert b'Please login' in response.data or b'Login' in response.data
        
        # Try to delete without login
        response = client.post(f'/delete_post/{post.id}', follow_redirects=True)
        assert b'Please login' in response.data or b'Login' in response.data
    
    def test_nonexistent_post_returns_404(self, client, app_context):
        """Test accessing non-existent post returns 404"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        # Try to edit non-existent post
        response = client.get('/edit_post/99999')
        assert response.status_code == 404
        
        # Try to delete non-existent post
        response = client.post('/delete_post/99999')
        assert response.status_code == 404


class TestCommentOwnership(TestAuthorizationDecorators):
    """Test comment ownership authorization"""
    
    def test_edit_own_comment_allowed(self, client, app_context):
        """Test that users can edit their own comments"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        comment = create_test_comment(user, post, "Original comment")
        
        login_user(client, "testuser", "testpass")
        
        response = client.get(f'/edit_comment/{comment.id}')
        assert response.status_code == 200
        assert b'Original comment' in response.data
        
        # Submit edit
        response = client.post(f'/edit_comment/{comment.id}', data={
            'text': 'Updated comment'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Comment updated successfully!' in response.data
    
    def test_edit_other_user_comment_denied(self, client, app_context):
        """Test that users cannot edit other users' comments"""
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        post = create_test_post(user1, "Test post")
        comment = create_test_comment(user1, post, "User1's comment")
        
        # User2 tries to edit user1's comment
        login_user(client, "user2", "pass2")
        
        response = client.get(f'/edit_comment/{comment.id}')
        assert response.status_code == 403  # Forbidden
        
        response = client.post(f'/edit_comment/{comment.id}', data={
            'text': 'Hacked comment'
        })
        assert response.status_code == 403  # Forbidden
    
    def test_delete_own_comment_allowed(self, client, app_context):
        """Test that users can delete their own comments"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        comment = create_test_comment(user, post, "My comment to delete")
        
        login_user(client, "testuser", "testpass")
        
        response = client.post(f'/delete_comment/{comment.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'Comment deleted successfully!' in response.data
    
    def test_delete_other_user_comment_denied(self, client, app_context):
        """Test that users cannot delete other users' comments"""
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        post = create_test_post(user1, "Test post")
        comment = create_test_comment(user1, post, "User1's comment")
        
        login_user(client, "user2", "pass2")
        
        response = client.post(f'/delete_comment/{comment.id}')
        assert response.status_code == 403  # Forbidden
    
    def test_comment_access_without_login(self, client, app_context):
        """Test comment operations require login"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        comment = create_test_comment(user, post, "Test comment")
        
        # Try to edit without login
        response = client.get(f'/edit_comment/{comment.id}', follow_redirects=True)
        assert b'Please login' in response.data or b'Login' in response.data
        
        # Try to delete without login
        response = client.post(f'/delete_comment/{comment.id}', follow_redirects=True)
        assert b'Please login' in response.data or b'Login' in response.data
    
    def test_nonexistent_comment_returns_404(self, client, app_context):
        """Test accessing non-existent comment returns 404"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        # Try to edit non-existent comment
        response = client.get('/edit_comment/99999')
        assert response.status_code == 404
        
        # Try to delete non-existent comment
        response = client.post('/delete_comment/99999')
        assert response.status_code == 404


class TestCrossOwnershipScenarios(TestAuthorizationDecorators):
    """Test complex ownership scenarios"""
    
    def test_comment_on_other_user_post(self, client, app_context):
        """Test commenting on another user's post but only being able to edit own comment"""
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        # User1 creates a post
        post = create_test_post(user1, "User1's post")
        
        # User2 comments on user1's post
        login_user(client, "user2", "pass2")
        response = client.post(f'/add_comment/{post.id}', data={
            'text': 'User2 comment on user1 post'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Find the comment that was just created
        from models import Comment
        comment = Comment.query.filter_by(user_id=user2.id, post_id=post.id).first()
        assert comment is not None
        
        # User2 should be able to edit their own comment
        response = client.get(f'/edit_comment/{comment.id}')
        assert response.status_code == 200
        
        # User1 should NOT be able to edit user2's comment
        login_user(client, "user1", "pass1")
        response = client.get(f'/edit_comment/{comment.id}')
        assert response.status_code == 403
    
    def test_authorization_logging(self, client, app_context):
        """Test that unauthorized access attempts are logged"""
        import logging
        
        # Setup a test log handler to capture log messages
        test_handler = logging.Handler()
        test_handler.logs = []
        
        def emit(record):
            test_handler.logs.append(record)
        
        test_handler.emit = emit
        
        security_logger = logging.getLogger('security')
        security_logger.addHandler(test_handler)
        security_logger.setLevel(logging.WARNING)
        
        # Create users and content
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        post = create_test_post(user1, "User1's post")
        
        # User2 tries to access user1's post
        login_user(client, "user2", "pass2")
        response = client.get(f'/edit_post/{post.id}')
        assert response.status_code == 403
        
        # Check if security event was logged
        security_logs = [log for log in test_handler.logs if 'Unauthorized' in log.getMessage()]
        assert len(security_logs) > 0
        
        # Cleanup
        security_logger.removeHandler(test_handler)


if __name__ == '__main__':
    pytest.main([__file__])