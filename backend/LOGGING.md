# Industrial-Level Logging System Documentation

## Overview

This Flask social media application implements a comprehensive, industrial-grade logging system designed for production environments. The logging system provides security monitoring, audit trails, performance metrics, and comprehensive debugging capabilities.

## Architecture

### Log Types and Files

The logging system generates several specialized log files:

1. **`application.log`** - General application events and business logic
2. **`security.log`** - Security events, authentication, and unauthorized access
3. **`audit.log`** - Compliance audit trail for all user actions
4. **`performance.log`** - Performance metrics and timing information
5. **`errors.log`** - Error events and exceptions

### Log Format

All logs use structured JSON format for easy parsing and analysis:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "app_jinja",
  "message": "User login successful: john_doe",
  "correlation_id": "12345678-1234-1234-1234-123456789012",
  "user": {"id": 123, "username": "john_doe"},
  "request": {
    "method": "POST",
    "url": "http://localhost:5001/login",
    "remote_addr": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  },
  "event_type": "login_success"
}
```

## Configuration

### Environment Variables

Configure logging through environment variables:

```bash
# Logging Configuration
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs           # Directory for log files
FLASK_ENV=production   # development, staging, production

# Security Configuration
MAX_LOGIN_ATTEMPTS=5
LOGIN_ATTEMPT_WINDOW=300

# Performance Configuration
ENABLE_PERFORMANCE_LOGGING=true
SLOW_QUERY_THRESHOLD=1000
```

### Log Rotation

- **Application logs**: 50MB max size, 10 backups
- **Security logs**: 100MB max size, 20 backups  
- **Audit logs**: 100MB max size, 50 backups (long retention)
- **Performance logs**: 30MB max size, 5 backups
- **Error logs**: 50MB max size, 15 backups

## Event Types

### Security Events

**Authentication Events:**
- `login_success` - Successful user login
- `login_failure` - Failed login attempt
- `logout` - User logout
- `registration_success` - New user registration
- `registration_failure` - Failed registration attempt

**Authorization Events:**
- `unauthorized_access` - Attempt to access unauthorized resource
- `permission_denied` - Insufficient permissions
- `suspicious_activity` - Potentially malicious behavior

**Security Incidents:**
- `multiple_failed_logins` - Brute force attempt detection
- `invalid_operation` - Suspicious user actions
- `data_access_violation` - Unauthorized data access

### Business Events

**Content Operations:**
- `post_created` - New post creation
- `post_edited` - Post modification
- `post_deleted` - Post deletion
- `comment_created` - New comment
- `comment_edited` - Comment modification
- `comment_deleted` - Comment deletion

**Social Interactions:**
- `post_liked` - Post like action
- `post_unliked` - Post unlike action
- `user_followed` - Follow relationship created
- `user_unfollowed` - Follow relationship removed

### Performance Events

**Response Times:**
- `request_start` - Request initiated
- `request_end` - Request completed with duration
- `db_query_select` - Database read operations
- `db_query_insert` - Database write operations
- `page_load` - Page rendering performance

**Resource Usage:**
- `slow_query` - Database queries exceeding threshold
- `memory_usage` - Memory consumption metrics
- `error_rate` - Application error frequency

## Usage Examples

### Basic Logging

```python
from social_media_logger import social_logger

# Log business event
social_logger.log_business_event(
    event="user_action",
    details={"action": "profile_update", "user_id": 123}
)

# Log security event
social_logger.log_security_event(
    event_type="suspicious_activity",
    description="Multiple rapid requests detected",
    user_id=123,
    additional_data={"request_count": 50, "time_window": 60}
)
```

### Using Decorators

```python
from social_media_logger import log_execution_time, log_user_action

@log_execution_time('database_operation')
def expensive_database_query():
    # This will automatically log execution time
    pass

@log_user_action('update_profile')
def update_user_profile():
    # This will log the user action with success/failure
    pass
```

### Correlation ID Tracking

Each request gets a unique correlation ID that appears in all related log entries, making it easy to trace a complete user session:

```bash
grep "12345678-1234-1234-1234-123456789012" logs/application.log
```

## Monitoring and Alerting

### Critical Events to Monitor

1. **Security Alerts:**
   - Multiple failed login attempts
   - Unauthorized access attempts
   - Suspicious user behavior patterns

2. **Performance Alerts:**
   - Response times > 5 seconds
   - Database queries > 1 second
   - Error rate > 5%

3. **Business Alerts:**
   - Unusual user activity patterns
   - High volume of content deletions
   - Rapid follower changes

### Log Analysis Queries

**Find failed login attempts:**
```bash
grep -r "login_failure" logs/security.log | jq '.additional_data.username'
```

**Monitor performance issues:**
```bash
grep -r "duration_ms" logs/performance.log | jq 'select(.duration_ms > 1000)'
```

**Track user activity:**
```bash
grep -r "user_id.*123" logs/audit.log | jq '.action'
```

## Compliance and Audit

### GDPR Compliance

- User actions are logged with timestamps for audit trails
- Personal data in logs is properly masked
- Log retention periods can be configured
- User data deletion events are tracked

### SOX Compliance

- All financial/business critical operations are audited
- Immutable audit trails with tamper detection
- Role-based access logging
- Regular audit log reviews

### Data Privacy

- Sensitive fields (passwords, tokens) are automatically masked
- IP addresses and user agents are logged for security but can be anonymized
- Configurable data retention periods
- Secure log storage and access controls

## Production Deployment

### Log Aggregation

For production environments, configure log shipping to centralized logging:

```bash
# Example Fluentd configuration
<source>
  @type tail
  path /app/logs/*.log
  pos_file /var/log/fluentd/social_media.log.pos
  tag social_media.*
  format json
</source>

<match social_media.**>
  @type elasticsearch
  host elasticsearch.company.com
  port 9200
  index_name social_media_logs
</match>
```

### Security Considerations

- Log files should be stored on separate, secure storage
- Access to logs should be restricted and audited
- Log integrity should be monitored (checksums)
- Sensitive data should never appear in logs

### Performance Impact

- Asynchronous logging minimizes performance impact
- Log levels can be adjusted based on environment
- Structured logging enables efficient parsing
- Log rotation prevents disk space issues

## Troubleshooting

### Common Issues

1. **Log files not created:** Check `LOG_DIR` permissions
2. **Performance degradation:** Reduce `LOG_LEVEL` in production
3. **Disk space issues:** Verify log rotation is working
4. **Missing correlation IDs:** Ensure `setup_request_logging()` is called

### Debug Mode

For development, enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
export FLASK_ENV=development
```

This will provide detailed request/response information and SQL queries.

## Maintenance

### Regular Tasks

1. **Log Rotation Monitoring:** Ensure automated rotation is working
2. **Disk Space Monitoring:** Alert when log partition reaches 80%
3. **Log Analysis:** Regular review of security and error patterns
4. **Archive Management:** Move old logs to long-term storage
5. **Performance Review:** Analyze slow queries and optimize

### Backup Strategy

- Critical audit logs should be backed up daily
- Security logs should be archived for compliance periods
- Performance logs can have shorter retention
- Implement immutable backup storage for audit trails