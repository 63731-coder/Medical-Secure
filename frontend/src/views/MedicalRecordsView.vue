<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { decryptData } from '../utils/crypto';
import StatusAlert from '../components/StatusAlert.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import api from '../services/api';
import { useNotifications } from '../composables/useNotifications';

const route = useRoute();
const router = useRouter();
const { success: notifySuccess, error: notifyError } = useNotifications();
const records = ref([]);
const loading = ref(true);
const error = ref("");
const patient = ref(null);
const patientId = ref(route.query.patient_id);
const userType = ref(null);
const showDeleteModal = ref(false);
const recordToDelete = ref(null);

// Fetch patient info if patient_id is provided
const fetchPatient = async () => {
    if (!patientId.value) return;
    
    try {
        const response = await api.getPatients();
        const foundPatient = response.data.find(p => p.id === parseInt(patientId.value));
        if (foundPatient) {
            patient.value = foundPatient;
        }
    } catch (e) {
        console.error("Failed to load patient:", e);
    }
};

// Fetch medical records from API
const fetchRecords = async () => {
    try {
        const token = localStorage.getItem('accessToken');
        let url = 'http://127.0.0.1:8000/api/files/';
        
        // Add patient filter if patient_id is provided
        if (patientId.value) {
            url += `?patient_id=${patientId.value}`;
        }
        
        const response = await axios.get(url, {
            headers: { 'Authorization': `Token ${token}` }
        });
        
        records.value = response.data;
        loading.value = false;
    } catch (e) {
        console.error("Failed to load records:", e);
        error.value = "Failed to load records.";
        loading.value = false;
    }
};

const handleDownload = async (record) => {
    try {
        const token = localStorage.getItem('accessToken');
        
        // 1. Download encrypted blob from server
        const response = await axios.get(`http://127.0.0.1:8000/api/files/${record.id}/download/`, {
            headers: { 'Authorization': `Token ${token}` },
            responseType: 'blob'
        });
        
        // 2. Read blob as text
        const encryptedText = await response.data.text();
        
        // 3. Decrypt using client-side key
        const decryptedBase64 = decryptData(encryptedText);
        
        if (!decryptedBase64) {
            throw new Error("Decryption failed. Wrong key?");
        }
        
        // 4. Convert Base64 back to binary
        const binaryString = atob(decryptedBase64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // 5. Create download link for decrypted file
        const blob = new Blob([bytes], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = record.name.replace('.enc', ''); // Remove .enc extension
        link.click();
        URL.revokeObjectURL(url);
        
        console.log(`✅ File ${record.name} decrypted and downloaded`);
    } catch (err) {
        console.error("Download/decryption error:", err);
        error.value = `Failed to decrypt ${record.name}`;
    }
};

const openDeleteModal = (record) => {
    recordToDelete.value = record;
    showDeleteModal.value = true;
};

const confirmDelete = async () => {
    showDeleteModal.value = false;
    const record = recordToDelete.value;
    
    try {
        const response = await api.deleteFile(record.id);
        
        // Check if it's a pending request (for doctors)
        if (response.data?.pending) {
            notifySuccess('Delete request sent to patient for approval');
            error.value = '';
        } else {
            // Direct deletion (for patients)
            notifySuccess('File deleted successfully');
            error.value = '';
            await fetchRecords();
        }
    } catch (err) {
        console.error("Delete error:", err);
        const errorMsg = err.response?.data?.error || 'Failed to delete file';
        error.value = errorMsg;
        notifyError(errorMsg);
    } finally {
        recordToDelete.value = null;
    }
};

const cancelDelete = () => {
    showDeleteModal.value = false;
    recordToDelete.value = null;
};

const getDeleteModalMessage = () => {
    if (!recordToDelete.value) return '';
    
    return userType.value === 'doctor' 
        ? `Request to delete "${recordToDelete.value.name}"? The patient must approve this action.`
        : `Are you sure you want to delete "${recordToDelete.value.name}"? This action cannot be undone.`;
};

onMounted(async () => {
    // Get user profile to determine user type
    try {
        const profileRes = await api.getProfile();
        userType.value = profileRes.data.user_type;
    } catch (e) {
        console.error('Failed to get user profile:', e);
    }
    
    await fetchPatient();
    await fetchRecords();
});
</script>

<template>
    <div class="max-w-4xl mx-auto mt-8">
        <div class="mb-6">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center">
                    <button v-if="patientId" @click="router.back()" 
                        class="mr-4 text-gray-600 hover:text-gray-900 transition">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                    </button>
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900">
                            {{ patient ? `${patient.user.first_name} ${patient.user.last_name}'s Medical Records` : 'My Medical Records' }}
                        </h1>
                        <p v-if="patient" class="text-gray-600 mt-1">
                            Date of Birth: {{ new Date(patient.date_of_birth).toLocaleDateString() }}
                        </p>
                    </div>
                </div>
                <button @click="router.push('/upload')"
                    class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    Add Medical Record
                </button>
            </div>
        </div>

        <StatusAlert v-if="error" type="error" :message="error" />

        <div v-if="loading" class="text-center py-10 text-gray-500">Loading secure records...</div>

        <div v-else class="bg-white rounded-xl shadow overflow-hidden border border-gray-100">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Document Title</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description
                        </th>
                        <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Action</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="file in records" :key="file.id" class="hover:bg-gray-50 transition">
                        <td class="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{{ file.name }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">{{ new Date(file.created_at).toLocaleDateString() }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">{{ file.description || 'N/A' }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                            <button @click="handleDownload(file)" class="text-blue-600 hover:text-blue-900 font-medium inline-flex items-center gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                Download
                            </button>
                            <button @click="openDeleteModal(file)" class="text-red-600 hover:text-red-900 font-medium inline-flex items-center gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                Delete
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div v-if="records.length === 0" class="p-6 text-center text-gray-500">
                No records found.
            </div>
        </div>

        <!-- Delete File Modal -->
        <ConfirmModal
            :show="showDeleteModal"
            :title="userType === 'doctor' ? 'Request File Deletion' : 'Delete File'"
            :message="getDeleteModalMessage()"
            :confirmText="userType === 'doctor' ? 'Send Request' : 'Delete'"
            :cancelText="'Cancel'"
            :isDangerous="true"
            @confirm="confirmDelete"
            @cancel="cancelDelete"
        />
    </div>
</template>