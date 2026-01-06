"""
Security event logging utilities
Log business-critical security events
"""

from config.logging_config import security_logger


def log_patient_doctor_relation_created(patient_id: int, patient_username: str, 
                                       doctor_id: int, doctor_username: str,
                                       initiated_by: str = 'patient'):
    """Log when a patient-doctor relationship is created"""
    security_logger.info(
        f"Patient-Doctor relation created",
        patient_id=patient_id,
        patient_username=patient_username,
        doctor_id=doctor_id,
        doctor_username=doctor_username,
        initiated_by=initiated_by
    )


def log_shared_key_created(patient_id: int, doctor_id: int, patient_username: str, doctor_username: str):
    """Log when an encryption key is shared"""
    security_logger.info(
        f"Encryption key shared",
        patient_id=patient_id,
        doctor_id=doctor_id,
        patient_username=patient_username,
        doctor_username=doctor_username
    )


def log_file_uploaded(patient_id: int, doctor_id: int, filename: str, file_size: int):
    """Log when a medical file is uploaded"""
    security_logger.info(
        f"Medical file uploaded",
        patient_id=patient_id,
        doctor_id=doctor_id,
        filename=filename,
        file_size_bytes=file_size
    )


def log_file_accessed(file_id: str, user_id: int, user_type: str, patient_id: int):
    """Log when a medical file is accessed/downloaded"""
    security_logger.info(
        f"Medical file accessed",
        file_id=file_id,
        user_id=user_id,
        user_type=user_type,
        patient_id=patient_id
    )


def log_file_deleted(file_id: str, filename: str, deleted_by_user_id: int, patient_id: int):
    """Log when a medical file is deleted"""
    security_logger.warning(
        f"Medical file deleted",
        file_id=file_id,
        filename=filename,
        deleted_by_user_id=deleted_by_user_id,
        patient_id=patient_id
    )


def log_unauthorized_access_attempt(user_id: int, user_username: str, 
                                    attempted_resource: str, reason: str):
    """Log unauthorized access attempts"""
    security_logger.warning(
        f"Unauthorized access attempt",
        user_id=user_id,
        user_username=user_username,
        attempted_resource=attempted_resource,
        reason=reason
    )


def log_authentication_failure(username: str, ip_address: str, reason: str):
    """Log failed authentication attempts"""
    security_logger.warning(
        f"Authentication failure",
        username=username,
        ip_address=ip_address,
        reason=reason
    )


def log_suspicious_activity(user_id: int, activity: str, details: dict):
    """Log suspicious activities"""
    security_logger.critical(
        f"Suspicious activity detected",
        user_id=user_id,
        activity=activity,
        **details
    )


def log_user_registered(user_id: int, username: str, user_type: str, keycloak_id: str):
    """Log new user registration"""
    security_logger.info(
        f"New user registered",
        user_id=user_id,
        username=username,
        user_type=user_type,
        keycloak_id=keycloak_id
    )


def log_data_decryption_failure(user_id: int, resource_type: str, resource_id: int):
    """Log when data decryption fails (potential tampering or key mismatch)"""
    security_logger.error(
        f"Data decryption failure",
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id
    )
