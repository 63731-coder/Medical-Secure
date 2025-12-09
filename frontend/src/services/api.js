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
    }
};