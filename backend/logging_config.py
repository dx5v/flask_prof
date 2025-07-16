"""
Industrial-level logging configuration for Flask Social Media Application
"""

import logging
import logging.handlers
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from flask import request, g, session
import traceback


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging with consistent field format
    """
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process,
        }
        
        # Add correlation ID if available (only within app context)
        try:
            if hasattr(g, 'correlation_id'):
                log_entry['correlation_id'] = g.correlation_id
        except RuntimeError:
            # No application context, skip correlation ID
            pass
        
        # Add request context if available
        if request:
            try:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'endpoint': request.endpoint,
                }
                
                # Add user context if authenticated
                try:
                    if hasattr(g, 'current_user') and g.current_user:
                        log_entry['user'] = {
                            'id': g.current_user.id,
                            'username': g.current_user.username
                        }
                    elif 'user_id' in session:
                        log_entry['user'] = {'id': session['user_id']}
                except (RuntimeError, NameError):
                    # No application context for g object or session not available
                    pass
                    
            except RuntimeError:
                # Outside request context
                pass
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the log record
        if self.include_extra:
            extra_fields = {
                k: v for k, v in record.__dict__.items() 
                if k not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'lineno', 'funcName', 'created',
                    'msecs', 'relativeCreated', 'thread', 'threadName',
                    'processName', 'process', 'exc_info', 'exc_text', 'stack_info'
                }
            }
            if extra_fields:
                log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str)


class SecurityFormatter(StructuredFormatter):
    """
    Security-focused formatter that ensures sensitive data is masked
    """
    
    SENSITIVE_FIELDS = {
        'password', 'password_hash', 'token', 'secret', 'key', 'authorization',
        'cookie', 'session', 'csrf_token', 'api_key', 'access_token'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with sensitive data masking"""
        formatted = super().format(record)
        log_data = json.loads(formatted)
        
        # Mask sensitive data
        self._mask_sensitive_data(log_data)
        
        return json.dumps(log_data, default=str)
    
    def _mask_sensitive_data(self, data: Any) -> None:
        """Recursively mask sensitive data in log entries"""
        if isinstance(data, dict):
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    data[key] = "***MASKED***"
                else:
                    self._mask_sensitive_data(value)
        elif isinstance(data, list):
            for item in data:
                self._mask_sensitive_data(item)


class LoggingConfig:
    """
    Centralized logging configuration for the application
    """
    
    @staticmethod
    def setup_logging(app) -> None:
        """Setup application logging with multiple handlers"""
        
        # Get environment-specific configuration
        environment = os.getenv('FLASK_ENV', 'development')
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_dir = os.getenv('LOG_DIR', 'logs')
        
        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Console handler for development
        if environment == 'development':
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Application log handler (structured JSON)
        app_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'application.log'),
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(app_handler)
        
        # Security log handler
        security_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'security.log'),
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=20,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(SecurityFormatter())
        
        # Create security logger
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.WARNING)
        security_logger.propagate = False
        
        # Error log handler
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'errors.log'),
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=15,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)
        
        # Performance log handler
        performance_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'performance.log'),
            maxBytes=30 * 1024 * 1024,  # 30MB
            backupCount=5,
            encoding='utf-8'
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(StructuredFormatter())
        
        # Create performance logger
        performance_logger = logging.getLogger('performance')
        performance_logger.addHandler(performance_handler)
        performance_logger.setLevel(logging.INFO)
        performance_logger.propagate = False
        
        # Audit log handler (for compliance)
        audit_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'audit.log'),
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=50,  # Keep more audit logs
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(SecurityFormatter())
        
        # Create audit logger
        audit_logger = logging.getLogger('audit')
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False
        
        # Configure Flask and SQLAlchemy loggers
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        
        app.logger.info("Logging system initialized", extra={
            'environment': environment,
            'log_level': log_level,
            'log_directory': log_dir
        })


class LoggerMixin:
    """
    Mixin class to provide consistent logging methods across the application
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__)
        self.security_logger = logging.getLogger('security')
        self.audit_logger = logging.getLogger('audit')
        self.performance_logger = logging.getLogger('performance')
    
    def log_security_event(self, event_type: str, description: str, 
                          user_id: Optional[int] = None, 
                          ip_address: Optional[str] = None, 
                          additional_data: Optional[Dict[str, Any]] = None) -> None:
        """Log security-related events"""
        self.security_logger.warning(
            f"Security Event: {event_type}",
            extra={
                'event_type': event_type,
                'description': description,
                'user_id': user_id,
                'ip_address': ip_address or (request.remote_addr if request else None),
                'additional_data': additional_data or {}
            }
        )
    
    def log_audit_event(self, action: str, resource_type: str, 
                       resource_id: Optional[str] = None,
                       user_id: Optional[int] = None,
                       changes: Optional[Dict[str, Any]] = None) -> None:
        """Log audit trail events for compliance"""
        self.audit_logger.info(
            f"Audit: {action} {resource_type}",
            extra={
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'user_id': user_id,
                'changes': changes or {},
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    
    def log_performance_metric(self, operation: str, duration_ms: float,
                              additional_metrics: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics"""
        self.performance_logger.info(
            f"Performance: {operation}",
            extra={
                'operation': operation,
                'duration_ms': duration_ms,
                'metrics': additional_metrics or {}
            }
        )
    
    def log_business_event(self, event: str, details: Dict[str, Any]) -> None:
        """Log business logic events"""
        self.logger.info(
            f"Business Event: {event}",
            extra={
                'event_type': 'business',
                'event': event,
                'details': details
            }
        )


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking"""
    return str(uuid.uuid4())


def setup_request_logging(app):
    """Setup request-level logging with correlation IDs"""
    
    @app.before_request
    def before_request():
        """Setup request context and correlation ID"""
        g.correlation_id = generate_correlation_id()
        g.request_start_time = datetime.now(timezone.utc)
        
        # Log incoming request
        app.logger.info(
            "Request started",
            extra={
                'event_type': 'request_start',
                'method': request.method,
                'url': request.url,
                'correlation_id': g.correlation_id
            }
        )
    
    @app.after_request
    def after_request(response):
        """Log request completion"""
        if hasattr(g, 'request_start_time'):
            duration = (datetime.now(timezone.utc) - g.request_start_time).total_seconds() * 1000
            
            app.logger.info(
                "Request completed",
                extra={
                    'event_type': 'request_end',
                    'status_code': response.status_code,
                    'duration_ms': round(duration, 2),
                    'correlation_id': getattr(g, 'correlation_id', 'unknown')
                }
            )
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Log unhandled exceptions"""
        app.logger.error(
            f"Unhandled exception: {error}",
            exc_info=True,
            extra={
                'event_type': 'unhandled_exception',
                'error_type': type(error).__name__,
                'correlation_id': getattr(g, 'correlation_id', 'unknown')
            }
        )
        
        # Return a generic error response
        return "Internal Server Error", 500