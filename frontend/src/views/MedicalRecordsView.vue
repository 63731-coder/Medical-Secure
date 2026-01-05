<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../services/api';
import { decryptData, encryptData, deriveKeyFromUser, decryptSharedKey, decryptWithSharedKey, encryptWithSharedKey, decryptMetadata, encryptMetadata, getCurrentKey } from '../utils/crypto';
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
const currentDoctorId = ref(null);  // For doctors to decrypt shared keys
const showDeleteModal = ref(false);
const recordToDelete = ref(null);
const showEditModal = ref(false);
const recordToEdit = ref(null);
const editFile = ref(null);
const editName = ref('');
const editDescription = ref('');
const editLoading = ref(false);
const decryptedPatientName = ref(''); // Store decrypted patient name
const decryptedPatientDOB = ref(''); // Store decrypted date of birth

// Fetch patient info if patient_id is provided
const fetchPatient = async () => {
    if (!patientId.value) return;
    
    try {
        const response = await api.getPatients();
        const foundPatient = response.data.find(p => p.id === parseInt(patientId.value));
        if (foundPatient) {
            patient.value = foundPatient;
            
            // Decrypt patient data if doctor is viewing
            if (userType.value === 'doctor' && currentDoctorId.value) {
                await decryptPatientData();
            }
        }
    } catch (e) {
        console.error("Failed to load patient:", e);
    }
};

