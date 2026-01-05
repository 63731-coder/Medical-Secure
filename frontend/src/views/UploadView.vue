<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';
import { useRouter, useRoute } from 'vue-router';
import { encryptData, encryptKeyForDoctor, decryptSharedKey, encryptWithSharedKey, encryptMetadata, getCurrentKey, decryptWithSharedKey } from '../utils/crypto';
import StatusAlert from '../components/StatusAlert.vue';
import { useNotifications } from '../composables/useNotifications';

const router = useRouter();
const route = useRoute();
const { success: notifySuccess, error: notifyError } = useNotifications();

const file = ref(null);
const title = ref("");
const fileExtension = ref("");
const loading = ref(false);
const status = ref({ type: 'info', message: '' });
const userType = ref(null);
const patients = ref([]);
const selectedPatient = ref(null);
const appointedDoctors = ref([]);
const currentDoctorId = ref(null);
const decryptedPatients = ref({}); // Store decrypted patient names

onMounted(async () => {
    try {
        const profileRes = await api.getProfile();
        userType.value = profileRes.data.user_type;
        
        // If doctor, fetch patients list and store doctor ID
        if (userType.value === 'doctor') {
            currentDoctorId.value = profileRes.data.profile.id;
            const patientsRes = await api.getPatients();
            patients.value = patientsRes.data;
            
            // Check if patient_id is in URL (coming from patient's records page)
            if (route.query.patient_id) {
                selectedPatient.value = route.query.patient_id;
            }
            
            // Decrypt patient names
            await decryptPatientsData();
        }
        
        // If patient, get appointed doctors list for key sharing
        if (userType.value === 'patient') {
            appointedDoctors.value = profileRes.data.profile.appointed_doctors || [];
        }
    } catch (e) {
        console.error('Failed to fetch profile:', e);
    }
});

// Decrypt patient names for dropdown
const decryptPatientsData = async () => {
    for (const patient of patients.value) {
        try {
            const keyResponse = await api.get(`/get-shared-key/?patient_id=${patient.id}`);
            const encryptedPatientKey = keyResponse.data.key;
            const patientKey = decryptSharedKey(encryptedPatientKey, currentDoctorId.value);
            
            if (patientKey && patient.first_name && patient.last_name) {
                const firstName = decryptWithSharedKey(patient.first_name, patientKey);
                const lastName = decryptWithSharedKey(patient.last_name, patientKey);
                decryptedPatients.value[patient.id] = { firstName, lastName };
            } else {
                // Fallback to username if decryption fails
                decryptedPatients.value[patient.id] = {
                    firstName: patient.user.username,
                    lastName: ''
                };
            }
        } catch (e) {
            console.warn(`Failed to decrypt patient ${patient.id}:`, e);
            decryptedPatients.value[patient.id] = {
                firstName: patient.user.username,
                lastName: ''
            };
        }
    }
};

const goBackToRecords = () => {
    // If doctor and patient is selected, go to patient's records
    if (userType.value === 'doctor' && selectedPatient.value) {
        router.push(`/records?patient_id=${selectedPatient.value}`);
    } else {
        // Otherwise go to own records
        router.push('/records');
    }
};

// Get decrypted patient name
const getPatientName = (patient) => {
    const data = decryptedPatients.value[patient.id];
    if (data) {
        return `${data.firstName} ${data.lastName}`.trim();
    }
    return `@${patient.user.username}`;
};

