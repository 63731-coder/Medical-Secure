"""
Custom middleware for MedSecure application
"""

from .security_logging import SecurityLoggingMiddleware

__all__ = ['SecurityLoggingMiddleware']