// Decrypt patient name and DOB for doctor view
const decryptPatientData = async () => {
    if (!patient.value) return;
    
    try {
        const keyResponse = await api.get(`/get-shared-key/?patient_id=${patient.value.id}`);
        const encryptedPatientKey = keyResponse.data.encrypted_key;
        const patientKey = decryptSharedKey(encryptedPatientKey, currentDoctorId.value);
        
        if (patientKey) {
            decryptedPatientName.value = patient.value.encrypted_first_name && patient.value.encrypted_last_name
                ? `${decryptWithSharedKey(patient.value.encrypted_first_name, patientKey)} ${decryptWithSharedKey(patient.value.encrypted_last_name, patientKey)}`
                : `${patient.value.user.first_name} ${patient.value.user.last_name}`;
            
            decryptedPatientDOB.value = patient.value.encrypted_date_of_birth
                ? decryptWithSharedKey(patient.value.encrypted_date_of_birth, patientKey)
                : patient.value.date_of_birth;
        }
    } catch (e) {
        console.warn('Failed to decrypt patient data:', e);
        decryptedPatientName.value = `${patient.value.user.first_name} ${patient.value.user.last_name}`;
        decryptedPatientDOB.value = patient.value.date_of_birth;
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

// Decrypt metadata for display
const getDecryptedName = (record) => {
    if (!record.encrypted_name) return record.name || 'Untitled';
    
    try {
        if (userType.value === 'doctor' && patientId.value) {
            // Doctor viewing patient file - need to use shared key
            // This is a simplified approach - in production, cache the shared key
            return record.name; // Fallback to plaintext for now (will decrypt on mount)
        }
        return decryptMetadata(record.encrypted_name) || record.name || 'Untitled';
    } catch (e) {
        console.error('Failed to decrypt name:', e);
        return record.name || 'Encrypted';
    }
};

const getDecryptedDate = (record) => {
    if (!record.encrypted_date) return record.created_at;
    
    try {
        const decrypted = decryptMetadata(record.encrypted_date);
        return decrypted || record.created_at;
    } catch (e) {
        console.error('Failed to decrypt date:', e);
        return record.created_at;
    }
};

const handleDownload = async (record) => {
    try {
        let decryptedBase64;
        
        // 1. Download encrypted blob from server
        const response = await api.get(`/files/${record.id}/download/`, { responseType: 'blob' });
        
        // 2. Read blob as text
        const encryptedText = await response.data.text();
        
        // 3. Decrypt based on user type
        if (userType.value === 'doctor' && patientId.value) {
            // Doctor downloading patient file - use shared key
            try {
                // Get shared encryption key from API
                const keyResponse = await api.get('/get-shared-key/', {
                    params: { patient_id: patientId.value }
                });
                
                const encryptedSharedKey = keyResponse.data.encrypted_key;
                
                // SIMPLIFIED: Decrypt using doctor ID only
                const patientKey = decryptSharedKey(encryptedSharedKey, currentDoctorId.value);
                
                if (!patientKey) {
                    throw new Error("Failed to decrypt shared encryption key");
                }
                
                // Decrypt file content using patient's key
                decryptedBase64 = decryptWithSharedKey(encryptedText, patientKey);
            } catch (keyError) {
                console.error("Shared key error:", keyError);
                throw new Error("Cannot access patient files. Key sharing may not be set up.");
            }
        } else {
            // Patient downloading their own file - use their key
            decryptedBase64 = decryptData(encryptedText);
        }
        
        if (!decryptedBase64) {
            throw new Error("Decryption failed. Encryption key not found or invalid.");
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
        
        // Remove .enc extension properly
        const cleanName = record.name.replace(/\.enc$/, '');
        link.download = cleanName;
        
        link.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        console.error("Download/decryption error:", err);
        error.value = `Failed to decrypt ${record.name}: ${err.message}`;
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
        
        // Encrypt metadata before sending
        const encryptionKey = userType.value === 'doctor' && patientId.value ?
            // Doctor: use patient's shared key
            decryptSharedKey(
                (await api.get('/get-shared-key/', { params: { patient_id: patientId.value } })).data.encrypted_key,
                currentDoctorId.value
            ) :
            // Patient: use own key
            getCurrentKey();
        
        const currentDate = new Date().toISOString();
        const encryptedName = encryptWithSharedKey(editName.value, encryptionKey) || encryptMetadata(editName.value);
        const encryptedDescription = encryptWithSharedKey(editDescription.value, encryptionKey) || encryptMetadata(editDescription.value);
        const encryptedDate = encryptWithSharedKey(currentDate, encryptionKey) || encryptMetadata(currentDate);
        
        formData.append('encrypted_name', encryptedName);
        formData.append('encrypted_description', encryptedDescription);
        formData.append('encrypted_date', encryptedDate);
        
        // If doctor, add encrypted_file_* fields
        if (userType.value === 'doctor') {
            formData.append('encrypted_file_name', encryptedName);
            formData.append('encrypted_file_description', encryptedDescription);
            formData.append('encrypted_file_date', encryptedDate);
        }
        
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
                        
                        let encryptedContent;
                        
                        // Check if user is a doctor - must use patient's key
                        if (userType.value === 'doctor') {
                            try {
                                // Get patient's shared encryption key
                                const keyResponse = await api.get('/get-shared-key/', {
                                    params: { patient_id: patientId.value }
                                });
                                
                                const encryptedSharedKey = keyResponse.data.encrypted_key;
                                
                                // Decrypt patient's key using doctor's ID
                                const patientKey = decryptSharedKey(encryptedSharedKey, currentDoctorId.value);
                                
                                if (!patientKey) {
                                    throw new Error("Failed to decrypt patient's encryption key");
                                }
                                
                                // Encrypt file content with patient's key
                                encryptedContent = encryptWithSharedKey(base64Content, patientKey);
                                
                                if (!encryptedContent) {
                                    throw new Error("Failed to encrypt file with patient's key");
                                }
                            } catch (keyError) {
                                console.error("Key retrieval error:", keyError);
                                throw new Error("Cannot encrypt file for patient. Ensure you have access to their key.");
                            }
                        } else {
                            // Patient editing their own file - use their own key
                            encryptedContent = encryptData(base64Content);
                            if (!encryptedContent) {
                                throw new Error('Encryption failed');
                            }
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
        
        const response = await api.put(`/files/${recordToEdit.value.id}/edit/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        // Check if it's a pending request (for doctors)
        if (response.data?.pending) {
            notifySuccess('Edit request sent to patient for approval');
        } else {
            // Direct update (for patients)
            notifySuccess('Medical record updated successfully');
            await fetchRecords();
        }
        
        showEditModal.value = false;
        recordToEdit.value = null;
        editFile.value = null;
        
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
        
        // Get doctor ID if user is a doctor
        if (userType.value === 'doctor' && profileRes.data.profile) {
            currentDoctorId.value = profileRes.data.profile.id;
        }
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
                            {{ patient ? (decryptedPatientName || `${patient.user.first_name} ${patient.user.last_name}`) + "'s Medical Records" : 'My Medical Records' }}
                        </h1>
                        <p v-if="patient" class="text-gray-600 mt-1">
                            Date of Birth: {{ decryptedPatientDOB ? new Date(decryptedPatientDOB).toLocaleDateString() : (patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'N/A') }}
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
                        <td class="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{{ getDecryptedName(file) }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">{{ new Date(getDecryptedDate(file)).toLocaleDateString() }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-gray-500">{{ file.description || 'N/A' }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                            <button @click="handleDownload(file)" class="text-blue-600 hover:text-blue-900 font-medium inline-flex items-center gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                Download
                            </button>
                            <button @click="openEditModal(file)" class="text-green-600 hover:text-green-900 font-medium inline-flex items-center gap-1">
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
                        <h3 class="text-lg font-semibold text-gray-900">
                            {{ userType === 'doctor' ? 'Request to Edit Medical Record' : 'Edit Medical Record' }}
                        </h3>
                        <p v-if="userType === 'doctor'" class="text-sm text-blue-600 mt-1">⚠️ Patient approval required for changes</p>
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
                            {{ editLoading ? 'Processing...' : (userType === 'doctor' ? 'Send Request' : 'Save Changes') }}
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