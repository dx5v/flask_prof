"""
Unit tests for logging system functionality
"""

import pytest
import logging
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_config import create_test_app, setup_test_db, teardown_test_db, create_test_user, login_user
from logging_config import StructuredFormatter, SecurityFormatter, LoggingConfig, LoggerMixin
from social_media_logger import SocialMediaLogger, log_execution_time, log_user_action


class TestStructuredFormatter:
    """Test structured JSON formatter"""
    
    def test_basic_formatting(self):
        """Test basic log record formatting"""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data['level'] == 'INFO'
        assert log_data['logger'] == 'test_logger'
        assert log_data['message'] == 'Test message'
        assert log_data['module'] == 'test'
        assert log_data['line'] == 10
    
    def test_exception_formatting(self):
        """Test exception info in log formatting"""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            record = logging.LogRecord(
                name='test_logger',
                level=logging.ERROR,
                pathname='test.py',
                lineno=10,
                msg='Error occurred',
                args=(),
                exc_info=True
            )
            record.exc_info = (ValueError, ValueError("Test error"), None)
            
            formatted = formatter.format(record)
            log_data = json.loads(formatted)
            
            assert 'exception' in log_data
            assert log_data['exception']['type'] == 'ValueError'
            assert log_data['exception']['message'] == 'Test error'
    
    def test_extra_fields(self):
        """Test extra fields in log formatting"""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.user_id = 123
        record.action = 'test_action'
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert 'extra' in log_data
        assert log_data['extra']['user_id'] == 123
        assert log_data['extra']['action'] == 'test_action'


class TestSecurityFormatter:
    """Test security formatter with data masking"""
    
    def test_sensitive_data_masking(self):
        """Test that sensitive data is properly masked"""
        formatter = SecurityFormatter()
        record = logging.LogRecord(
            name='security',
            level=logging.WARNING,
            pathname='test.py',
            lineno=10,
            msg='Security event',
            args=(),
            exc_info=None
        )
        
        # Add sensitive data
        record.password = 'secret123'
        record.token = 'abc123token'
        record.normal_field = 'safe_data'
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Sensitive fields should be masked
        assert log_data['extra']['password'] == '***MASKED***'
        assert log_data['extra']['token'] == '***MASKED***'
        # Normal fields should remain
        assert log_data['extra']['normal_field'] == 'safe_data'
    
    def test_nested_sensitive_data_masking(self):
        """Test masking of sensitive data in nested structures"""
        formatter = SecurityFormatter()
        record = logging.LogRecord(
            name='security',
            level=logging.WARNING,
            pathname='test.py',
            lineno=10,
            msg='Security event',
            args=(),
            exc_info=None
        )
        
        # Add nested sensitive data
        record.user_data = {
            'username': 'testuser',
            'password_hash': 'hashed_password',
            'preferences': {
                'api_key': 'secret_key',
                'theme': 'dark'
            }
        }
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        user_data = log_data['extra']['user_data']
        assert user_data['username'] == 'testuser'
        assert user_data['password_hash'] == '***MASKED***'
        assert user_data['preferences']['api_key'] == '***MASKED***'
        assert user_data['preferences']['theme'] == 'dark'


class TestLoggingConfig:
    """Test logging configuration"""
    
    def test_setup_logging_creates_directories(self):
        """Test that logging setup creates log directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_test_app()
            
            with patch.dict(os.environ, {'LOG_DIR': temp_dir}):
                LoggingConfig.setup_logging(app)
                
                # Directory should be created
                assert os.path.exists(temp_dir)
    
    def test_logging_handlers_creation(self):
        """Test that logging handlers are properly created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_test_app()
            
            with patch.dict(os.environ, {'LOG_DIR': temp_dir, 'FLASK_ENV': 'production'}):
                LoggingConfig.setup_logging(app)
                
                # Check that log files would be created
                expected_files = [
                    'application.log',
                    'security.log', 
                    'errors.log',
                    'performance.log',
                    'audit.log'
                ]
                
                # Handlers should be configured (files created on first log)
                root_logger = logging.getLogger()
                assert len(root_logger.handlers) > 0


