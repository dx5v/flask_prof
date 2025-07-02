"""
Unit tests for Flask application routes and endpoints
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
from models import db, Post, Like, Comment


class TestRoutes:
    """Base test class for route testing"""
    
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


class TestHomeRoute(TestRoutes):
    """Test home page functionality"""
    
    def test_home_requires_login(self, client):
        """Test that home page requires authentication"""
        response = client.get('/home', follow_redirects=True)
        assert b'Login' in response.data
    
    def test_home_displays_posts(self, client, app_context):
        """Test that home page displays posts from followed users"""
        # Create users
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        # User1 creates posts
        post1 = create_test_post(user1, "User1's first post")
        post2 = create_test_post(user1, "User1's second post")
        
        # User2 follows user1
        user2.follow(user1)
        db.session.commit()
        
        # Login as user2 and check home page
        login_user(client, "user2", "pass2")
        response = client.get('/home')
        
        assert response.status_code == 200
        assert b"User1's first post" in response.data
        assert b"User1's second post" in response.data
    
    def test_home_shows_own_posts(self, client, app_context):
        """Test that home page shows user's own posts"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "My own post")
        
        login_user(client, "testuser", "testpass")
        response = client.get('/home')
        
        assert response.status_code == 200
        assert b"My own post" in response.data
    
    def test_home_shows_suggested_users(self, client, app_context):
        """Test that home page shows suggested users to follow"""
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        user3 = create_test_user("user3", "pass3")
        
        login_user(client, "user1", "pass1")
        response = client.get('/home')
        
        assert response.status_code == 200
        # Should show other users as suggestions
        assert b"user2" in response.data or b"user3" in response.data


