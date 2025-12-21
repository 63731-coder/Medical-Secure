<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../services/api';
import { decryptData, encryptData, deriveKeyFromUser } from '../utils/crypto';
import StatusAlert from '../components/StatusAlert.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import { useNotifications } from '../composables/useNotifications';
import CryptoJS from 'crypto-js';

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
const showEditModal = ref(false);
const recordToEdit = ref(null);
const editFile = ref(null);
const editName = ref('');
const editDescription = ref('');
const editLoading = ref(false);

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
        let url = '/files/';
        
        // Add patient filter if patient_id is provided
        if (patientId.value) {
            url += `?patient_id=${patientId.value}`;
        }
        
        const response = await api.get(url);
        
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
        // 1. Download encrypted blob from server
        const response = await api.get(`/files/${record.id}/download/`, { responseType: 'blob' });
        
        // 2. Read blob as text
        const encryptedText = await response.data.text();
        
        // 3. Decrypt using PATIENT'S key (not current user's key)
        // Generate the patient's encryption key from their credentials
        const patientUsername = record.patient.user.username;
        const patientKeycloakId = record.patient.keycloak_id;
        
        // Derive patient's key (same as deriveKeyFromUser but inline)
        const seed = `${patientUsername}:${patientKeycloakId}:medical-secure`;
        const patientKey = CryptoJS.PBKDF2(seed, 'keycloak-medical-salt', {
            keySize: 256 / 32,
            iterations: 100000  // NIST recommande minimum 100k iterations
        }).toString();
        
        // Decrypt with patient's key
        const bytes = CryptoJS.AES.decrypt(encryptedText, patientKey);
        const decryptedBase64 = bytes.toString(CryptoJS.enc.Utf8);
        
        if (!decryptedBase64) {
            throw new Error("Decryption failed. Wrong key?");
        }
        
        // 4. Convert Base64 back to binary
        const binaryString = atob(decryptedBase64);
        const bytesArray = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytesArray[i] = binaryString.charCodeAt(i);
        }
        
        // 5. Create download link for decrypted file
        const blob = new Blob([bytesArray], { type: 'application/octet-stream' });
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

const openEditModal = (record) => {
    recordToEdit.value = record;
    editName.value = record.name.replace('.enc', '');
    editDescription.value = record.description || '';
    editFile.value = null;
    showEditModal.value = true;
};

const handleEditFileChange = (event) => {
    editFile.value = event.target.files[0];
};

const saveEdit = async () => {
    if (!editName.value) {
        notifyError('File name is required');
        return;
    }
    
    editLoading.value = true;
    
    try {
        const formData = new FormData();
        formData.append('name', editName.value);
        formData.append('description', editDescription.value);
        
        // If new file is provided, encrypt and add it
        if (editFile.value) {
            const reader = new FileReader();
            reader.readAsArrayBuffer(editFile.value);
            
            await new Promise((resolve, reject) => {
                reader.onload = async (e) => {
                    try {
                        const arrayBuffer = e.target.result;
                        const uint8Array = new Uint8Array(arrayBuffer);
                        let binary = '';
                        uint8Array.forEach(byte => binary += String.fromCharCode(byte));
                        const base64Content = btoa(binary);
                        
                        const encryptedContent = encryptData(base64Content);
                        if (!encryptedContent) {
                            throw new Error('Encryption failed');
                        }
                        
                        const encryptedBlob = new Blob([encryptedContent], { type: 'application/octet-stream' });
                        formData.append('file', encryptedBlob, editFile.value.name + '.enc');
                        resolve();
                    } catch (err) {
                        reject(err);
                    }
                };
                reader.onerror = reject;
            });
        }
        
        await api.put(`/files/${recordToEdit.value.id}/edit/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        notifySuccess('Medical record updated successfully');
        showEditModal.value = false;
        recordToEdit.value = null;
        editFile.value = null;
        await fetchRecords();
        
    } catch (err) {
        console.error('Edit error:', err);
        const errorMsg = err.response?.data?.error || 'Failed to update record';
        notifyError(errorMsg);
    } finally {
        editLoading.value = false;
    }
};

const cancelEdit = () => {
    showEditModal.value = false;
    recordToEdit.value = null;
    editFile.value = null;
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
                            <button v-if="userType === 'patient'" @click="openEditModal(file)" class="text-green-600 hover:text-green-900 font-medium inline-flex items-center gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                Edit
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

        <!-- Edit File Modal -->
        <Transition name="modal">
            <div v-if="showEditModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" @click.self="cancelEdit">
                <div class="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 overflow-hidden">
                    <div class="px-6 py-4 border-b border-gray-200">
                        <h3 class="text-lg font-semibold text-gray-900">Edit Medical Record</h3>
                    </div>
                    
                    <div class="px-6 py-4 space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Document Title</label>
                            <input v-model="editName" type="text" required
                                class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="e.g., Blood Test Results">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Description (Optional)</label>
                            <textarea v-model="editDescription" rows="3"
                                class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="Add description..."></textarea>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Replace File (Optional)</label>
                            <input type="file" @change="handleEditFileChange"
                                class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100" />
                            <p class="text-xs text-gray-500 mt-2">Leave empty to keep current file, or upload a new one to replace it.</p>
                        </div>
                    </div>
                    
                    <div class="px-6 py-4 bg-gray-50 flex justify-end gap-3">
                        <button @click="cancelEdit" :disabled="editLoading"
                            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50">
                            Cancel
                        </button>
                        <button @click="saveEdit" :disabled="editLoading"
                            class="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition disabled:opacity-50">
                            {{ editLoading ? 'Saving...' : 'Save Changes' }}
                        </button>
                    </div>
                </div>
            </div>
        </Transition>
    </div>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
</style>