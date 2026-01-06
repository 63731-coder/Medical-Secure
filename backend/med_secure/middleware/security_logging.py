"""
Security logging middleware for Django
Logs all API requests with security context
"""

import time
import json
from django.utils.deprecation import MiddlewareMixin
from config.logging_config import security_logger


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests with security context
    Logs: timestamp, user, endpoint, method, status, duration
    """
    
    def process_request(self, request):
        """Store request start time"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log request details after response is ready"""
        # Only log API endpoints
        if not request.path.startswith('/api/'):
            return response
        
        # Calculate request duration
        duration = time.time() - getattr(request, '_start_time', time.time())
        
        # Get user info
        user_info = 'anonymous'
        user_type = 'unknown'
        user_id = None
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = request.user.username
            user_id = request.user.id
            
            # Determine user type
            if hasattr(request.user, 'patient_profile'):
                user_type = 'patient'
            elif hasattr(request.user, 'doctor_profile'):
                user_type = 'doctor'
            elif request.user.is_staff:
                user_type = 'admin'
        
        # Determine log level based on status code
        status_code = response.status_code
        if status_code >= 500:
            level = 'critical'
        elif status_code >= 400:
            level = 'warning'
        else:
            level = 'info'
        
        # Build log details
        details = {
            'method': request.method,
            'path': request.path,
            'status_code': status_code,
            'user': user_info,
            'user_id': user_id,
            'user_type': user_type,
            'duration_ms': round(duration * 1000, 2),
            'ip_address': self._get_client_ip(request),
            'query_params': dict(request.GET) if request.GET else None
        }
        
        # Log with appropriate level
        action = f"{request.method} {request.path}"
        getattr(security_logger, level)(action, **details)
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def process_exception(self, request, exception):
        """Log unhandled exceptions"""
        security_logger.error(
            'Unhandled exception in request',
            path=request.path,
            method=request.method,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            user=request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
        )
        return None