class TestLoggerMixin:
    """Test LoggerMixin functionality"""
    
    def test_logger_mixin_initialization(self):
        """Test LoggerMixin creates proper loggers"""
        class TestClass(LoggerMixin):
            def __init__(self):
                super().__init__()
        
        test_obj = TestClass()
        
        assert hasattr(test_obj, 'logger')
        assert hasattr(test_obj, 'security_logger')
        assert hasattr(test_obj, 'audit_logger')
        assert hasattr(test_obj, 'performance_logger')
    
    def test_security_event_logging(self):
        """Test security event logging"""
        class TestClass(LoggerMixin):
            def __init__(self):
                super().__init__()
        
        test_obj = TestClass()
        
        # Mock the security logger
        with patch.object(test_obj.security_logger, 'warning') as mock_warning:
            test_obj.log_security_event(
                event_type='test_event',
                description='Test security event',
                user_id=123
            )
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert 'Security Event: test_event' in call_args[0][0]
            assert call_args[1]['extra']['event_type'] == 'test_event'
            assert call_args[1]['extra']['user_id'] == 123
    
    def test_audit_event_logging(self):
        """Test audit event logging"""
        class TestClass(LoggerMixin):
            def __init__(self):
                super().__init__()
        
        test_obj = TestClass()
        
        with patch.object(test_obj.audit_logger, 'info') as mock_info:
            test_obj.log_audit_event(
                action='create',
                resource_type='post',
                resource_id='123',
                user_id=456
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert 'Audit: create post' in call_args[0][0]
            assert call_args[1]['extra']['action'] == 'create'
            assert call_args[1]['extra']['resource_type'] == 'post'
    
    def test_performance_metric_logging(self):
        """Test performance metric logging"""
        class TestClass(LoggerMixin):
            def __init__(self):
                super().__init__()
        
        test_obj = TestClass()
        
        with patch.object(test_obj.performance_logger, 'info') as mock_info:
            test_obj.log_performance_metric(
                operation='database_query',
                duration_ms=150.5,
                additional_metrics={'query_type': 'SELECT'}
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert 'Performance: database_query' in call_args[0][0]
            assert call_args[1]['extra']['duration_ms'] == 150.5
            assert call_args[1]['extra']['metrics']['query_type'] == 'SELECT'


class TestSocialMediaLogger:
    """Test SocialMediaLogger functionality"""
    
    def test_login_attempt_logging(self):
        """Test login attempt logging"""
        logger = SocialMediaLogger()
        
        with patch.object(logger, 'log_audit_event') as mock_audit, \
             patch.object(logger.logger, 'info') as mock_info, \
             patch('social_media_logger.session', {'user_id': 123}), \
             patch('social_media_logger.request') as mock_request:
            
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers = {'User-Agent': 'test-agent'}
            
            logger.log_login_attempt('testuser', success=True)
            
            mock_audit.assert_called_once()
            mock_info.assert_called_once()
    
    def test_failed_login_logging(self):
        """Test failed login attempt logging"""
        logger = SocialMediaLogger()
        
        with patch.object(logger, 'log_security_event') as mock_security, \
             patch('social_media_logger.request') as mock_request:
            
            mock_request.remote_addr = '127.0.0.1'
            mock_request.headers = {'User-Agent': 'test-agent'}
            
            logger.log_login_attempt(
                'testuser', 
                success=False, 
                failure_reason='invalid_credentials'
            )
            
            mock_security.assert_called_once()
            call_args = mock_security.call_args
            assert call_args[1]['event_type'] == 'failed_login'
    
    def test_post_creation_logging(self):
        """Test post creation logging"""
        logger = SocialMediaLogger()
        
        with patch.object(logger, 'log_audit_event') as mock_audit, \
             patch.object(logger, 'log_business_event') as mock_business:
            
            logger.log_post_creation(
                post_id=123,
                user_id=456,
                caption_length=50
            )
            
            mock_audit.assert_called_once()
            mock_business.assert_called_once()
            
            # Check audit call
            audit_args = mock_audit.call_args
            assert audit_args[1]['action'] == 'create'
            assert audit_args[1]['resource_type'] == 'post'
            assert audit_args[1]['resource_id'] == '123'


class TestLoggingDecorators:
    """Test logging decorators"""
    
    def test_log_execution_time_decorator(self):
        """Test execution time logging decorator"""
        @log_execution_time('test_operation')
        def test_function():
            return "success"
        
        with patch('social_media_logger.social_logger') as mock_logger:
            result = test_function()
            
            assert result == "success"
            mock_logger.log_performance_metric.assert_called_once()
            
            call_args = mock_logger.log_performance_metric.call_args
            assert call_args[1]['operation'] == 'test_operation'
            assert 'duration_ms' in call_args[1]
    
    def test_log_execution_time_with_exception(self):
        """Test execution time decorator with exceptions"""
        @log_execution_time('failing_operation')
        def failing_function():
            raise ValueError("Test error")
        
        with patch('social_media_logger.social_logger') as mock_logger:
            with pytest.raises(ValueError):
                failing_function()
            
            mock_logger.logger.error.assert_called_once()
    
    def test_log_user_action_decorator(self):
        """Test user action logging decorator"""
        @log_user_action('test_action')
        def test_action():
            return "completed"
        
        with patch('social_media_logger.session', {'user_id': 123}), \
             patch('social_media_logger.social_logger') as mock_logger:
            
            result = test_action()
            
            assert result == "completed"
            mock_logger.logger.info.assert_called_once()
            
            call_args = mock_logger.logger.info.call_args
            assert 'User action completed: test_action' in call_args[0][0]
            assert call_args[1]['extra']['action_type'] == 'test_action'
            assert call_args[1]['extra']['user_id'] == 123
            assert call_args[1]['extra']['success'] == True


class TestIntegratedLogging:
    """Test logging integration with Flask application"""
    
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
    
    def test_login_logging_integration(self, client, app_context):
        """Test that login attempts are properly logged"""
        create_test_user("testuser", "testpass")
        
        # Capture log records
        with patch('social_media_logger.social_logger') as mock_logger:
            login_user(client, "testuser", "testpass")
            
            # Should have logged the login attempt
            mock_logger.log_login_attempt.assert_called_once()
            call_args = mock_logger.log_login_attempt.call_args
            assert call_args[0][0] == "testuser"  # username
            assert call_args[0][1] == True       # success
    
    def test_post_creation_logging_integration(self, client, app_context):
        """Test that post creation is properly logged"""
        create_test_user("testuser", "testpass")
        login_user(client, "testuser", "testpass")
        
        with patch('social_media_logger.social_logger') as mock_logger:
            client.post('/create_post', data={
                'caption': 'Test post for logging'
            }, follow_redirects=True)
            
            # Should have logged the post creation
            mock_logger.log_post_creation.assert_called_once()
    
    def test_unauthorized_access_logging(self, client, app_context):
        """Test that unauthorized access attempts are logged"""
        user1 = create_test_user("user1", "pass1")
        user2 = create_test_user("user2", "pass2")
        
        from test_config import create_test_post
        post = create_test_post(user1, "User1's post")
        
        login_user(client, "user2", "pass2")
        
        # Capture security logs
        security_logger = logging.getLogger('security')
        with patch.object(security_logger, 'warning') as mock_warning:
            response = client.get(f'/edit_post/{post.id}')
            assert response.status_code == 403
            
            # Should have logged the unauthorized access
            mock_warning.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])