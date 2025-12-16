import axios from 'axios';

// Backend Django API base URL
const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add token to all requests
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Token ${token}`;
    }
    return config;
});

export default {
    // Auth
    register(userData) {
        return apiClient.post('/register/', userData);
    },
    
    login(credentials) {
        return apiClient.post('/login/', credentials);
    },
    
    logout() {
        return apiClient.post('/logout/');
    },
    
    getProfile() {
        return apiClient.get('/profile/');
    },

    // Medical Records
    getMedicalRecord() {
        return apiClient.get('/files/');
    },

    // Upload file (file must be encrypted BEFORE calling this)
    uploadFile(formData) {
        return apiClient.post('/files/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
    },
    
    downloadFile(fileId) {
        return apiClient.get(`/files/${fileId}/`);
    },
    
    deleteFile(fileId) {
        return apiClient.delete(`/files/${fileId}/`);
    },

    // Doctors
    getDoctors() {
        return apiClient.get('/doctors/');
    },
    
    addDoctor(patientId, doctorId) {
        return apiClient.post(`/patients/${patientId}/add-doctor/`, { doctor_id: doctorId });
    },
    
    removeDoctor(patientId, doctorId) {
        return apiClient.delete(`/patients/${patientId}/remove-doctor/${doctorId}/`);
    },

    // Patients
    getPatients() {
        return apiClient.get('/patients/');
    },
    
    // Notifications
    getNotifications() {
        return apiClient.get('/notifications/');
    },
    
    getNotification(id) {
        return apiClient.get(`/notifications/${id}/`);
    },
    
    markNotificationAsRead(id) {
        return apiClient.post(`/notifications/${id}/mark-read/`);
    },
    
    markAllNotificationsAsRead() {
        return apiClient.post('/notifications/mark-all-read/');
    },
    
    getUnreadNotificationCount() {
        return apiClient.get('/notifications/unread-count/');
    },
    
    // Appointment Requests
    requestAppointment(patientId) {
        return apiClient.post('/appointments/request/', { patient_id: patientId });
    },
    
    getAppointmentRequests(patientId) {
        return apiClient.get(`/patients/${patientId}/appointment-requests/`);
    },
    
    respondToAppointmentRequest(patientId, requestId, action) {
        return apiClient.post(`/patients/${patientId}/appointment-requests/${requestId}/respond/`, { action });
    },
    
    // File Action Requests
    getPendingFileActions() {
        return apiClient.get('/files/pending-file-actions/');
    },
    
    respondToFileAction(requestId, action) {
        return apiClient.post('/files/respond-file-action/', { 
            request_id: requestId, 
            action 
        });
    },
    
    // Audit Logs
    getAuditLogs() {
        return apiClient.get('/audit-logs/');
    },
    
    getSecurityEvents() {
        return apiClient.get('/audit-logs/security-events/');
    },
    
    // File operations with doctor workflow
    uploadFileAsDoctor(formData, patientId) {
        formData.append('patient_id', patientId);
        return apiClient.post('/files/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
    },
    
    modifyFile(fileId, formData) {
        return apiClient.patch(`/files/${fileId}/`, formData);
    },
    
    downloadFileSecure(fileId) {
        return apiClient.get(`/files/${fileId}/download/`, {
            responseType: 'blob'
        });
    }
};