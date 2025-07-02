"""
Social Media Application Logger
Specialized logging for social media business operations
"""

import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional, Callable
from flask import request, session, g
from logging_config import LoggerMixin


class SocialMediaLogger(LoggerMixin):
    """
    Specialized logger for social media application operations
    """
    
    def __init__(self):
        super().__init__()
    
    # ==================== AUTHENTICATION EVENTS ====================
    
    def log_login_attempt(self, username: str, success: bool, 
                         failure_reason: Optional[str] = None) -> None:
        """Log user login attempts"""
        event_type = "login_success" if success else "login_failure"
        
        if success:
            self.log_audit_event(
                action="login",
                resource_type="user_session",
                user_id=session.get('user_id'),
                changes={'status': 'logged_in'}
            )
            self.logger.info(
                f"User login successful: {username}",
                extra={
                    'event_type': event_type,
                    'username': username,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            )
        else:
            self.log_security_event(
                event_type="failed_login",
                description=f"Failed login attempt for username: {username}",
                additional_data={
                    'username': username,
                    'failure_reason': failure_reason,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            )
    
    def log_logout(self, user_id: int, username: str) -> None:
        """Log user logout"""
        self.log_audit_event(
            action="logout",
            resource_type="user_session",
            user_id=user_id,
            changes={'status': 'logged_out'}
        )
        self.logger.info(
            f"User logout: {username}",
            extra={
                'event_type': 'logout',
                'user_id': user_id,
                'username': username
            }
        )
    
    def log_registration(self, username: str, user_id: int) -> None:
        """Log new user registration"""
        self.log_audit_event(
            action="create",
            resource_type="user",
            resource_id=str(user_id),
            changes={'username': username, 'status': 'registered'}
        )
        self.log_business_event(
            event="user_registered",
            details={
                'user_id': user_id,
                'username': username,
                'registration_ip': request.remote_addr
            }
        )
    
    # ==================== POST OPERATIONS ====================
    
    def log_post_creation(self, post_id: int, user_id: int, caption_length: int) -> None:
        """Log post creation"""
        self.log_audit_event(
            action="create",
            resource_type="post",
            resource_id=str(post_id),
            user_id=user_id,
            changes={'caption_length': caption_length}
        )
        self.log_business_event(
            event="post_created",
            details={
                'post_id': post_id,
                'user_id': user_id,
                'caption_length': caption_length
            }
        )
    
    def log_post_edit(self, post_id: int, user_id: int, 
                     old_caption: str, new_caption: str) -> None:
        """Log post editing"""
        self.log_audit_event(
            action="update",
            resource_type="post",
            resource_id=str(post_id),
            user_id=user_id,
            changes={
                'old_caption_length': len(old_caption),
                'new_caption_length': len(new_caption),
                'modified_at': datetime.now(timezone.utc).isoformat()
            }
        )
        self.log_business_event(
            event="post_edited",
            details={
                'post_id': post_id,
                'user_id': user_id,
                'caption_changed': old_caption != new_caption
            }
        )
    
    def log_post_deletion(self, post_id: int, user_id: int, 
                         likes_count: int, comments_count: int) -> None:
        """Log post deletion"""
        self.log_audit_event(
            action="delete",
            resource_type="post",
            resource_id=str(post_id),
            user_id=user_id,
            changes={
                'likes_count': likes_count,
                'comments_count': comments_count,
                'deleted_at': datetime.now(timezone.utc).isoformat()
            }
        )
        self.log_business_event(
            event="post_deleted",
            details={
                'post_id': post_id,
                'user_id': user_id,
                'engagement_lost': {
                    'likes': likes_count,
                    'comments': comments_count
                }
            }
        )
    
    # ==================== LIKE OPERATIONS ====================
    
    def log_like_action(self, post_id: int, user_id: int, action: str) -> None:
        """Log like/unlike actions"""
        self.log_audit_event(
            action=action,
            resource_type="like",
            resource_id=f"{user_id}_{post_id}",
            user_id=user_id,
            changes={'post_id': post_id, 'action': action}
        )
        self.log_business_event(
            event=f"post_{action}d",
            details={
                'post_id': post_id,
                'user_id': user_id,
                'engagement_type': 'like'
            }
        )
    
    # ==================== COMMENT OPERATIONS ====================
    
    def log_comment_creation(self, comment_id: int, post_id: int, 
                           user_id: int, text_length: int) -> None:
        """Log comment creation"""
        self.log_audit_event(
            action="create",
            resource_type="comment",
            resource_id=str(comment_id),
            user_id=user_id,
            changes={
                'post_id': post_id,
                'text_length': text_length
            }
        )
        self.log_business_event(
            event="comment_created",
            details={
                'comment_id': comment_id,
                'post_id': post_id,
                'user_id': user_id,
                'text_length': text_length,
                'engagement_type': 'comment'
            }
        )
    
    def log_comment_edit(self, comment_id: int, user_id: int, 
                        old_text: str, new_text: str) -> None:
        """Log comment editing"""
        self.log_audit_event(
            action="update",
            resource_type="comment",
            resource_id=str(comment_id),
            user_id=user_id,
            changes={
                'old_text_length': len(old_text),
                'new_text_length': len(new_text),
                'modified_at': datetime.now(timezone.utc).isoformat()
            }
        )
        self.log_business_event(
            event="comment_edited",
            details={
                'comment_id': comment_id,
                'user_id': user_id,
                'text_changed': old_text != new_text
            }
        )
    
    def log_comment_deletion(self, comment_id: int, post_id: int, user_id: int) -> None:
        """Log comment deletion"""
        self.log_audit_event(
            action="delete",
            resource_type="comment",
            resource_id=str(comment_id),
            user_id=user_id,
            changes={
                'post_id': post_id,
                'deleted_at': datetime.now(timezone.utc).isoformat()
            }
        )
        self.log_business_event(
            event="comment_deleted",
            details={
                'comment_id': comment_id,
                'post_id': post_id,
                'user_id': user_id
            }
        )
    
    # ==================== FOLLOW OPERATIONS ====================
    
    def log_follow_action(self, follower_id: int, followed_id: int, action: str) -> None:
        """Log follow/unfollow actions"""
        self.log_audit_event(
            action=action,
            resource_type="follow_relationship",
            resource_id=f"{follower_id}_{followed_id}",
            user_id=follower_id,
            changes={
                'followed_user_id': followed_id,
                'action': action
            }
        )
        self.log_business_event(
            event=f"user_{action}ed",
            details={
                'follower_id': follower_id,
                'followed_id': followed_id,
                'relationship_action': action
            }
        )
    
    # ==================== SECURITY EVENTS ====================
    
    def log_unauthorized_access(self, resource_type: str, resource_id: str,
                              attempted_action: str, user_id: Optional[int] = None) -> None:
        """Log unauthorized access attempts"""
        self.log_security_event(
            event_type="unauthorized_access",
            description=f"Unauthorized {attempted_action} attempt on {resource_type}",
            user_id=user_id,
            additional_data={
                'resource_type': resource_type,
                'resource_id': resource_id,
                'attempted_action': attempted_action,
                'endpoint': request.endpoint,
                'method': request.method
            }
        )
    
    def log_suspicious_activity(self, activity_type: str, description: str,
                              user_id: Optional[int] = None,
                              risk_score: Optional[int] = None) -> None:
        """Log suspicious user activity"""
        self.log_security_event(
            event_type="suspicious_activity",
            description=description,
            user_id=user_id,
            additional_data={
                'activity_type': activity_type,
                'risk_score': risk_score,
                'user_agent': request.headers.get('User-Agent', ''),
                'referer': request.headers.get('Referer', '')
            }
        )
    
    # ==================== PERFORMANCE MONITORING ====================
    
    def log_database_query(self, query_type: str, table: str, duration_ms: float,
                          record_count: Optional[int] = None) -> None:
        """Log database query performance"""
        self.log_performance_metric(
            operation=f"db_query_{query_type}",
            duration_ms=duration_ms,
            additional_metrics={
                'table': table,
                'query_type': query_type,
                'record_count': record_count
            }
        )
    
    def log_page_load(self, endpoint: str, duration_ms: float,
                     user_id: Optional[int] = None) -> None:
        """Log page load performance"""
        self.log_performance_metric(
            operation="page_load",
            duration_ms=duration_ms,
            additional_metrics={
                'endpoint': endpoint,
                'user_id': user_id,
                'method': request.method
            }
        )


# Singleton instance for global use
social_logger = SocialMediaLogger()


def log_execution_time(operation_name: str):
    """Decorator to log execution time of functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                social_logger.log_performance_metric(
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2)
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                social_logger.logger.error(
                    f"Function {operation_name} failed after {duration_ms:.2f}ms",
                    exc_info=True,
                    extra={
                        'operation': operation_name,
                        'duration_ms': round(duration_ms, 2),
                        'error_type': type(e).__name__
                    }
                )
                raise
        return wrapper
    return decorator


def log_user_action(action_type: str):
    """Decorator to automatically log user actions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            user_id = session.get('user_id')
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                social_logger.logger.info(
                    f"User action completed: {action_type}",
                    extra={
                        'action_type': action_type,
                        'user_id': user_id,
                        'duration_ms': round(duration_ms, 2),
                        'success': True
                    }
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                social_logger.logger.error(
                    f"User action failed: {action_type}",
                    exc_info=True,
                    extra={
                        'action_type': action_type,
                        'user_id': user_id,
                        'duration_ms': round(duration_ms, 2),
                        'success': False,
                        'error_type': type(e).__name__
                    }
                )
                raise
        return wrapper
    return decorator