class TestPostRoutes(TestRoutes):
    """Test post-related routes"""
    
    def test_create_post(self, client, app_context):
        """Test post creation"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        response = client.post('/create_post', data={
            'caption': 'New test post'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Post created!' in response.data
        
        # Verify post was created in database
        post = Post.query.filter_by(caption='New test post').first()
        assert post is not None
        assert post.user_id == user.id
    
    def test_create_empty_post(self, client, app_context):
        """Test that empty posts are not created"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        initial_count = Post.query.count()
        
        # Try to create post with empty caption
        response = client.post('/create_post', data={
            'caption': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # No new post should be created
        assert Post.query.count() == initial_count
    
    def test_create_post_requires_login(self, client, app_context):
        """Test that post creation requires login"""
        response = client.post('/create_post', data={
            'caption': 'Unauthorized post'
        }, follow_redirects=True)
        
        assert b'Login' in response.data
        # No post should be created
        assert Post.query.count() == 0


class TestLikeRoutes(TestRoutes):
    """Test like/unlike functionality"""
    
    def test_toggle_like_adds_like(self, client, app_context):
        """Test that toggling like adds a like"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        
        login_user(client, "testuser", "testpass")
        
        # Initially no likes
        assert Like.query.filter_by(user_id=user.id, post_id=post.id).first() is None
        
        # Toggle like
        response = client.get(f'/toggle_like/{post.id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Should now have a like
        like = Like.query.filter_by(user_id=user.id, post_id=post.id).first()
        assert like is not None
    
    def test_toggle_like_removes_like(self, client, app_context):
        """Test that toggling like removes existing like"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        
        # Create initial like
        like = Like(user_id=user.id, post_id=post.id)
        db.session.add(like)
        db.session.commit()
        
        login_user(client, "testuser", "testpass")
        
        # Toggle like (should remove it)
        response = client.get(f'/toggle_like/{post.id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Like should be removed
        like = Like.query.filter_by(user_id=user.id, post_id=post.id).first()
        assert like is None
    
    def test_toggle_like_requires_login(self, client, app_context):
        """Test that liking requires login"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        
        response = client.get(f'/toggle_like/{post.id}', follow_redirects=True)
        assert b'Login' in response.data


class TestCommentRoutes(TestRoutes):
    """Test comment functionality"""
    
    def test_add_comment(self, client, app_context):
        """Test adding a comment to a post"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        
        login_user(client, "testuser", "testpass")
        
        response = client.post(f'/add_comment/{post.id}', data={
            'text': 'Test comment'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Comment added!' in response.data
        
        # Verify comment was created
        comment = Comment.query.filter_by(text='Test comment').first()
        assert comment is not None
        assert comment.user_id == user.id
        assert comment.post_id == post.id
    
    def test_add_empty_comment(self, client, app_context):
        """Test that empty comments are not added"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        
        login_user(client, "testuser", "testpass")
        
        initial_count = Comment.query.count()
        
        # Try to add empty comment
        response = client.post(f'/add_comment/{post.id}', data={
            'text': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # No new comment should be created
        assert Comment.query.count() == initial_count
    
    def test_add_comment_requires_login(self, client, app_context):
        """Test that adding comments requires login"""
        user = create_test_user("testuser", "testpass")
        post = create_test_post(user, "Test post")
        
        response = client.post(f'/add_comment/{post.id}', data={
            'text': 'Unauthorized comment'
        }, follow_redirects=True)
        
        assert b'Login' in response.data
        # No comment should be created
        assert Comment.query.count() == 0


class TestFollowRoutes(TestRoutes):
    """Test follow/unfollow functionality"""
    
    def test_follow_user(self, client, app_context):
        """Test following another user"""
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        login_user(client, "user1", "pass1")
        
        # Initially not following
        assert not user1.is_following(user2)
        
        # Follow user2
        response = client.get(f'/follow/{user2.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'You are now following user2' in response.data
        
        # Refresh user1 from database
        db.session.refresh(user1)
        assert user1.is_following(user2)
    
    def test_unfollow_user(self, client, app_context):
        """Test unfollowing a user"""
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        # Set up initial follow relationship
        user1.follow(user2)
        db.session.commit()
        
        login_user(client, "user1", "pass1")
        
        # Unfollow user2
        response = client.get(f'/unfollow/{user2.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'You unfollowed user2' in response.data
        
        # Refresh user1 from database
        db.session.refresh(user1)
        assert not user1.is_following(user2)
    
    def test_follow_self_prevention(self, client, app_context):
        """Test that users cannot follow themselves"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        response = client.get(f'/follow/{user.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'You cannot follow yourself' in response.data
        
        # Should not be following self
        db.session.refresh(user)
        assert not user.is_following(user)
    
    def test_follow_requires_login(self, client, app_context):
        """Test that following requires login"""
        user = create_test_user("testuser", "testpass")
        
        response = client.get(f'/follow/{user.id}', follow_redirects=True)
        assert b'Login' in response.data
    
    def test_follow_nonexistent_user(self, client, app_context):
        """Test following non-existent user returns 404"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        response = client.get('/follow/99999')
        assert response.status_code == 404


class TestIndexRoute(TestRoutes):
    """Test index/root route behavior"""
    
    def test_index_redirects_unauthenticated_to_login(self, client):
        """Test that index redirects unauthenticated users to login"""
        response = client.get('/', follow_redirects=True)
        assert b'Login' in response.data
    
    def test_index_redirects_authenticated_to_home(self, client, app_context):
        """Test that index redirects authenticated users to home"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        # Should be on home page (might contain posts, navigation, etc.)
        # Since we're logged in, we shouldn't see the login form
        assert b'Login' not in response.data or b'logout' in response.data.lower()


class TestErrorHandling(TestRoutes):
    """Test error handling in routes"""
    
    def test_404_on_nonexistent_post(self, client, app_context):
        """Test 404 error for non-existent posts"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        response = client.get('/edit_post/99999')
        assert response.status_code == 404
    
    def test_404_on_nonexistent_comment(self, client, app_context):
        """Test 404 error for non-existent comments"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        response = client.get('/edit_comment/99999')
        assert response.status_code == 404
    
    def test_404_on_invalid_like_post(self, client, app_context):
        """Test 404 error when trying to like non-existent post"""
        user = create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        response = client.get('/toggle_like/99999')
        assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__])