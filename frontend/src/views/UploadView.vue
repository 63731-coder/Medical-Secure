<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';
import { useRouter } from 'vue-router';
import { encryptData } from '../utils/crypto';
import StatusAlert from '../components/StatusAlert.vue';
import { useNotifications } from '../composables/useNotifications';

const router = useRouter();
const { success: notifySuccess, error: notifyError } = useNotifications();

const file = ref(null);
const title = ref("");
const loading = ref(false);
const status = ref({ type: 'info', message: '' });
const userType = ref(null);
const patients = ref([]);
const selectedPatient = ref(null);

onMounted(async () => {
    try {
        const profileRes = await api.getProfile();
        userType.value = profileRes.data.user_type;
        
        // If doctor, fetch patients list
        if (userType.value === 'doctor') {
            const patientsRes = await api.getPatients();
            patients.value = patientsRes.data;
        }
    } catch (e) {
        console.error('Failed to fetch profile:', e);
    }
});

const handleFileChange = (event) => {
    file.value = event.target.files[0];
};

const handleUpload = async () => {
    if (!file.value || !title.value) {
        status.value = { type: 'error', message: "Please select a file and a title." };
        return;
    }
    
    // Doctors must select a patient
    if (userType.value === 'doctor' && !selectedPatient.value) {
        status.value = { type: 'error', message: "Please select a patient." };
        return;
    }

    loading.value = true;
    status.value = { type: 'info', message: "Reading and encrypting file..." };

    // 1. Read file locally as ArrayBuffer (works for all file types including PDFs)
    const reader = new FileReader();
    reader.readAsArrayBuffer(file.value);

    reader.onload = async (e) => {
        try {
            const arrayBuffer = e.target.result;
            // Convert ArrayBuffer to Base64 string for encryption
            const uint8Array = new Uint8Array(arrayBuffer);
            let binary = '';
            uint8Array.forEach(byte => binary += String.fromCharCode(byte));
            const base64Content = btoa(binary);

            // 2. Encrypt Content (Client-Side)
            // The server NEVER sees the rawContent
            const encryptedContent = encryptData(base64Content);

            if (!encryptedContent) {
                throw new Error("Encryption failed. Are you logged in?");
            }

            // 3. Prepare Form Data (Django expects a file)
            // We create a new Blob from the encrypted string
            const encryptedBlob = new Blob([encryptedContent], { type: 'application/octet-stream' });
            const formData = new FormData();
            formData.append('name', title.value);
            formData.append('description', ''); // Add empty description field
            formData.append('file', encryptedBlob, file.value.name + ".enc"); // Add .enc extension
            
            // If doctor, add patient_id
            if (userType.value === 'doctor') {
                formData.append('patient_id', selectedPatient.value);
            }

            // 4. Send to Server
            status.value = { type: 'info', message: "Uploading encrypted data..." };

            await api.post('/files/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            // Patient upload - immediate success
            if (userType.value === 'patient') {
                status.value = { type: 'success', message: "File encrypted and uploaded successfully!" };
                notifySuccess('File uploaded successfully');
            }
            
            title.value = "";
            file.value = null;
            selectedPatient.value = null;

        } catch (error) {
            console.error('Upload error:', error);
            console.error('Response data:', error.response?.data);
            console.error('Response status:', error.response?.status);
            
            // Check if it's a pending request (for doctors)
            if (error.response?.data?.pending) {
                status.value = { type: 'success', message: error.response.data.message };
                notifySuccess('Upload request sent to patient for approval');
            } else {
                const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message;
                status.value = { type: 'error', message: "Upload failed: " + errorMsg };
                notifyError('Upload failed: ' + errorMsg);
            }
        } finally {
            loading.value = false;
        }
    };
};
</script>

<template>
    <div class="max-w-xl mx-auto bg-white p-8 rounded-xl shadow border border-gray-100 mt-10">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Secure Document Upload</h2>

        <StatusAlert :type="status.type" :message="status.message" />

        <form @submit.prevent="handleUpload" class="space-y-6">
            <!-- Patient Selector (for doctors only) -->
            <div v-if="userType === 'doctor'" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    Select Patient
                </label>
                <select v-model="selectedPatient" required
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
                    <option :value="null" disabled>Choose a patient...</option>
                    <option v-for="patient in patients" :key="patient.id" :value="patient.id">
                        {{ patient.user.first_name }} {{ patient.user.last_name }} (@{{ patient.user.username }})
                    </option>
                </select>
                <p class="text-xs text-blue-600 mt-2">⚠️ Patient approval required for upload</p>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Document Title</label>
                <input v-model="title" type="text" required
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="e.g., Blood Test Results">
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Select File</label>
                <div
                    class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50 transition">
                    <input type="file" @change="handleFileChange"
                        class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
                </div>
                <p class="text-xs text-gray-500 mt-2">File will be encrypted locally using AES-256 before upload.</p>
            </div>

            <button type="submit" :disabled="loading"
                class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition disabled:bg-blue-300">
                {{ loading ? 'Processing...' : 'Encrypt & Upload' }}
            </button>
        </form>
    </div>
</template>