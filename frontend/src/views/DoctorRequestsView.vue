<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';
import StatusAlert from '../components/StatusAlert.vue';
import { useNotifications } from '../composables/useNotifications';
import { getCurrentKey, encryptKeyForDoctor } from '../utils/crypto';

const { success: notifySuccess, error: notifyError } = useNotifications();
const requests = ref([]);
const loading = ref(true);
const error = ref('');
const success = ref('');
const decryptedDoctors = ref({}); // Store decrypted doctor names

onMounted(async () => {
    await fetchRequests();
    await decryptDoctorsData();
});

const fetchRequests = async () => {
    try {
        loading.value = true;
        
        // Get profile to confirm user is a patient
        const profileRes = await api.getProfile();
        if (profileRes.data.user_type !== 'patient') {
            error.value = "This page is for patients only.";
            loading.value = false;
            return;
        }
        
        // Get all requests for this patient
        const requestsRes = await api.getRequests();
        requests.value = requestsRes.data.filter(r => r.status === 'pending');
        
        loading.value = false;
    } catch (e) {
        console.error("Failed to fetch requests:", e);
        error.value = "Failed to load requests.";
        loading.value = false;
    }
};

// Check if a string looks like encrypted data (Base64 CryptoJS format)
const isEncryptedString = (str) => {
    if (!str) return false;
    // CryptoJS encrypted strings start with "U2FsdGVkX1" (Base64 for "Salted__")
    return str.startsWith('U2FsdGVkX1');
};

// Get doctor names - doctors' names should NOT be encrypted (public professional info)
// But handle legacy encrypted names gracefully by falling back to username
const decryptDoctorsData = async () => {
    for (const request of requests.value) {
        try {
            const doctor = request.doctor;
            if (!doctor) continue;
            
            // Doctor names should be in plain text in Django User model
            // If they look encrypted (legacy data), fall back to username
            let firstName = doctor.user.first_name || '';
            let lastName = doctor.user.last_name || '';
            
            // Check if names are encrypted (legacy issue) - use username instead
            if (isEncryptedString(firstName) || isEncryptedString(lastName)) {
                firstName = doctor.user.username;
                lastName = '';
            }
            
            decryptedDoctors.value[doctor.id] = { firstName, lastName };
        } catch (e) {
            // Fallback to username if something fails
            const doctor = request.doctor;
            decryptedDoctors.value[doctor.id] = {
                firstName: doctor.user.username,
                lastName: ''
            };
        }
    }
};

// Get decrypted doctor name
const getDoctorName = (doctor) => {
    if (!doctor) return 'Unknown';
    const data = decryptedDoctors.value[doctor.id];
    if (data && data.firstName) {
        return `${data.firstName} ${data.lastName}`.trim();
    }
    return doctor.user.username;
};

const approveRequest = async (request) => {
    try {
        // First approve the request
        await api.approveRequest(request.id);
        
        // Then automatically share the encryption key with the doctor
        try {
            const myEncryptionKey = getCurrentKey();
            
            if (myEncryptionKey) {
                // Encrypt patient's key for the doctor using doctor ID
                const encryptedKey = encryptKeyForDoctor(myEncryptionKey, request.doctor.id);
                
                await api.post('/share-key/', {
                    doctor_id: request.doctor.id,
                    key: encryptedKey
                });
            }
        } catch (keyError) {
            console.error('Failed to share encryption key:', keyError);
            // Don't fail the whole approval if key sharing fails
        }
        
        const doctorName = getDoctorName(request.doctor);
        const message = `Dr. ${doctorName} has been added to your doctors list.`;
        success.value = message;
        notifySuccess(message);
        error.value = '';
        await fetchRequests();
        await decryptDoctorsData();
    } catch (e) {
        console.error("Failed to approve request:", e);
        const errorMsg = e.response?.data?.error || "Failed to approve request.";
        error.value = errorMsg;
        notifyError(errorMsg);
    }
};

const rejectRequest = async (request) => {
    try {
        await api.rejectRequest(request.id);
        const doctorName = getDoctorName(request.doctor);
        success.value = `Request from Dr. ${doctorName} has been rejected.`;
        error.value = '';
        await fetchRequests();
        await decryptDoctorsData();
    } catch (e) {
        console.error("Failed to reject request:", e);
        error.value = e.response?.data?.error || "Failed to reject request.";
    }
};

// Decrypt request action type
const getDecryptedActionType = (request) => {
    // action_type is NOT encrypted on backend - it's stored as plain 'add' or 'remove'
    // This is not sensitive data, just an action type
    if (!request.action_type) return 'add';
    return request.action_type;
};

</script>

<template>
    <div class="max-w-4xl mx-auto py-8">
        <StatusAlert v-if="error" type="error" :message="error" @close="error = ''" />
        <StatusAlert v-if="success" type="success" :message="success" @close="success = ''" />

        <div class="mb-6">
            <h1 class="text-2xl font-extrabold text-gray-900">Doctor Access Requests</h1>
            <p class="text-sm text-gray-500">Review and approve doctors who want to access your medical records.</p>
        </div>

        <div v-if="loading" class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="text-gray-500 mt-2">Loading requests...</p>
        </div>

        <div v-else-if="requests.length === 0" class="text-center py-12 bg-white rounded-lg shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-gray-600 font-medium">No pending requests</p>
            <p class="text-gray-400 text-sm mt-1">You don't have any doctor access requests at the moment</p>
        </div>

        <div v-else class="space-y-4">
            <div v-for="request in requests" :key="request.id" 
                :class="[
                    'rounded-lg shadow-md border p-6',
                    getDecryptedActionType(request) === 'remove' ? 'bg-red-50 border-red-200' : 'bg-white border-gray-200'
                ]">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <h3 class="font-bold text-lg text-gray-900">
                                Dr. {{ getDoctorName(request.doctor) }}
                            </h3>
                            <span v-if="getDecryptedActionType(request) === 'remove'" 
                                class="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded">
                                REMOVAL REQUEST
                            </span>
                        </div>
                        <p class="text-sm text-gray-600">{{ request.doctor.organisation }}</p>
                        <p class="text-xs text-gray-500 mt-2">
                            Request sent {{ new Date(request.created_at).toLocaleDateString() }}
                        </p>
                    </div>
                    <span class="bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-1 rounded">
                        Pending
                    </span>
                </div>

                <div :class="[
                    'border rounded-lg p-4 mb-4',
                    getDecryptedActionType(request) === 'remove' ? 'bg-red-100 border-red-300' : 'bg-blue-50 border-blue-200'
                ]">
                    <p :class="[
                        'text-sm',
                        getDecryptedActionType(request) === 'remove' ? 'text-red-900' : 'text-blue-900'
                    ]">
                        <strong>Dr. {{ getDoctorName(request.doctor) }}</strong> 
                        <span v-if="getDecryptedActionType(request) === 'add'">
                            is requesting access to your medical records.
                            If you approve, they will be able to view and upload medical files to your account.
                        </span>
                        <span v-else>
                            is requesting to be removed from your doctors list.
                            If you approve, they will no longer have access to your medical records.
                        </span>
                    </p>
                </div>

                <div class="flex gap-3">
                    <button @click="approveRequest(request)"
                        class="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition">
                        Approve
                    </button>
                    <button @click="rejectRequest(request)"
                        class="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition">
                        Reject
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
