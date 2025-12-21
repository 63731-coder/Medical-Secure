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
    const token = localStorage.getItem('access_token');  // Keycloak uses 'access_token'
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;  // JWT uses Bearer
    }
    return config;
});

export default {
    // Generic HTTP methods (for direct API calls)
    get(url, config) {
        return apiClient.get(url, config);
    },
    
    post(url, data, config) {
        return apiClient.post(url, data, config);
    },
    
    put(url, data, config) {
        return apiClient.put(url, data, config);
    },
    
    delete(url, config) {
        return apiClient.delete(url, config);
    },

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
        return apiClient.get('/auth/me/');  // Keycloak endpoint
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
    
    // Download encrypted file (returns blob for client-side decryption)
    downloadFile(fileId) {
        return apiClient.get(`/files/${fileId}/download/`, {
            responseType: 'blob'
        });
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

    // All patients (for doctors)
    getAllPatients() {
        return apiClient.get('/all-patients/');
    },

    // Doctor-Patient Requests
    getRequests() {
        return apiClient.get('/requests/');
    },

    createRequest(data) {
        return apiClient.post('/requests/', data);
    },

    approveRequest(requestId) {
        return apiClient.post(`/requests/${requestId}/approve/`);
    },

    rejectRequest(requestId) {
        return apiClient.post(`/requests/${requestId}/reject/`);
    },

    // File Action Requests
    getFileActionRequests() {
        return apiClient.get('/file-requests/');
    },

    approveFileAction(requestId) {
        return apiClient.post(`/file-requests/${requestId}/approve/`);
    },

    rejectFileAction(requestId) {
        return apiClient.post(`/file-requests/${requestId}/reject/`);
    }
};