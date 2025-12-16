from .models import AuditLog, Notification
from django.utils import timezone


def log_action(user, action, ip_address=None, user_agent=None, medical_file=None, 
               patient=None, success=True, error_message='', details=None):
    """
    Create an audit log entry for security tracking
    """
    return AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        medical_file=medical_file,
        patient=patient,
        success=success,
        error_message=error_message,
        details=details or {}
    )


def create_notification(recipient, sender, notification_type, title, message,
                       file_action_request=None, appointment_request=None):
    """
    Create a notification for user
    """
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message=message,
        file_action_request=file_action_request,
        appointment_request=appointment_request
    )


def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Get user agent from request
    """
    return request.META.get('HTTP_USER_AGENT', '')


def mark_notification_as_read(notification):
    """
    Mark a notification as read with timestamp
    """
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    return notification
