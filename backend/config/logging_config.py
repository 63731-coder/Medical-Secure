"""
Logging configuration for MedSecure application
Provides structured JSON logging with security-focused features
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict


class SecurityLogger:
    """
    Centralized security logger for the application
    Logs structured JSON format compatible with ELK stack
    """
    
    def __init__(self, name: str = 'medsecure'):
        self.logger = logging.getLogger(name)
        
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from logs"""
        sensitive_keys = [
            'password', 'token', 'key', 'secret', 'encrypted_key',
            'access_token', 'refresh_token', 'first_name', 'last_name',
            'date_of_birth', 'encryption_key'
        ]
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _format_log(self, level: str, action: str, details: Dict[str, Any] = None) -> str:
        """Format log entry as JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'action': action,
            'service': 'medsecure-backend'
        }
        
        if details:
            log_entry['details'] = self._sanitize_data(details)
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def info(self, action: str, **kwargs):
        """Log informational message"""
        self.logger.info(self._format_log('INFO', action, kwargs))
    
    def warning(self, action: str, **kwargs):
        """Log warning message"""
        self.logger.warning(self._format_log('WARNING', action, kwargs))
    
    def error(self, action: str, **kwargs):
        """Log error message"""
        self.logger.error(self._format_log('ERROR', action, kwargs))
    
    def critical(self, action: str, **kwargs):
        """Log critical security event"""
        self.logger.critical(self._format_log('CRITICAL', action, kwargs))


# Create global security logger instance
security_logger = SecurityLogger()
