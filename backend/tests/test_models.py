"""
Unit tests for database models
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_config import create_test_app, setup_test_db, teardown_test_db
from models import db, User, Post, Like, Comment


class TestUser:
    """Test cases for User model"""
    
    @pytest.fixture
    def app(self):
        app = create_test_app()
        setup_test_db(app)
        yield app
        teardown_test_db(app)
    
    @pytest.fixture
    def app_context(self, app):
        with app.app_context():
            yield app
    
    def test_user_creation(self, app_context):
        """Test basic user creation"""
        user = User(username="testuser")
        user.set_password("testpass")
        
        assert user.username == "testuser"
        assert user.password_hash is not None
        assert user.password_hash != "testpass"  # Should be hashed
    
    def test_password_hashing(self, app_context):
        """Test password hashing and verification"""
        user = User(username="testuser")
        user.set_password("mypassword")
        
        # Password should be hashed
        assert user.password_hash != "mypassword"
        
        # Check password should work
        assert user.check_password("mypassword") == True
        assert user.check_password("wrongpassword") == False
    
    def test_user_to_dict(self, app_context):
        """Test user serialization"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        user_dict = user.to_dict()
        assert user_dict['username'] == "testuser"
        assert user_dict['id'] == user.id
        assert 'password_hash' not in user_dict  # Should not expose password
    
    def test_follow_functionality(self, app_context):
        """Test user follow/unfollow functionality"""
        user1 = User(username="user1")
        user2 = User(username="user2")
        user1.set_password("pass1")
        user2.set_password("pass2")
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        # Initially not following
        assert user1.is_following(user2) == False
        assert user2.is_following(user1) == False
        
        # Follow user2
        user1.follow(user2)
        db.session.commit()
        
        assert user1.is_following(user2) == True
        assert user2.is_following(user1) == False  # Not mutual
        
        # Unfollow user2
        user1.unfollow(user2)
        db.session.commit()
        
        assert user1.is_following(user2) == False
    
    def test_follow_self_prevention(self, app_context):
        """Test that users cannot follow themselves"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        # Attempt to follow self
        user.follow(user)
        db.session.commit()
        
        # Should not be following self
        assert user.is_following(user) == False


class TestPost:
    """Test cases for Post model"""
    
    @pytest.fixture
    def app(self):
        app = create_test_app()
        setup_test_db(app)
        yield app
        teardown_test_db(app)
    
    @pytest.fixture
    def app_context(self, app):
        with app.app_context():
            yield app
    
    def test_post_creation(self, app_context):
        """Test basic post creation"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        post = Post(caption="Test post", user_id=user.id)
        db.session.add(post)
        db.session.commit()
        
        assert post.caption == "Test post"
        assert post.user_id == user.id
        assert post.author.username == "testuser"
        assert isinstance(post.timestamp, datetime)
    
    def test_post_to_dict(self, app_context):
        """Test post serialization"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        post = Post(caption="Test post", user_id=user.id)
        db.session.add(post)
        db.session.commit()
        
        post_dict = post.to_dict()
        assert post_dict['caption'] == "Test post"
        assert post_dict['user_id'] == user.id
        assert post_dict['author'] == "testuser"
        assert post_dict['likes_count'] == 0
        assert post_dict['comments_count'] == 0
    
    def test_post_cascade_delete(self, app_context):
        """Test that deleting a user deletes their posts"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        post = Post(caption="Test post", user_id=user.id)
        db.session.add(post)
        db.session.commit()
        
        post_id = post.id
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        # Post should also be deleted
        deleted_post = Post.query.get(post_id)
        assert deleted_post is None


class TestLike:
    """Test cases for Like model"""
    
    @pytest.fixture
    def app(self):
        app = create_test_app()
        setup_test_db(app)
        yield app
        teardown_test_db(app)
    
    @pytest.fixture
    def app_context(self, app):
        with app.app_context():
            yield app
    
    def test_like_creation(self, app_context):
        """Test basic like creation"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        post = Post(caption="Test post", user_id=user.id)
        db.session.add(post)
        db.session.commit()
        
        like = Like(user_id=user.id, post_id=post.id)
        db.session.add(like)
        db.session.commit()
        
        assert like.user_id == user.id
        assert like.post_id == post.id
        assert like.user.username == "testuser"
        assert like.post.caption == "Test post"
    
    def test_unique_user_post_like(self, app_context):
        """Test that a user can only like a post once"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        post = Post(caption="Test post", user_id=user.id)
        db.session.add(post)
        db.session.commit()
        
        # First like should work
        like1 = Like(user_id=user.id, post_id=post.id)
        db.session.add(like1)
        db.session.commit()
        
        # Second like should fail due to unique constraint
        like2 = Like(user_id=user.id, post_id=post.id)
        db.session.add(like2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db.session.commit()


class TestComment:
    """Test cases for Comment model"""
    
    @pytest.fixture
    def app(self):
        app = create_test_app()
        setup_test_db(app)
        yield app
        teardown_test_db(app)
    
    @pytest.fixture
    def app_context(self, app):
        with app.app_context():
            yield app
    
    def test_comment_creation(self, app_context):
        """Test basic comment creation"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        post = Post(caption="Test post", user_id=user.id)
        db.session.add(post)
        db.session.commit()
        
        comment = Comment(text="Test comment", user_id=user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        
        assert comment.text == "Test comment"
        assert comment.user_id == user.id
        assert comment.post_id == post.id
        assert comment.author.username == "testuser"
        assert isinstance(comment.timestamp, datetime)
    
    def test_comment_to_dict(self, app_context):
        """Test comment serialization"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        post = Post(caption="Test post", user_id=user.id)
        db.session.add(post)
        db.session.commit()
        
        comment = Comment(text="Test comment", user_id=user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        
        comment_dict = comment.to_dict()
        assert comment_dict['text'] == "Test comment"
        assert comment_dict['user_id'] == user.id
        assert comment_dict['post_id'] == post.id
        assert comment_dict['author'] == "testuser"
    
    def test_comment_cascade_delete(self, app_context):
        """Test that deleting a post deletes its comments"""
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        
        post = Post(caption="Test post", user_id=user.id)
        db.session.add(post)
        db.session.commit()
        
        comment = Comment(text="Test comment", user_id=user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        
        comment_id = comment.id
        
        # Delete post
        db.session.delete(post)
        db.session.commit()
        
        # Comment should also be deleted
        deleted_comment = Comment.query.get(comment_id)
        assert deleted_comment is None


if __name__ == '__main__':
    pytest.main([__file__])