const handleFileChange = (event) => {
    file.value = event.target.files[0];
    
    if (file.value) {
        const fileName = file.value.name;
        const lastDotIndex = fileName.lastIndexOf('.');
        
        if (lastDotIndex !== -1) {
            fileExtension.value = fileName.substring(lastDotIndex); // e.g., ".png"
            const nameWithoutExt = fileName.substring(0, lastDotIndex);
            
            // If title is empty, use filename without extension
            if (!title.value) {
                title.value = nameWithoutExt;
            }
        } else {
            fileExtension.value = "";
            if (!title.value) {
                title.value = fileName;
            }
        }
    }
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

            let encryptedContent;
            
            // 2. Encrypt Content (Client-Side)
            // The server NEVER sees the rawContent
            if (userType.value === 'doctor') {
                // Doctor encrypting for patient - need to use patient's key
                try {
                    // Get patient's shared encryption key
                    const keyResponse = await api.get('/get-shared-key/', {
                        params: { patient_id: selectedPatient.value }
                    });
                    
                    const encryptedSharedKey = keyResponse.data.key;
                    
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
                    throw new Error("Cannot encrypt file for patient. Ensure you have been appointed as their doctor.");
                }
            } else {
                // Patient encrypting their own file - use their own key
                encryptedContent = encryptData(base64Content);
                
                if (!encryptedContent) {
                    throw new Error("Encryption failed. Are you logged in?");
                }
            }

            // 3. Prepare Form Data (Django expects a file)
            // We create a new Blob from the encrypted string
            const encryptedBlob = new Blob([encryptedContent], { type: 'application/octet-stream' });
            const formData = new FormData();
            // Combine title and extension for the document name
            const fullTitle = title.value + fileExtension.value;
            formData.append('file', encryptedBlob, file.value.name + ".enc"); // Add .enc extension
            
            // Encrypt sensitive metadata (file name and date) BEFORE sending to server
            const currentDate = new Date().toISOString();
            let encryptedName, encryptedDate;
            
            if (userType.value === 'doctor') {
                // Doctor: use patient's shared key
                try {
                    const keyResponse = await api.get('/get-shared-key/', {
                        params: { patient_id: selectedPatient.value }
                    });
                    const patientKey = decryptSharedKey(keyResponse.data.key, currentDoctorId.value);
                    encryptedName = encryptWithSharedKey(fullTitle, patientKey);
                    encryptedDate = encryptWithSharedKey(currentDate, patientKey);
                } catch (keyError) {
                    console.error("Failed to encrypt metadata with patient key:", keyError);
                    throw new Error("Cannot encrypt file metadata for patient");
                }
                
                formData.append('patient_id', selectedPatient.value);
                formData.append('file_name', encryptedName);
                formData.append('file_description', '');
                formData.append('file_date', encryptedDate);
            } else {
                // Patient: use their own key (simpler)
                encryptedName = encryptMetadata(fullTitle);
                encryptedDate = encryptMetadata(currentDate);
            }
            
            formData.append('name', encryptedName);
            formData.append('description', ''); // Empty encrypted description
            formData.append('date', encryptedDate);

            // 4. Send to Server
            status.value = { type: 'info', message: "Uploading encrypted data..." };

            await api.post('/files/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            // Patient upload - immediate success
            if (userType.value === 'patient') {
                status.value = { type: 'success', message: "File encrypted and uploaded successfully!" };
                notifySuccess('File uploaded successfully');
                
                // Share encryption key with all appointed doctors
                const patientKey = sessionStorage.getItem('encryptionKey');
                if (patientKey && appointedDoctors.value.length > 0) {
                    for (const doctor of appointedDoctors.value) {
                        try {
                            // Encrypt and share key with each appointed doctor
                            const encryptedKey = encryptKeyForDoctor(patientKey, doctor.id);
                            
                            await api.post('/share-key/', {
                                doctor_id: doctor.id,
                                key: encryptedKey
                            });
                        } catch (keyError) {
                            console.error(`Failed to share key with doctor ${doctor.id}:`, keyError);
                        }
                    }
                }
            }
            
            title.value = "";
            fileExtension.value = "";
            file.value = null;
            selectedPatient.value = null;

        } catch (error) {
            // Check if it's a pending request (for doctors)
            if (error.response?.data?.pending) {
                status.value = { type: 'success', message: error.response.data.message };
                notifySuccess('Upload request sent to patient for approval');
            } else {
                console.error('Upload error:', error);
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
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold text-gray-900">Secure Document Upload</h2>
            <button @click="goBackToRecords" 
                class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                View All Records
            </button>
        </div>

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
                        {{ getPatientName(patient) }} (@{{ patient.user.username }})
                    </option>
                </select>
                <p class="text-xs text-blue-600 mt-2">⚠️ Patient approval required for upload</p>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Document Title</label>
                <div class="flex items-center gap-2">
                    <input v-model="title" type="text" required
                        class="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="e.g., Blood Test Results">
                    <span v-if="fileExtension" 
                        class="px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-700 font-mono text-sm">
                        {{ fileExtension }}
                    </span>
                </div>
                <p v-if="fileExtension" class="text-xs text-gray-500 mt-1">Extension automatically added from file</p>
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