<script setup>
import { ref, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import api from '../services/api';
import ConfirmModal from '../components/ConfirmModal.vue';
import StatusAlert from '../components/StatusAlert.vue';
import { decryptWithSharedKey, decryptSharedKey } from '../utils/crypto';

const patients = ref([]);
const loading = ref(true);
const error = ref('');
const success = ref('');
const showRemoveModal = ref(false);
const patientToRemove = ref(null);
const decryptedPatients = ref({}); // Store decrypted patient data as reactive object
const currentDoctorId = ref(null); // Store doctor ID for key decryption

onMounted(async () => {
    await fetchData();
});

const fetchData = async () => {
    try {
        loading.value = true;
        
        // Get doctor profile
        const profileRes = await api.get('/auth/me/');
        currentDoctorId.value = profileRes.data.profile.id;
        
        // Get doctor's patients
        const patientsRes = await api.getPatients();
        patients.value = patientsRes.data;
        
        // Decrypt patient data using shared keys
        await decryptPatientsData();
        
        loading.value = false;
    } catch (e) {
        console.error("Failed to fetch data:", e);
        error.value = "Failed to load data.";
        loading.value = false;
    }
};

// Decrypt patient personal information using shared keys
const decryptPatientsData = async () => {
    console.log('[DEBUG] Starting to decrypt patients data...');
    console.log('[DEBUG] Current doctor ID:', currentDoctorId.value);
    console.log('[DEBUG] Number of patients:', patients.value.length);
    
    for (const patient of patients.value) {
        try {
            console.log(`[DEBUG] Processing patient: ${patient.user.username} (ID: ${patient.id})`);
            
            // Get shared key for this patient (encrypted with doctor's derived key)
            const keyResponse = await api.get(`/get-shared-key/?patient_id=${patient.id}`);
            const encryptedPatientKey = keyResponse.data.encrypted_key;
            console.log(`[DEBUG] Got encrypted key (first 50 chars): ${encryptedPatientKey.substring(0, 50)}`);
            
            // Step 1: Decrypt the patient's key using doctor's ID
            const patientKey = decryptSharedKey(encryptedPatientKey, currentDoctorId.value);
            console.log(`[DEBUG] Decrypted patient key:`, patientKey ? 'SUCCESS' : 'FAILED');
            
            if (!patientKey) {
                throw new Error('Failed to decrypt patient key');
            }
            
            // Step 2: Decrypt patient data with patient's key
            console.log(`[DEBUG] encrypted_first_name exists: ${!!patient.encrypted_first_name}`);
            console.log(`[DEBUG] encrypted_last_name exists: ${!!patient.encrypted_last_name}`);
            
            const firstName = patient.encrypted_first_name ? decryptWithSharedKey(patient.encrypted_first_name, patientKey) : patient.user.first_name;
            const lastName = patient.encrypted_last_name ? decryptWithSharedKey(patient.encrypted_last_name, patientKey) : patient.user.last_name;
            const dateOfBirth = patient.encrypted_date_of_birth ? decryptWithSharedKey(patient.encrypted_date_of_birth, patientKey) : patient.date_of_birth;
            
            console.log(`[DEBUG] Decrypted firstName: ${firstName}`);
            console.log(`[DEBUG] Decrypted lastName: ${lastName}`);
            console.log(`[DEBUG] Decrypted dateOfBirth: ${dateOfBirth}`);
            console.log(`[DEBUG] Original date_of_birth: ${patient.date_of_birth}`);
            
            const decryptedData = { firstName, lastName, dateOfBirth };
            
            // Use object assignment for Vue reactivity
            decryptedPatients.value[patient.id] = decryptedData;
        } catch (e) {
            console.error(`[ERROR] Failed to decrypt patient ${patient.id} data:`, e);
            // Fallback to encrypted placeholders
            decryptedPatients.value[patient.id] = {
                firstName: patient.user.first_name,
                lastName: patient.user.last_name,
                dateOfBirth: patient.date_of_birth
            };
        }
    }
    console.log('[DEBUG] Finished decrypting patients data');
    console.log('[DEBUG] Decrypted patients object:', decryptedPatients.value);
};

// Get decrypted patient name
const getPatientName = (patient) => {
    const data = decryptedPatients.value[patient.id];
    console.log(`[DEBUG] getPatientName for ${patient.id}:`, data);
    if (data) {
        return `${data.firstName} ${data.lastName}`;
    }
    // Fallback to username if decryption failed
    return `@${patient.user.username}`;
};

// Get decrypted patient date of birth
const getPatientDOB = (patient) => {
    const data = decryptedPatients.value[patient.id];
    if (data && data.dateOfBirth) {
        return new Date(data.dateOfBirth).toLocaleDateString();
    }
    return 'N/A';  // No fallback to plaintext
};

const cancelRequest = async (requestId) => {
    try {
        await api.rejectRequest(requestId);
        success.value = "Request cancelled.";
        error.value = '';
        await fetchData();
    } catch (e) {
        console.error("Failed to cancel request:", e);
        error.value = "Failed to cancel request.";
    }
};

const openRemoveModal = (patient) => {
    patientToRemove.value = patient;
    showRemoveModal.value = true;
};

const confirmRemovePatient = async () => {
    showRemoveModal.value = false;
    const patient = patientToRemove.value;
    
    try {
        await api.createRequest({ 
            patient_id: patient.id,
            action_type: 'remove'
        });
        success.value = `Removal request sent for ${getPatientName(patient)}.`;
        error.value = '';
        await fetchData();
    } catch (e) {
        console.error("Failed to send removal request:", e);
        error.value = e.response?.data?.error || "Failed to send removal request.";
    } finally {
        patientToRemove.value = null;
    }
};

const cancelRemovePatient = () => {
    showRemoveModal.value = false;
    patientToRemove.value = null;
};
</script>

<template>
    <div class="max-w-6xl mx-auto py-8">
        <StatusAlert v-if="error" type="error" :message="error" @close="error = ''" />
        <StatusAlert v-if="success" type="success" :message="success" @close="success = ''" />

        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-extrabold text-gray-900">My Patients</h1>
                <p class="text-sm text-gray-500">Manage your patients and send access requests.</p>
            </div>
            <button @click="$router.push('/add-patient')"
                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
                + Add Patient
            </button>
        </div>

        <!-- Current Patients List -->
        <div v-if="loading" class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="text-gray-500 mt-2">Loading patients...</p>
        </div>

        <div v-else-if="patients.length === 0" class="text-center py-12 bg-white rounded-lg shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p class="text-gray-600 font-medium">No patients yet</p>
            <p class="text-gray-400 text-sm mt-1">Add patients to start managing their medical records</p>
        </div>

        <div v-else class="grid gap-4">
            <div v-for="patient in patients" :key="patient.id" 
                class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="font-bold text-lg text-gray-900">
                            {{ getPatientName(patient) }}
                        </h3>
                        <p class="text-sm text-gray-500">@{{ patient.user.username }}</p>
                        <p class="text-sm text-gray-500 mt-1">
                            Date of Birth: {{ getPatientDOB(patient) }}
                        </p>
                    </div>
                    <div class="flex gap-2">
                        <RouterLink :to="`/records?patient_id=${patient.id}`"
                            class="bg-blue-100 text-blue-700 hover:bg-blue-200 px-3 py-1.5 rounded text-sm font-medium transition flex items-center gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            View Records
                        </RouterLink>
                        <button @click="openRemoveModal(patient)"
                            class="bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1.5 rounded text-sm font-medium transition flex items-center gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Remove Patient Modal -->
        <ConfirmModal
            :show="showRemoveModal"
            :title="'Remove Patient'"
            :message="patientToRemove ? `Request to remove ${getPatientName(patientToRemove)} from your patients list? The patient must approve this action.` : ''"
            :confirmText="'Send Request'"
            :cancelText="'Cancel'"
            :isDangerous="true"
            @confirm="confirmRemovePatient"
            @cancel="cancelRemovePatient"
        />
    </div>
</template>
