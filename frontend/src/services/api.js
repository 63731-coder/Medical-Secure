import axios from 'axios';

// URL de votre backend Django
const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Intercepteur pour ajouter le token Keycloak automatiquement (à configurer plus tard)
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('keycloak_token'); // Simplification pour l'exemple
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default {
    // Récupérer le dossier médical (fichiers)
    getMedicalRecord() {
        return apiClient.get('/medical-record/');
    },

    // Uploader un fichier
    uploadFile(formData) {
        // RAPPEL: Le contenu du fichier doit être chiffré AVANT d'arriver ici [cite: 42]
        return apiClient.post('/medical-record/upload/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
    }
};